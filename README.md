# LLMin Workspace

仓库现分层架构：

```text
.
├── apps/
│   ├── backend/    # FastAPI、RAG、评测脚本
│   └── frontend/   # Web UI 与代理服务
├── docs/
│   └── licenses/   # 模型许可证
├── models/
│   └── baichuan/   # Baichuan 自定义模型配置代码
├── scripts/        # 顶层启动入口
└── LICENSE
```

## 常用启动

```bash
# 激活项目环境（GPU PyTorch + vLLM + 后端/RAG/前端代理）
source .venv/bin/activate

# vLLM + 后端 + 前端
# MODEL_PATH 必须指向真实 Baichuan 权重目录，而不是仅包含代码的 models/baichuan
MODEL_PATH=/path/to/Baichuan bash scripts/start_services.sh

# 前端 + 后端
bash scripts/start_app.sh

# 仅后端
bash scripts/start_backend.sh

# 仅 vLLM
MODEL_PATH=/path/to/Baichuan bash scripts/start_vllm.sh

# 仅 MCP Server（stdio，供 MCP Client 拉起）
bash scripts/start_mcp.sh
```

## vLLM / GPU 配置

- `.venv` 当前使用 CUDA 版 PyTorch，并已安装 vLLM；同一个环境用于 FastAPI、RAG、Embedding、前端代理和 vLLM。
- `requirements.txt` 固定 GPU PyTorch 基础运行时；`requirements-vllm.txt` 安装 vLLM 及其 CUDA 依赖。
- 当前仓库的 `models/baichuan` 只有 Baichuan 自定义代码和配置，不包含模型权重；启动 vLLM 前必须设置 `MODEL_PATH` 到包含 `config.json` 和 `*.safetensors` / `pytorch_model*.bin` 的权重目录。
- `scripts/start_vllm.sh` 默认自动选择显存占用最低的 GPU；也可手动设置 `GPU_ID=0`、`GPU_ID=1` 等。
- vLLM 以 OpenAI 兼容接口提供服务，默认 `served model` 为 `baichuan`，后端默认请求 `http://127.0.0.1:8000/v1/chat/completions`。

安装/更新当前环境：

```bash
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-vllm.txt

MODEL_PATH=/path/to/Baichuan GPU_ID=auto bash scripts/start_vllm.sh
```

常用环境变量：

```bash
MODEL_PATH=/path/to/Baichuan          # 必填：真实权重目录
VLLM_PYTHON_BIN=/path/to/python       # 可选：默认使用 .venv/bin/python
GPU_ID=auto                           # 默认：自动选择显存占用最低的 GPU
VLLM_MODEL=baichuan                   # 后端请求的模型名，同时传给 vLLM served model
VLLM_API_URL=http://127.0.0.1:8000/v1/chat/completions
```

## 依赖文件

- `requirements.txt`: 主前后端运行环境与 GPU PyTorch
- `requirements-vllm.txt`: vLLM 服务依赖
- `requirements-eval.txt`: RAG 评测脚本依赖
- `requirements-optional.txt`: 量化等可选工具依赖

更细的 RAG 测试说明见 `apps/backend/docs/rag_test_tutorial.md`。
MCP 接入说明见 `apps/backend/docs/mcp_integration.md`。
