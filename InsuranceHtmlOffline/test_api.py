#!/usr/bin/env python3
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],  # 只允许前端域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "测试API服务器运行中"}

@app.post("/api/v1/documents/analyze")
async def test_upload(file: UploadFile = File(...)):
    return {
        "success": True,
        "data": {
            "document_id": "test-doc-123",
            "filename": file.filename,
            "summary": "这是一个测试摘要"
        }
    }

if __name__ == "__main__":
    print("启动测试API服务器在端口8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
