# 前端说明

当前主线前端位于 `apps/frontend`，负责静态页面与 `/api/v1/*` 代理。

## 目录

```text
apps/frontend/
├── index.html
├── css/
├── js/
├── icon/
├── run_ui_opt.sh
└── ui_proxy_server.py
```

## 启动

推荐从仓库根目录运行：

```bash
bash scripts/start_app.sh
```

也可以直接在当前目录运行：

```bash
PYTHON_BIN=python ./run_ui_opt.sh
```

默认地址是 `http://127.0.0.1:8095`。该脚本会先启动 `apps/backend/main_api.py`，再启动当前目录下的前端代理服务。

## 说明

- 页面资源在 `index.html`、`css/`、`js/`、`icon/`。
- 代理服务入口是 `ui_proxy_server.py`。
- 后端接口基址通过环境变量 `BACKEND_BASE` 控制。
