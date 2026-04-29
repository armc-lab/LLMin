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
# 前端 + 后端
bash scripts/start_app.sh

# 仅后端
bash scripts/start_backend.sh

# 仅 vLLM
bash scripts/start_vllm.sh
```

更细的 RAG 测试说明见 `apps/backend/docs/rag_test_tutorial.md`。
