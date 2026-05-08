# MCP 接入说明

本项目已新增一个 stdio 模式的 MCP Server，用来把保险合同 RAG 能力暴露给支持 MCP 的客户端。

## 启动

先安装运行依赖：

```bash
pip install -r requirements.txt
```

启动 MCP Server：

```bash
bash scripts/start_mcp.sh
```

默认入口文件：

```text
apps/backend/mcp_server.py
```

MCP Server 会懒加载 `main_api.py`：进程启动不立刻加载 embedding 模型；首次调用需要 RAG 后端的 tool/resource/prompt 时才加载。若默认 embedding 目录缺少权重文件，`health_check` 会返回结构化错误。

## Tools

- `health_check`：检查 MCP Server、RAG 开关、Chroma 路径和 vLLM 地址。
- `list_documents`：列出当前进程内已加载合同。
- `analyze_local_contract`：读取本地 PDF/TXT 合同，完成摘要、分块、向量化和 Chroma 入库。
- `search_contract_clauses`：只做合同条款检索，不调用大模型生成答案。
- `ask_insurance_contract`：基于合同 RAG 回答问题，返回答案、引用和建议。
- `generate_session_archive`：根据会话历史生成归档报告数据包。

## Resources

- `insurance://documents`
- `insurance://documents/{document_id}/summary`
- `insurance://documents/{document_id}/chunks`
- `insurance://documents/{document_id}/chunks/{chunk_index}`

## Prompts

- `insurance_contract_qa`：复用项目里的保险合同问答提示词模板。

## 客户端配置示例

以 stdio MCP Client 为例，命令指向项目脚本：

```json
{
  "mcpServers": {
    "baichuan-insurance-rag": {
      "command": "bash",
      "args": [
        "/home/wsc/wsc/codes/Baichuan/scripts/start_mcp.sh"
      ]
    }
  }
}
```

## 环境变量

- `VLLM_API_URL`：vLLM OpenAI 兼容接口地址，默认 `http://localhost:8000/v1/chat/completions`。
- `VLLM_MODEL_PATH`：vLLM 模型名或模型路径，默认指向 `models/baichuan`。
- `USE_RAG`：是否启用 RAG，默认启用。
- `CHROMA_DB_PATH`：Chroma 持久化目录。
- `EMBEDDING_MODEL_DIR`：本地 embedding 模型目录。
- `MCP_CONTRACT_ROOT`：允许 MCP 读取合同文件的根目录，默认项目根目录。
- `MCP_MAX_FILE_MB`：MCP 读取本地合同的文件大小限制，默认 `25`。

## 安全边界

`analyze_local_contract` 不接受任意路径。默认只能读取项目根目录下的 PDF/TXT 文件；如需读取其他合同目录，显式设置 `MCP_CONTRACT_ROOT`。

MCP Server 在工具调用时会复用 `main_api.py` 的全局模型、Chroma 客户端和内存会话状态。因此 MCP Server 与 FastAPI Server 是两个独立进程时，内存里的 `DATABASE` 不共享；Chroma 中已持久化的文档分块可以按 `document_id` 自动恢复。
