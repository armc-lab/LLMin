#!/usr/bin/env python3
"""Single-file frontend server for insurance_api.

Usage:
  python frontend_onefile_server.py

Then open:
  http://127.0.0.1:8088

This file serves a product-style frontend page and proxies /api/v1/* requests
to the existing backend (default http://127.0.0.1:8001).
"""

from __future__ import annotations

import http.client
import os
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HOST = os.getenv("FRONTEND_HOST", "127.0.0.1")
PORT = int(os.getenv("FRONTEND_PORT", "8088"))
BACKEND_BASE = os.getenv("BACKEND_BASE", "http://127.0.0.1:8001")

HTML_PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="保险合同解释助手" />
  <title>保险合同解释助手</title>
  <style>
    :root {
      --green: #4c742c;
      --green-dark: #395b1f;
      --gray-light: #f5f5f5;
      --gray-medium: #d9d9d9;
      --white: #ffffff;
      --text-primary: #333;
      --text-secondary: #666;
      --text-muted: #999;
      --text-placeholder: #bbb;
      --border-radius: 6px;
      --border-radius-lg: 24px;
      --shadow-sm: 0 2px 4px rgba(0,0,0,0.06);
      --shadow-md: 0 4px 8px rgba(0,0,0,0.1);
      --transition-fast: 0.2s;
    }

    * { box-sizing: border-box; }
    html, body { height: 100%; margin: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
      font-size: 14px;
      line-height: 1.5;
      color: var(--text-primary);
      background: var(--gray-light);
    }

    .container {
      display: flex;
      height: 100vh;
      overflow: hidden;
      background: var(--gray-light);
    }

    aside {
      width: 260px;
      background: var(--gray-light);
      border-right: 1px solid var(--gray-medium);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
      transition: width var(--transition-fast);
    }

    aside.collapsed { width: 60px; }

    .logo-box {
      padding: 10px 16px 6px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid rgba(217, 217, 217, 0.3);
      position: relative;
    }

    .logo-box img {
      width: 30px;
      height: 30px;
      object-fit: cover;
      transform: scale(1.15);
    }

    .panel-title {
      color: var(--text-secondary);
      font-weight: 600;
      letter-spacing: 0.5px;
    }

    .collapse-btn {
      cursor: pointer;
      font-size: 18px;
      color: #777;
      user-select: none;
      padding: 4px;
      border-radius: 4px;
    }

    .menu-btn {
      width: 90%;
      margin: 6px auto;
      padding: 12px 16px;
      border: none;
      border-radius: var(--border-radius);
      background: var(--green);
      color: var(--white);
      font-size: 15px;
      font-weight: 500;
      cursor: pointer;
      transition: all var(--transition-fast);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }

    .menu-btn:hover { background: var(--green-dark); transform: translateY(-1px); }

    .btn-icon { width: 18px; height: 18px; filter: brightness(0) invert(1); }

    .history-content, .evidence-section {
      margin: 14px 10px 0;
      padding: 12px 14px;
      border-top: 1px solid rgba(217, 217, 217, 0.5);
      min-height: 120px;
      color: var(--text-muted);
      overflow-y: auto;
      flex: 1;
    }

    .evidence-section { min-height: 120px; flex: 0 0 auto; }

    .evidence-title { margin-bottom: 8px; font-weight: 600; color: var(--text-secondary); }

    .placeholder { color: var(--text-placeholder); font-size: 13px; }

    .profile {
      margin-top: auto;
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 16px;
      border-top: 1px solid rgba(217, 217, 217, 0.5);
      color: var(--text-secondary);
    }

    main {
      flex: 1;
      background: var(--white);
      display: flex;
      flex-direction: column;
      position: relative;
      overflow: hidden;
    }

    .welcome {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 30px 20px;
    }

    .welcome-header {
      display: flex;
      align-items: center;
      gap: 15px;
      margin-bottom: 15px;
    }

    .welcome img { width: 64px; height: 64px; }

    .welcome h1 {
      margin: 0;
      font-size: 32px;
      font-weight: 600;
      color: var(--text-primary);
      letter-spacing: 0.5px;
      line-height: 1.3;
    }

    .welcome p {
      margin: 6px 0;
      font-size: 18px;
      color: var(--text-secondary);
      line-height: 1.6;
      letter-spacing: 0.3px;
    }

    .upload-page {
      display: none;
      flex: 1;
      align-items: center;
      justify-content: center;
      background: var(--white);
      min-height: 100%;
    }

    .upload-content {
      max-width: 900px;
      width: 100%;
      padding: 60px 40px;
      text-align: center;
    }

    .upload-header { margin-bottom: 40px; }
    .upload-icon-circle {
      width: 100px; height: 100px; border-radius: 50%;
      background: rgba(34, 197, 94, 0.15);
      display: flex; align-items: center; justify-content: center;
      margin: 0 auto 20px;
    }
    .upload-header-icon { width: 48px; height: 48px; }
    .upload-content h2 { margin: 0 0 16px; font-size: 40px; font-weight: 600; }
    .upload-description { margin: 0 auto 30px; max-width: 620px; color: var(--text-secondary); font-size: 22px; line-height: 1.8; }

    .upload-area {
      border: 2px dashed var(--gray-medium);
      border-radius: 12px;
      padding: 60px 80px;
      margin-bottom: 40px;
      background: var(--white);
      min-height: 420px;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all var(--transition-fast);
    }

    .upload-area:hover { border-color: var(--green); background: rgba(76, 116, 44, 0.02); }
    .upload-placeholder {
      width: 100%; height: 100%;
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      text-align: center;
    }
    .upload-placeholder-icon { width: 72px; height: 72px; margin-bottom: 32px; opacity: 0.6; }
    .upload-main-text { margin: 16px 0 12px; font-size: 24px; font-weight: 500; }
    .file-hint { font-size: 20px; color: var(--text-muted); margin: 0 0 24px 0; }

    .file-preview { text-align: center; padding: 20px; width: 100%; }
    .file-preview-header { font-size: 18px; color: var(--text-secondary); margin-bottom: 20px; font-weight: 500; }
    .file-item {
      display: flex; align-items: center; background: #fef5f5; border-radius: 8px;
      padding: 20px; margin: 0 auto 30px; max-width: 600px; position: relative;
    }
    .file-icon { margin-right: 16px; }
    .file-type-icon { width: 48px; height: 48px; }
    .file-info { flex: 1; text-align: left; }
    .file-name { font-size: 18px; font-weight: 600; margin-bottom: 6px; }
    .file-details { display: flex; gap: 12px; font-size: 15px; color: var(--text-muted); }
    .file-remove { position: absolute; top: 35px; right: 20px; background: rgba(255,255,255,0.9); border: 1px solid #ddd; border-radius: 50%; width: 24px; height: 24px; }
    .file-reselect-actions { display: flex; justify-content: center; margin-top: 20px; }
    .btn-reselect {
      background: #f5f5f5; color: #666; border: 1px solid #ddd; padding: 16px 40px; border-radius: var(--border-radius);
      font-size: 18px; font-weight: 600; cursor: pointer;
    }
    .upload-actions, .upload-bottom-actions { display: flex; justify-content: center; margin-top: 18px; }
    .btn-upload, #confirmUpload {
      background: var(--green); color: white; border: none; border-radius: var(--border-radius);
      padding: 14px 34px; font-size: 18px; font-weight: 600; cursor: pointer;
    }
    .btn-upload:hover, #confirmUpload:hover { background: var(--green-dark); }

    .chat-page {
      display: none;
      height: 100vh;
      flex-direction: column;
      background: var(--white);
      overflow-y: auto;
    }

    .chat-container { display: flex; flex-direction: column; min-height: 100%; }
    .chat-header {
      display: flex; align-items: center; justify-content: center;
      padding: 16px 20px; background: var(--white); position: sticky; top: 0; z-index: 10;
      border-bottom: 1px solid #f0f0f0;
    }
    .chat-title { font-size: 22px; font-weight: 700; margin: 0; text-align: center; }
    .chat-messages {
      flex: 1; padding: 20px 20px 180px; max-width: 1050px; margin: 0 auto; width: 100%;
    }
    .welcome-message, .bot-message {
      display: flex; align-items: flex-start; gap: 16px; max-width: 1034px; width: 100%; margin: 0 auto 12px;
    }
    .bot-avatar { width: 36px; height: 36px; border-radius: 50%; background: white; border: 1px solid var(--gray-light); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
    .bot-avatar img { width: 22px; height: 22px; }
    .message-content {
      background: var(--white); border-radius: 12px; padding: 16px 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid var(--gray-light);
      max-width: 900px;
    }
    .message-content p { margin: 0; font-size: 16px; line-height: 1.7; }
    .user-message { display: flex; justify-content: flex-end; margin-bottom: 20px; width: 100%; }
    .user-message .message-content { background: rgba(76, 116, 80, 0.08); max-width: 70%; }

    .chat-input-bar {
      position: fixed; bottom: 16px; left: calc(50% + 140px); transform: translateX(-50%) scale(1.22);
      transform-origin: center bottom; width: 600px; min-height: 80px; background: white;
      border: 2px solid #e5e7eb; border-radius: var(--border-radius-lg); z-index: 100; display: flex; align-items: center; justify-content: center;
    }
    .chat-input-bar textarea {
      width: calc(100% - 11px); height: 100%; border: none; border-radius: var(--border-radius-lg);
      padding: 18px 6px 45px 18px; margin-right: 11px; font-size: 12px; resize: none; outline: none; font-family: inherit; background: transparent;
    }
    .add-ui-btn, .send-btn {
      position: absolute; width: 28px; height: 28px; border: none; border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; z-index: 102;
    }
    .add-ui-btn { left: 10px; bottom: 6px; background: white; }
    .send-btn { right: 10px; bottom: 6px; background: var(--green); color: white; width: auto; min-width: 50px; padding: 0 10px; gap: 6px; border-radius: 10px; }

    .badge {
      display: inline-flex; align-items: center; gap: 6px; border-radius: 999px; padding: 4px 10px; font-size: 12px; font-weight: 600;
    }
    .badge-hit { color: #166534; background: #dcfce7; border: 1px solid #86efac; }
    .badge-miss { color: #92400e; background: #fef3c7; border: 1px solid #fcd34d; }

    .list { margin: 10px 0 0; padding: 0; list-style: none; display: grid; gap: 8px; }
    .item { border: 1px solid var(--gray-medium); border-radius: 8px; background: #fff; padding: 10px; font-size: 13px; line-height: 1.6; }
    .item small { display: block; margin-top: 4px; color: var(--text-muted); }
    .hint { margin-top: 10px; color: var(--text-muted); font-size: 13px; }
    .error { margin-top: 10px; color: #b91c1c; font-size: 13px; background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 8px 10px; display: none; }
    .status-pill { margin-left: auto; color: var(--text-secondary); font-size: 13px; }

    .backend-bar {
      margin: 12px 20px 0;
      padding: 10px 14px;
      border: 1px solid var(--gray-medium);
      border-radius: 10px;
      background: #fafafa;
      color: var(--text-secondary);
      font-size: 13px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .backend-bar strong { color: var(--text-primary); }

    @media (max-width: 768px) {
      aside { display: none; }
      .chat-input-bar { left: 50%; transform: translateX(-50%) scale(1); width: calc(100% - 32px); }
      .welcome h1 { font-size: 24px; }
      .welcome p { white-space: normal; font-size: 16px; }
      .upload-content h2 { font-size: 28px; }
      .upload-description { font-size: 16px; }
      .upload-area { min-height: 280px; padding: 24px; }
    }
  </style>
</head>
<body>
  <div class="container">
    <aside id="sidebar">
      <div class="logo-box">
        <img alt="logo" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%234c742c'/%3E%3Cpath d='M22 26c0-5.5 4.5-10 10-10s10 4.5 10 10v6c0 5.5-4.5 10-10 10s-10-4.5-10-10v-6z' fill='white'/%3E%3Ccircle cx='28' cy='29' r='2' fill='%234c742c'/%3E%3Ccircle cx='36' cy='29' r='2' fill='%234c742c'/%3E%3Cpath d='M26 35c2 3 10 3 12 0' stroke='%234c742c' stroke-width='2' fill='none' stroke-linecap='round'/%3E%3C/svg%3E" />
        <span class="panel-title">操作面板</span>
        <span class="collapse-btn" id="collapseToggle">«</span>
      </div>

      <button class="menu-btn" id="uploadNavBtn"><span>上传合同文档</span></button>
      <button class="menu-btn" id="askNavBtn"><span>提问</span></button>
      <button class="menu-btn" id="evidenceNavBtn"><span>存证</span></button>

      <div class="history-content" id="historyContent">
        <div class="placeholder">暂无历史对话</div>
      </div>

      <div class="evidence-section" id="evidenceSectionPanel">
        <div class="evidence-title">证据与建议</div>
        <div class="badge badge-miss" id="hitBadge">未命中原文</div>
        <div class="hint">引用片段</div>
        <ul id="evidenceSectionList" class="list"><li class="item">暂无引用片段</li></ul>
        <div class="hint">下一步建议</div>
        <ul id="recommendSectionList" class="list"><li class="item">暂无建议</li></ul>
      </div>

      <div class="profile"><span>个人信息</span></div>
    </aside>

    <main>
      <div class="backend-bar">
        <strong>后端</strong>
        <span id="backendBarText">已连接后端代理，接口请求将转发到 API 服务</span>
      </div>
      <div class="welcome" id="welcomeArea">
        <div class="welcome-header">
          <img alt="bot" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%234c742c'/%3E%3Crect x='18' y='22' width='28' height='20' rx='10' fill='white'/%3E%3Ccircle cx='26' cy='31' r='2' fill='%234c742c'/%3E%3Ccircle cx='38' cy='31' r='2' fill='%234c742c'/%3E%3Cpath d='M24 38h16' stroke='%234c742c' stroke-width='2' stroke-linecap='round'/%3E%3C/svg%3E" />
          <h1>我是保险合同解释助手，很高兴见到你！</h1>
        </div>
        <p>我可以回答合同相关的基础问题、解析合同文件，请把你的任务交给我吧~</p>
      </div>

      <div class="upload-page" id="uploadPage">
        <div class="upload-content">
          <div class="upload-header">
            <div class="upload-icon-circle">
              <img class="upload-header-icon" alt="upload" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 64 64'%3E%3Cpath d='M32 8v30' stroke='%2322c55e' stroke-width='4' stroke-linecap='round'/%3E%3Cpath d='M20 20l12-12 12 12' fill='none' stroke='%2322c55e' stroke-width='4' stroke-linecap='round' stroke-linejoin='round'/%3E%3Crect x='12' y='34' width='40' height='18' rx='6' fill='none' stroke='%2322c55e' stroke-width='4'/%3E%3C/svg%3E" />
            </div>
            <h2>上传合同文档</h2>
            <p class="upload-description">将你的保险合同文档上传到这里，我们的 AI 助手将帮助你分析和理解合同内容</p>
          </div>

          <div class="upload-area" id="uploadArea">
            <div class="upload-placeholder" id="uploadPlaceholder">
              <img class="upload-placeholder-icon" alt="upload" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='72' height='72' viewBox='0 0 72 72'%3E%3Cpath d='M36 10v32' stroke='%23999' stroke-width='4' stroke-linecap='round'/%3E%3Cpath d='M22 24l14-14 14 14' fill='none' stroke='%23999' stroke-width='4' stroke-linecap='round' stroke-linejoin='round'/%3E%3Crect x='14' y='38' width='44' height='18' rx='6' fill='none' stroke='%23999' stroke-width='4'/%3E%3C/svg%3E" />
              <p class="upload-main-text">点击上传文档或拖拽到此处</p>
              <p class="file-hint">支持 PDF、TXT 等格式</p>
            </div>

            <div class="file-preview" id="filePreview" style="display:none;">
              <div class="file-preview-header">已选择的文件</div>
              <div class="file-item">
                <div class="file-icon">
                  <img class="file-type-icon" alt="file" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='64' height='64' viewBox='0 0 64 64'%3E%3Crect x='12' y='8' width='40' height='48' rx='6' fill='%23fef5f5' stroke='%23d9d9d9'/%3E%3Cpath d='M24 20h16M24 28h16M24 36h10' stroke='%234c742c' stroke-width='3' stroke-linecap='round'/%3E%3C/svg%3E" />
                </div>
                <div class="file-info">
                  <div class="file-name" id="fileName">文件名.pdf</div>
                  <div class="file-details"><span id="fileType">PDF文档</span><span id="fileSize">1.2 MB</span></div>
                </div>
                <button class="file-remove" id="fileRemove">×</button>
              </div>
              <div class="file-reselect-actions"><button class="btn-reselect" id="reselectFileBtn">重新选择</button></div>
            </div>

            <input type="file" id="fileInput" accept=".pdf,.txt" style="display:none;" />
          </div>

          <div class="upload-actions"><button class="btn-upload" id="selectFileBtn">选择文件</button></div>
          <div class="upload-bottom-actions"><button id="confirmUpload">确认上传</button></div>
          <div id="uploadMeta" style="margin-top:18px;color:var(--text-secondary);"></div>
          <div id="uploadError" class="error"></div>
        </div>
      </div>

      <div class="chat-page" id="chatPage">
        <div class="chat-container">
          <div class="chat-header">
            <div style="display:flex;flex-direction:column;gap:6px;align-items:center;">
              <h3 class="chat-title" id="chatTitle">保险合同解释助手</h3>
              <div class="status-pill" id="globalStatus">状态：等待上传合同</div>
            </div>
          </div>

          <div class="chat-messages" id="chatMessages">
            <div class="welcome-message" id="chatWelcome">
              <div class="bot-avatar">
                <img alt="bot" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='36' height='36' viewBox='0 0 36 36'%3E%3Ccircle cx='18' cy='18' r='18' fill='%234c742c'/%3E%3Crect x='9' y='10' width='18' height='12' rx='6' fill='white'/%3E%3Ccircle cx='15' cy='16' r='1.5' fill='%234c742c'/%3E%3Ccircle cx='21' cy='16' r='1.5' fill='%234c742c'/%3E%3Cpath d='M13 21h10' stroke='%234c742c' stroke-width='1.5' stroke-linecap='round'/%3E%3C/svg%3E" />
              </div>
              <div class="message-content"><p>你好！我是你的保险合同解释助手，我可以帮助你分析和理解保险合同的各项条款。请告诉我你想了解的问题吧！</p></div>
            </div>
          </div>
        </div>
      </div>

      <div class="chat-input-bar" id="chatInputBar">
        <textarea id="questionInput" placeholder="请输入问题，例如：轻症赔付后重疾保额是否变化？"></textarea>
        <button class="add-ui-btn" id="askBtn" title="发送">
          <span>+</span>
        </button>
        <button class="send-btn" id="archiveBtn"><span>存证</span></button>
      </div>
    </main>
  </div>

  <script>
    const state = { documentId: "", uploadedFileName: "", chatHistory: [] };
    const $ = (id) => document.getElementById(id);

    function showPage(page) {
      $("welcomeArea").style.display = page === "welcome" ? "flex" : "none";
      $("uploadPage").style.display = page === "upload" ? "flex" : "none";
      $("chatPage").style.display = page === "chat" ? "flex" : "none";
      $("chatInputBar").style.display = page === "chat" ? "flex" : "none";
    }

    function setGlobalStatus(text) { $("globalStatus").textContent = `状态：${text}`; }

    function setError(id, msg) {
      const el = $(id);
      if (!msg) { el.style.display = "none"; el.textContent = ""; return; }
      el.style.display = "block";
      el.textContent = msg;
    }

    function setHistory(text) {
      const h = $("historyContent");
      h.innerHTML = `<div style="color:#555;line-height:1.8;font-size:13px;white-space:pre-wrap;">${text}</div>`;
    }

    function addMessage(role, text) {
      const wrap = document.createElement("div");
      wrap.className = role === "user" ? "user-message" : "bot-message";
      const avatar = role === "user" ? "" : `<div class=\"bot-avatar\"><img alt=\"bot\" src=\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='36' height='36' viewBox='0 0 36 36'%3E%3Ccircle cx='18' cy='18' r='18' fill='%234c742c'/%3E%3Crect x='9' y='10' width='18' height='12' rx='6' fill='white'/%3E%3Ccircle cx='15' cy='16' r='1.5' fill='%234c742c'/%3E%3Ccircle cx='21' cy='16' r='1.5' fill='%234c742c'/%3E%3Cpath d='M13 21h10' stroke='%234c742c' stroke-width='1.5' stroke-linecap='round'/%3E%3C/svg%3E\" /></div>`;
      wrap.innerHTML = role === "user"
        ? `<div class=\"message-content\"><p>${text}</p></div>`
        : `${avatar}<div class=\"message-content\"><p>${text.replace(/\n/g, "<br/>")}</p></div>`;
      $("chatMessages").appendChild(wrap);
      $("chatMessages").scrollTop = $("chatMessages").scrollHeight;
      state.chatHistory.push(`${role}: ${text}`);
      setHistory(state.chatHistory.slice(-8).join("\n\n"));
    }

    function renderKeywords(keywords = []) {
      const wrap = $("historyContent");
      if (!keywords.length) {
        wrap.innerHTML = '<div class="placeholder">暂无历史对话</div>';
        return;
      }
      wrap.innerHTML = keywords.map((kw) => `<div style="padding:6px 0;border-bottom:1px solid rgba(0,0,0,0.04);font-size:13px;color:#555;">${kw}</div>`).join("");
    }

    function renderCitations(citations = []) {
      const target = $("evidenceSectionList");
      if (!target) return;
      target.innerHTML = citations.length
        ? citations.map((c) => `<li class=\"item\">${c.text || ""}<small>片段 #${c.index ?? "-"} · 评分 ${c.score ?? "-"}</small></li>`).join("")
        : '<li class="item">暂无引用片段</li>';
    }

    function renderRecommendations(recommendations = []) {
      const target = $("recommendSectionList");
      if (!target) return;
      target.innerHTML = recommendations.length
        ? recommendations.map((r) => `<li class=\"item\">${r}</li>`).join("")
        : '<li class="item">暂无建议</li>';
    }

    function renderEvidencePanel(status, citations, recommendations) {
      const section = $("evidenceSectionPanel");
      if (!section) return;
      section.innerHTML = `
        <div class="evidence-title">证据与建议</div>
        <div id="hitBadge" class="badge ${status === 'hit' ? 'badge-hit' : 'badge-miss'}">${status === 'hit' ? '已命中合同原文' : '未命中原文'}</div>
        <div class="hint">引用片段</div>
        <ul id="evidenceSectionList" class="list">${(citations || []).length ? citations.map((c) => `<li class=\"item\">${c.text || ""}<small>片段 #${c.index ?? "-"} · 评分 ${c.score ?? "-"}</small></li>`).join("") : '<li class="item">暂无引用片段</li>'}</ul>
        <div class="hint">下一步建议</div>
        <ul id="recommendSectionList" class="list">${(recommendations || []).length ? recommendations.map((r) => `<li class=\"item\">${r}</li>`).join("") : '<li class="item">暂无建议</li>'}</ul>
      `;
    }

    async function postJson(path, payload) {
      const resp = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await resp.json().catch(() => ({}));
      if (!resp.ok) throw new Error(data.detail || data.error || `请求失败(${resp.status})`);
      return data;
    }

    const fileInput = $("fileInput");
    const selectFileBtn = $("selectFileBtn");
    const reselectFileBtn = $("reselectFileBtn");
    const confirmUpload = $("confirmUpload");
    const fileRemove = $("fileRemove");
    const uploadArea = $("uploadArea");

    selectFileBtn.onclick = () => fileInput.click();
    reselectFileBtn.onclick = () => fileInput.click();
    uploadArea.onclick = () => fileInput.click();
    fileRemove.onclick = () => { fileInput.value = ""; $("filePreview").style.display = "none"; $("uploadPlaceholder").style.display = "flex"; };

    fileInput.onchange = () => {
      const file = fileInput.files[0];
      if (!file) return;
      state.uploadedFileName = file.name;
      $("fileName").textContent = file.name;
      $("fileType").textContent = file.name.toLowerCase().endsWith(".pdf") ? "PDF文档" : "文本文件";
      $("fileSize").textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB`;
      $("filePreview").style.display = "block";
      $("uploadPlaceholder").style.display = "none";
      setGlobalStatus("文件已选择，等待上传");
      showPage("upload");
    };

    confirmUpload.onclick = async () => {
      setError("uploadError", "");
      const file = fileInput.files[0];
      if (!file) { setError("uploadError", "请先选择文件。"); return; }
      const fd = new FormData();
      fd.append("file", file);
      try {
        setGlobalStatus("正在上传并分析合同");
        const resp = await fetch("/api/v1/documents/analyze", { method: "POST", body: fd });
        const data = await resp.json().catch(() => ({}));
        if (!resp.ok || !data.success) throw new Error(data.detail || data.error || "上传分析失败");
        const d = data.data || {};
        state.documentId = d.document_id || "";
        $("uploadMeta").innerHTML = `文档：<b>${d.filename || "-"}</b><br/>摘要：${d.summary || "-"}<br/>文档ID：${state.documentId || "-"}`;
        renderKeywords(d.suggested_keywords || []);
        setGlobalStatus("合同已就绪，可以提问");
        showPage("chat");
        $("chatTitle").textContent = d.filename || "保险合同解释助手";
        addMessage("bot", `文档已上传。\n\n摘要：${d.summary || "-"}`);
      } catch (err) {
        setError("uploadError", err.message || "上传失败");
        setGlobalStatus("上传失败");
      }
    };

    $("askBtn").onclick = async () => {
      setError("uploadError", "");
      const q = $("questionInput").value.trim();
      if (!state.documentId) { setError("uploadError", "请先上传合同后再提问。"); return; }
      if (!q) { setError("uploadError", "请输入问题。"); return; }
      try {
        setGlobalStatus("正在检索条款并生成回答");
        addMessage("user", q);
        const data = await postJson("/api/v1/chat/completions", { document_id: state.documentId, question: q });
        const d = data.data || {};
        addMessage("bot", d.answer || "");
        renderEvidencePanel(d.status || "miss", d.citations || [], d.recommendations || []);
        setGlobalStatus("回答已生成");
      } catch (err) {
        setError("uploadError", err.message || "问答失败");
        setGlobalStatus("问答失败");
      }
    };

    $("archiveBtn").onclick = async () => {
      setError("uploadError", "");
      if (!state.documentId) { setError("uploadError", "请先上传合同并发起至少一次问答。"); return; }
      try {
        setGlobalStatus("正在生成归档报告");
        const data = await postJson("/api/v1/archive/generate-and-submit", { document_id: state.documentId, archive_type: "session_summary" });
        const payload = data.archive_payload || {};
        addMessage("bot", payload.generated_report_markdown || "未返回归档内容");
        setGlobalStatus("归档报告已生成");
      } catch (err) {
        setError("uploadError", err.message || "归档失败");
        setGlobalStatus("归档失败");
      }
    };

    $("uploadNavBtn").onclick = () => showPage("upload");
    $("askNavBtn").onclick = () => showPage("chat");
    $("evidenceNavBtn").onclick = () => showPage("chat");

    $("collapseToggle").onclick = () => {
      const sidebar = $("sidebar");
      sidebar.classList.toggle("collapsed");
    };

    showPage("welcome");
    renderEvidencePanel("miss", [], []);
  </script>
</body>
</html>
"""


def _backend_parts() -> tuple[str, int, str]:
    parsed = urlparse(BACKEND_BASE)
    host = parsed.hostname or "127.0.0.1"
    if parsed.port is not None:
        port = parsed.port
    else:
        port = 443 if parsed.scheme == "https" else 80
    scheme = parsed.scheme or "http"
    return host, port, scheme


def _pick_free_port(host: str, preferred_port: int, max_tries: int = 32) -> int:
    for offset in range(max_tries):
        candidate = preferred_port + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, candidate))
            except OSError:
                continue
            return candidate
    raise OSError(f"No free port found starting from {preferred_port}")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            data = HTML_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if self.path == "/health":
            body = b'{"ok":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        if not self.path.startswith("/api/v1/"):
            self.send_error(404, "Not Found")
            return

        host, port, scheme = _backend_parts()
        content_len = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_len) if content_len > 0 else b""

        req_headers = {
            "Content-Type": self.headers.get("Content-Type", "application/octet-stream"),
            "Accept": self.headers.get("Accept", "application/json"),
        }

        conn_cls = http.client.HTTPSConnection if scheme == "https" else http.client.HTTPConnection
        try:
            conn = conn_cls(host, port, timeout=180)
            conn.request("POST", self.path, body=raw_body, headers=req_headers)
            resp = conn.getresponse()
            payload = resp.read()

            self.send_response(resp.status)
            content_type = resp.getheader("Content-Type") or "application/json"
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except Exception as exc:
            body = (
                '{"success":false,"error":"ProxyError","detail":"%s"}' % str(exc).replace('"', "'")
            ).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        finally:
            try:
                conn.close()  # type: ignore[name-defined]
            except Exception:
                pass


def main() -> None:
    actual_port = _pick_free_port(HOST, PORT)
    server = ThreadingHTTPServer((HOST, actual_port), Handler)
    print("=" * 70)
    print("Frontend preview server started")
    if actual_port == PORT:
        print(f"Open:   http://{HOST}:{actual_port}")
    else:
        print(f"Open:   http://{HOST}:{actual_port} (default {PORT} is occupied)")
    print(f"Proxy:  {BACKEND_BASE}")
    print("=" * 70)
    server.serve_forever()


if __name__ == "__main__":
    main()
