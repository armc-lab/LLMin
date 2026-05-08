"""MCP server for the insurance contract RAG backend.

The server exposes the existing FastAPI/RAG capabilities as MCP tools,
resources, and prompts. It is intentionally stdio-first so desktop agents can
spawn it directly.
"""

import json
import os
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List

from fastapi import HTTPException
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("baichuan-insurance-rag")
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parents[1]
_BACKEND: ModuleType | None = None
_BACKEND_IMPORT_ERROR: Exception | None = None


def _backend() -> ModuleType:
    global _BACKEND, _BACKEND_IMPORT_ERROR
    if _BACKEND is not None:
        return _BACKEND

    try:
        import main_api
    except Exception as exc:
        _BACKEND_IMPORT_ERROR = exc
        raise RuntimeError(f"后端运行时加载失败: {exc}") from exc

    _BACKEND = main_api
    _BACKEND_IMPORT_ERROR = None
    return _BACKEND


def _http_error_to_value_error(exc: HTTPException) -> ValueError:
    return ValueError(str(exc.detail))


def _resolve_allowed_file(file_path: str) -> Path:
    raw_path = Path(file_path).expanduser()
    path = raw_path if raw_path.is_absolute() else PROJECT_ROOT / raw_path
    path = path.resolve()

    allowed_root = Path(os.getenv("MCP_CONTRACT_ROOT", str(PROJECT_ROOT))).expanduser().resolve()
    if path != allowed_root and allowed_root not in path.parents:
        raise ValueError(f"文件路径不在允许目录内: {allowed_root}")

    if not path.exists() or not path.is_file():
        raise ValueError(f"文件不存在: {path}")

    if path.suffix.lower() not in {".pdf", ".txt"}:
        raise ValueError("MCP 合同入库目前仅支持 PDF 和 TXT 文件。")

    max_mb = int(os.getenv("MCP_MAX_FILE_MB", "25"))
    if path.stat().st_size > max_mb * 1024 * 1024:
        raise ValueError(f"文件超过 MCP_MAX_FILE_MB 限制: {max_mb}MB")

    return path


def _document_metadata(document_id: str, doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "document_id": document_id,
        "filename": doc.get("filename", ""),
        "summary": doc.get("summary", ""),
        "chunk_count": len(doc.get("chunks", [])),
        "suggested_keywords": doc.get("suggested_keywords", []),
    }


def _list_documents_payload() -> List[Dict[str, Any]]:
    api = _backend()
    return [
        _document_metadata(document_id, doc)
        for document_id, doc in api.DATABASE["documents"].items()
    ]


@mcp.tool()
def health_check() -> Dict[str, Any]:
    """检查 MCP Server 与本地 RAG 运行时是否已加载。"""
    try:
        api = _backend()
    except RuntimeError as exc:
        return {
            "name": "baichuan-insurance-rag",
            "backend_loaded": False,
            "error": str(exc),
            "project_root": str(PROJECT_ROOT),
            "embedding_model_dir": os.getenv("EMBEDDING_MODEL_DIR", str(BACKEND_DIR / "bge-large-zh-v1.5-local")),
        }

    return {
        "name": "baichuan-insurance-rag",
        "backend_loaded": True,
        "backend": "main_api",
        "rag_enabled": api.USE_RAG,
        "documents_in_memory": len(api.DATABASE["documents"]),
        "chroma_path": api.CHROMA_DB_PATH,
        "vllm_api_url": api.VLLM_API_URL,
    }


@mcp.tool()
def list_documents() -> List[Dict[str, Any]]:
    """列出当前进程内已加载的保险合同文档。"""
    return _list_documents_payload()


@mcp.tool()
async def analyze_local_contract(file_path: str) -> Dict[str, Any]:
    """读取本地 PDF/TXT 合同，完成摘要、分块、向量化和 Chroma 入库。"""
    api = _backend()
    path = _resolve_allowed_file(file_path)
    contents = path.read_bytes()
    if path.suffix.lower() == ".pdf":
        full_text = api.parse_pdf_text(contents)
    else:
        full_text = contents.decode("utf-8")

    try:
        return await api.analyze_contract_text(path.name, full_text)
    except HTTPException as exc:
        raise _http_error_to_value_error(exc) from exc


@mcp.tool()
def search_contract_clauses(document_id: str, question: str, top_k: int = 6) -> Dict[str, Any]:
    """仅检索合同条款，不调用大模型生成答案。"""
    api = _backend()
    safe_top_k = max(1, min(int(top_k), 12))
    try:
        result = api.retrieve_contract_context(
            document_id=document_id,
            question=question,
            max_context_length=3000,
            max_results=safe_top_k,
        )
    except HTTPException as exc:
        raise _http_error_to_value_error(exc) from exc

    return {
        "document_id": document_id,
        "question": question,
        "status": result["status"],
        "query_hint": result["query_hint"],
        "citations": result["citations"],
        "context": result["context"],
    }


@mcp.tool()
async def ask_insurance_contract(document_id: str, question: str, save_history: bool = True) -> Dict[str, Any]:
    """基于合同 RAG 回答保险合同问题，并返回引用依据。"""
    api = _backend()
    try:
        data = await api.answer_contract_question(
            document_id=document_id,
            question=question,
            save_history=save_history,
        )
    except HTTPException as exc:
        raise _http_error_to_value_error(exc) from exc

    return {
        "document_id": document_id,
        "question": question,
        **data,
    }


@mcp.tool()
async def generate_session_archive(document_id: str) -> Dict[str, Any]:
    """根据某份合同的会话历史生成 Markdown 归档报告数据包。"""
    api = _backend()
    try:
        return await api.build_archive_payload(document_id, archive_type="session_summary")
    except HTTPException as exc:
        raise _http_error_to_value_error(exc) from exc


@mcp.resource("insurance://documents")
def documents_resource() -> str:
    """当前已加载合同列表。"""
    return json.dumps(_list_documents_payload(), ensure_ascii=False, indent=2)


@mcp.resource("insurance://documents/{document_id}/summary")
def document_summary_resource(document_id: str) -> str:
    """指定合同摘要。"""
    api = _backend()
    try:
        doc = api.get_document_or_restore(document_id)
    except HTTPException as exc:
        raise _http_error_to_value_error(exc) from exc
    return doc.get("summary", "")


@mcp.resource("insurance://documents/{document_id}/chunks")
def document_chunks_resource(document_id: str) -> str:
    """指定合同的所有文本分块。"""
    api = _backend()
    try:
        doc = api.get_document_or_restore(document_id)
    except HTTPException as exc:
        raise _http_error_to_value_error(exc) from exc

    chunks = [
        {"index": idx, "text": chunk}
        for idx, chunk in enumerate(doc.get("chunks", []))
    ]
    return json.dumps(chunks, ensure_ascii=False, indent=2)


@mcp.resource("insurance://documents/{document_id}/chunks/{chunk_index}")
def document_chunk_resource(document_id: str, chunk_index: str) -> str:
    """指定合同的单个文本分块。"""
    api = _backend()
    try:
        doc = api.get_document_or_restore(document_id)
    except HTTPException as exc:
        raise _http_error_to_value_error(exc) from exc

    chunks = doc.get("chunks", [])
    idx = int(chunk_index)
    if idx < 0 or idx >= len(chunks):
        raise ValueError(f"chunk_index 超出范围: {idx}")
    return chunks[idx]


@mcp.prompt()
def insurance_contract_qa(question: str, context: str = "") -> str:
    """生成保险合同问答的标准提示词。"""
    api = _backend()
    return api.build_insurance_prompt(context=context, question=question)


if __name__ == "__main__":
    mcp.run()
