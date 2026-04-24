# 保险审核项目 RAG 实现说明

本文档说明项目中 RAG（Retrieval-Augmented Generation，检索增强生成）在 [main_api.py](main_api.py) 的实现方式。

## 1. 总体架构

当前实现是一个典型的两阶段流程：

1. 文档入库阶段（离线/准实时）
2. 问答阶段（在线）

对应接口：

1. `POST /api/v1/documents/analyze`：上传合同并建立向量索引
2. `POST /api/v1/chat/completions`：根据问题做检索并生成回答

## 2. 文档入库阶段

### 2.1 文档解析

- PDF 文档通过 `parse_pdf_text` 使用 `PyMuPDF` 抽取文本。
- TXT 文档按 UTF-8 解码。

### 2.2 预处理与分块

- 通过 `split_by_length(text, max_len=800)` 做段落级分块。
- 分块目标：
  - 避免一次性输入过长上下文。
  - 保持条款语义完整，减少句子截断。

### 2.3 向量化

- 使用 `SentenceTransformer`（CPU）做 embedding。
- `normalize_embeddings=True`，将向量归一化。
- 归一化后内积 $\text{IP}$ 近似余弦相似度：
  $$\cos(\theta) \approx \mathbf{q}\cdot\mathbf{d}$$

### 2.4 向量索引

- 使用 `faiss.IndexFlatIP` 建立索引。
- 将所有 chunk 向量写入索引，保存在内存数据库：
  - `chunks`
  - `faiss_index`
  - `summary`
  - `suggested_keywords`

## 3. 问答阶段

### 3.1 查询增强（Query Hint）

- 对用户问题执行 `build_query_hint`。
- 根据问题模式自动追加关键检索词（如“如实告知”“第10章”等），提升关键条款命中概率。

### 3.2 语义检索

- 将增强后的 query 向量化。
- 在 FAISS 中检索 top-k（最多 8 个）候选。
- 使用阈值 `SIM_THRESHOLD = 0.45` 过滤低相关结果。

### 3.3 规则优先召回

- `rule_priority_indices` 会优先匹配高价值条款编号/标题（如 `11.6`、`5.2`、`第10章`）。
- 最终上下文顺序：
  1. 规则命中
  2. FAISS 命中

### 3.4 上下文拼接与裁剪

- 上下文总长度限制 `MAX_CONTEXT_LENGTH = 4000`。
- 拼接时附带来源标签：`[规则优先]` 或 `[相似度:x.xx]`。
- 同时构建 `citations`，供前端展示依据片段。

### 3.5 生成与后处理

- 通过 `build_insurance_prompt` 构建严格提示词：
  - 只能依据上下文
  - 禁止引用上下文外法规
  - 固定输出结构（结论/合同依据/说明/处理建议）
- 模型输出再经过：
  - `sanitize_model_output`：去噪、去重复、标准化
  - `extract_three_part_response`：结构化提取关键段落

## 4. 数据流与状态

项目当前使用内存数据库（进程内字典）：

- `DATABASE["documents"]`：保存文档、chunk、向量索引
- `DATABASE["conversations"]`：保存多轮问答历史

优点：实现简单、调试快。
限制：服务重启后数据丢失，不适合多实例共享。

## 5. 现状优势与风险

### 优势

1. 语义检索 + 规则优先融合，命中关键条款更稳定。
2. 提示词约束较强，回答更可引用。
3. 输出增加 `citations` 与 `recommendations`，前端可解释性更好。

### 风险

1. 索引仅在内存中，缺乏持久化。
2. 分块策略是长度启发式，复杂版式合同可能切分不理想。
3. 指标体系尚未内置，需要外部评测脚本。

## 6. 建议的下一步

1. 增加离线索引持久化（FAISS index + 元数据落盘）。
2. 增加 reranker（cross-encoder）提升 top-k 质量。
3. 在 CI 中加入 RAG 回归评测，避免提示词或阈值调整带来退化。
