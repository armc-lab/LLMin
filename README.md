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
# 激活环境
conda activate /home/wsc/wsc/codes/Baichuan/.venv

# 前端 + 后端
bash scripts/start_app.sh

# 仅后端
bash scripts/start_backend.sh

# 仅 vLLM
bash scripts/start_vllm.sh
```

## 依赖文件

- `requirements.txt`: 主前后端运行环境
- `requirements-vllm.txt`: 本机启动 vLLM 服务时再安装
- `requirements-eval.txt`: RAG 评测脚本依赖
- `requirements-optional.txt`: 量化等可选工具依赖

更细的 RAG 测试说明见 `apps/backend/docs/rag_test_tutorial.md`。
