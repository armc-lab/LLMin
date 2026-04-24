# main_api.py (Version 3.1 - Semantic Search RAG - 强化版)
import uuid
import datetime
import httpx
import fitz  # PyMuPDF
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Any

# RAG 相关
from sentence_transformers import SentenceTransformer
import faiss

# =========================
# 1) 配置
# =========================
APP_PORT = 8001
VLLM_API_URL = "http://localhost:8000/v1/chat/completions"
VLLM_MODEL_PATH = "/data2/wangliangmin/snap/Baichuan"

# Embedding：放 CPU，避免与 vLLM 抢显存
print("正在加载 Embedding 模型（device=cpu）...")
EMBEDDING_MODEL_DIR = "./bge-large-zh-v1.5-local"
embedding_model = SentenceTransformer(EMBEDDING_MODEL_DIR, device="cpu")
print("Embedding 模型加载完成。")

# 简易“内存数据库”
DATABASE: Dict[str, Dict[str, Any]] = {
    "documents": {},      # doc_id -> {filename, summary, chunks, faiss_index}
    "conversations": {}   # doc_id -> [ {role, content}, ... ]
}

# =========================
# 2) 数据模型（Schemas）
# =========================
class DocumentData(BaseModel):
    document_id: str
    filename: str
    summary: str

class DocumentResponse(BaseModel):
    success: bool = True
    data: DocumentData

class ChatRequest(BaseModel):
    document_id: str = Field(..., description="关联的文档ID")
    question: str

class ChatResponseData(BaseModel):
    answer: str

class ChatResponse(BaseModel):
    success: bool = True
    data: ChatResponseData

class ArchiveRequest(BaseModel):
    document_id: str
    archive_type: Literal["session_summary"] = "session_summary"

class ArchivePayload(BaseModel):
    archive_id: str
    archive_type: str
    timestamp: str
    source_document_id: str
    generated_report_markdown: str
    model_version: str

class ArchiveResponse(BaseModel):
    success: bool = True
    message: str
    archive_payload: ArchivePayload

# =========================
# 3) 工具函数
# =========================
def parse_pdf_text(file_content: bytes) -> str:
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")
        return "".join(page.get_text() for page in doc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF 解析失败: {e}")

async def call_vllm(prompt: str, temperature: float = 0.0) -> str:
    """调用 vLLM /v1/chat/completions（OpenAI 兼容）"""
    payload = {
        "model": VLLM_MODEL_PATH,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(VLLM_API_URL, json=payload)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"请求 vLLM 服务失败: {e}")
    except (KeyError, IndexError) as e:
        raise HTTPException(status_code=500, detail=f"解析 vLLM 响应失败: {e}")

def split_by_length(text: str, max_len: int = 800) -> List[str]:
    """将长文本按近似长度分块，更稳的分段效果。"""
    buf, out = [], []
    for para in text.splitlines():
        if not para.strip():
            continue
        if sum(len(x) for x in buf) + len(para) <= max_len:
            buf.append(para)
        else:
            out.append("\n".join(buf))
            buf = [para]
    if buf:
        out.append("\n".join(buf))
    return out

def dedup_summary_lines(summary: str, max_lines: int = 8) -> str:
    """摘要去重，提升可读性。"""
    seen, out = set(), []
    for ln in summary.splitlines():
        s = ln.strip()
        if s and s not in seen:
            out.append(s)
            seen.add(s)
        if len(out) >= max_lines:
            break
    return "\n".join(out)

def build_query_hint(q: str) -> str:
    """根据问题类型拼接检索提示词，提升命中“关键条款”概率。"""
    q = q.strip()
    if "告知" in q or "拒保" in q:
        return "如实告知 第11.6 明确说明与如实告知 健康告知 告知义务 免责 解除合同"
    if "120" in q or "重疾" in q or "重大疾病" in q:
        return "第10章 重大疾病释义 疾病定义 使用规范 诊断条件 病理 影像"
    if "轻症" in q and ("重疾" in q or "重大" in q):
        return "1.2.3.2 轻度疾病保险金给付后 合同继续有效 基本保险金额不变 1.2.5 重大疾病保险金"
    if "报案" in q or "通知" in q:
        return "5.2 保险事故通知 报案 10日内 通知义务 影响责任认定"
    return ""

def rule_priority_indices(chunks: List[str], q: str) -> List[int]:
    """规则优先：命中关键条款编号/标题的分块索引，优先加入上下文。"""
    keys: List[str] = []
    if "告知" in q or "拒保" in q:
        keys += ["11.6", "明确说明", "如实告知"]
    if "报案" in q or "通知" in q:
        keys += ["5.2", "保险事故通知"]
    if "轻症" in q and ("重疾" in q or "重大" in q):
        keys += ["1.2.3.2", "1.2.5"]
    if "120" in q or "重大疾病" in q or "重疾" in q:
        keys += ["第10章", "重大疾病释义"]
    if not keys:
        return []
    hits: List[int] = []
    for i, ck in enumerate(chunks):
        if not ck:
            continue
        head = ck.splitlines()[0][:60]
        tail = ck[:200]
        if any(k in head or k in tail for k in keys):
            hits.append(i)
    # 去重保序
    return list(dict.fromkeys(hits))

def build_insurance_prompt(context: str, question: str) -> str:
    """
    更严格的提示词：
    - 只能依据上下文；
    - 禁止引用上下文外的法律/条款/页码；
    - 未命中时不说“无法判断”，而是承认未命中并给出通俗解释 + 建议；
    - 强制固定五段式输出。
    """
    return f"""
你是资深保险理赔审核员。**只能**依据【上下文】回答【问题】；**严禁引用上下文中未出现的法律/法规/条款/页码**（如《保险法》《合同法》或“第X条/第X章/第X页”等占位式引用）。若上下文没有出现对应表述，必须坦诚说明“未检索到该条款原文”，随后给出通俗解释与可执行建议，**不得写“无法判断”四个字**。

【输出格式（必须逐段输出，中文，标题须原样保留）】
问题：{question}

结论：<一句话结论；若与健康告知相关，明确“必须如实告知”；若上下文未命中证据，写“本次检索未命中合同原文，以下为通俗解释与建议”>

合同依据：
- 【<条款定位或写“未定位条款号”>】"<逐字引用的原文句子1>"
- 【<条款定位或写“未定位条款号”>】"<逐字引用的原文句子2>"
- （若上下文未命中任何可引用文本，写“（未检索到可引用的合同原文）”）

说明：
- <用2–4行把条款与问题的对应逻辑说清楚；若未命中文本，则写清“未命中的原因/可能在合同其他部分”>

处理建议：
- <给2–4条可执行建议：如“如实填写健康问卷”“对照第10章释义逐条比对病历”“事故10日内完成通知”“准备病理/影像/出院小结”等>

【上下文】（仅可依据此处内容作答；若为空，必须进入“未命中”处理）：
---
{(context if context.strip() else "（未检索到相关条款原文）")}
---
"""

# =========================
# 4) FastAPI 应用
# =========================
app = FastAPI(
    title="保险智能审核 API v3.1 (语义检索RAG-强化)",
    description="RAG（语义检索）+ 规则优先检索 + 严格可引用提示词。",
    version="3.1",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "保险智能审核 API v3.1 已启动", "docs_url": "/docs"}

# =========================
# 5) Endpoints
# =========================
@app.post("/api/v1/documents/analyze", response_model=DocumentResponse, tags=["1. 文档处理与索引"])
async def analyze_document(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="目前仅支持 PDF 和 TXT 文件。")
    # input("here")

    contents = await file.read()
    full_text = parse_pdf_text(contents) if file.filename.lower().endswith(".pdf") else contents.decode("utf-8")

    # 摘要（截断以控 token）
    summary_prompt = (
        "你是专业的保险合同分析引擎。请在不超过50字内给出摘要，必须包含：合同性质、核心保障、关键免责条款。"
        f"\n\n合同文本（可能截断）：\n{full_text[:3000]}"
    )
    summary = await call_vllm(summary_prompt, temperature=0.2)
    summary = dedup_summary_lines(summary, max_lines=8)

    # 分块 + 向量化（归一化后用 IP 即余弦）
    chunks = split_by_length(full_text, max_len=800)
    if not chunks:
        raise HTTPException(status_code=400, detail="文档内容为空或无法分块。")

    print(f"正在为 {len(chunks)} 个文本块创建向量...")
    print("here")
    chunk_embeddings = embedding_model.encode(chunks, normalize_embeddings=True)
    chunk_embeddings = np.asarray(chunk_embeddings, dtype="float32")
    print(type(chunk_embeddings))
    print("向量创建完成成。")
    
    faiss_index = faiss.IndexFlatIP(chunk_embeddings.shape[1])  # 余弦相似度（归一化后IP≈cosine）
    
    faiss_index.add(chunk_embeddings)   #这一句有问题
   
    print("FAISS（cosine）检索引擎构建完成。")

    doc_id = f"doc-{uuid.uuid4()}"
    DATABASE["documents"][doc_id] = {
        "filename": file.filename,
        "summary": summary,
        "chunks": chunks,
        "faiss_index": faiss_index,
    }
    DATABASE["conversations"][doc_id] = []

    return {"success": True, "data": {"document_id": doc_id, "filename": file.filename, "summary": summary}}

@app.post("/api/v1/chat/completions", response_model=ChatResponse, tags=["2. 核心问答 (语义检索)"])
async def handle_chat_completion(request: ChatRequest):
    doc_id = request.document_id
    if doc_id not in DATABASE["documents"]:
        raise HTTPException(status_code=404, detail=f"文档ID '{doc_id}' 不存在。")

    doc_data = DATABASE["documents"][doc_id]
    faiss_index = doc_data.get("faiss_index")
    all_chunks: List[str] = doc_data.get("chunks", [])
    if not faiss_index or not all_chunks:
        raise HTTPException(status_code=500, detail="检索引擎或分块数据不存在，请重新上传文档。")

    print("正在为问题进行语义检索...")
    # 加入查询提示词（query hint）以提升命中关键条款概率
    query_hint = build_query_hint(request.question)
    effective_query = (request.question + " " + query_hint).strip()

    q_emb = embedding_model.encode([effective_query], normalize_embeddings=True)
    q_emb = np.asarray(q_emb, dtype="float32")

    # 更高的门槛 + 更多候选
    k = min(8, len(all_chunks))
    sims, idxs = faiss_index.search(q_emb, k)
    SIM_THRESHOLD = 0.45

    # 规则优先条款
    prio = rule_priority_indices(all_chunks, request.question)
    # 合并排序：规则优先在前，其次是 faiss 结果
    ordered = prio + [i for i in idxs[0].tolist() if i not in prio]

    # 拼接上下文（带相似度标签），限制长度
    MAX_CONTEXT_LENGTH = 4000
    ctx_parts, cur_len = [], 0
    used = set()
    for i in ordered:
        if i < 0 or i >= len(all_chunks) or i in used:
            continue
        # 对于规则优先的块，没有相似度；FAISS 检索块读取相似度
        if i in prio:
            seg = f"[规则优先]\n{all_chunks[i]}"
        else:
            # 找到该 i 在 faiss 返回中的相似度
            try:
                # 如果 i 不在 idxs[0] 中，默认给 0.40（边界）
                pos = idxs[0].tolist().index(i)
                s = sims[0][pos]
            except ValueError:
                s = 0.40
            if s < SIM_THRESHOLD:
                continue
            seg = f"[相似度:{s:.2f}]\n{all_chunks[i]}"

        seg_len = len(seg) + 8
        if cur_len + seg_len <= MAX_CONTEXT_LENGTH:
            ctx_parts.append(seg)
            cur_len += seg_len
            used.add(i)
        else:
            break

    context = "\n\n---\n\n".join(ctx_parts)

    # 结构化、严格可引用提示词
    rag_prompt = build_insurance_prompt(context, request.question)
    final_answer = await call_vllm(rag_prompt, temperature=0.0)

    # 记入会话
    DATABASE["conversations"][doc_id].append({"role": "user", "content": request.question})
    DATABASE["conversations"][doc_id].append({"role": "assistant", "content": final_answer})

    return {"success": True, "data": {"answer": final_answer}}

@app.post("/api/v1/archive/generate-and-submit", response_model=ArchiveResponse, tags=["3. 报告生成与归档"])
async def generate_and_submit_archive(request: ArchiveRequest):
    doc_id = request.document_id
    if doc_id not in DATABASE["conversations"]:
        raise HTTPException(status_code=404, detail=f"文档ID '{doc_id}' 的会话历史不存在。")

    chat_history = DATABASE["conversations"][doc_id]
    if not chat_history:
        raise HTTPException(status_code=400, detail="该文档没有会话历史，无法生成报告。")

    chat_history_str = "\n".join([f"{item['role']}: {item['content']}" for item in chat_history])
    report_prompt = (
        "你是归档机器人。根据【对话历史】生成 Markdown 会话总结报告，必须包含两个段落："
        "【核心问题】、【最终结论】；语言简洁明确。\n\n"
        f"【对话历史】:\n{chat_history_str}\n\n请输出报告："
    )
    markdown_report = await call_vllm(report_prompt, temperature=0.2)

    archive_payload = {
        "archive_id": f"archive-{uuid.uuid4()}",
        "archive_type": request.archive_type,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_document_id": doc_id,
        "generated_report_markdown": markdown_report,
        "model_version": "Baichuan-7B-v1.0-RAG-v3.1",
    }

    return {
        "success": True,
        "message": "报告已生成。以下是准备归档到区块链的数据包。",
        "archive_payload": archive_payload,
    }

# =========================
# 6) 启动
# =========================
if __name__ == "__main__":
    import uvicorn
    print(f"启动保险智能审核 API v3.1 (语义检索RAG-强化)，监听端口 {APP_PORT}...")
    print(f"API 文档地址: http://localhost:{APP_PORT}/docs")
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)
