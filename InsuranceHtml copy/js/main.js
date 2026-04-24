/**
 * =================================================================
 * 保险合同解释助手 - AI智能回复版主JavaScript文件
 * 版本: 1.2.0 (AI回复功能已激活)
 * 更新时间: 2025-01-14 15:30
 * =================================================================
 */

'use strict';

console.log('🤖 AI智能回复版本已加载 - v1.2.0');

/**
 * 应用程序主类 - 优化版
 */
class InsuranceAssistant {
    constructor() {
        this.elements = {};
        this.state = {
            collapsed: false,
            currentPage: 'welcome',
            uploadedFile: null,
            currentDocumentId: null, // 当前文档ID
            uploadHistory: [], // 存储上传的文档历史
            currentConversationId: null, // 当前对话ID
            inHistoryConversation: false, // 是否在历史对话中
            messages: [], // 存储所有消息历史
            evidenceStartIndex: null, // 存证开始时的消息索引
            evidenceRecords: [] // 存储存证记录
        };

        // 审核进度定时器
        this.currentAuditTimer = null;

        // 确保DOM完全加载后再初始化
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    /**
     * 初始化应用程序
     */
    init() {
        console.log('=== 保险合同解释助手初始化开始 ===');

        this.cacheElements();
        this.validateElements();
        this.bindEvents();
        this.setupTextareaAutoResize();

        // 初始化上传按钮状态
        this.updateSelectFileButton(false);

        console.log('=== 保险合同解释助手初始化完成 ===');
    }

    /**
     * 缓存DOM元素
     */
    cacheElements() {
        this.elements = {
            // 侧边栏元素
            collapseToggle: document.getElementById('collapseToggle'),
            aside: document.querySelector('aside'),
            uploadBtn: document.getElementById('uploadBtn'),
            askBtn: document.getElementById('askBtn'),
            evidenceBtn: document.getElementById('evidenceBtn'),
            logoIcon: document.getElementById('logoIcon'),
            historyContent: document.querySelector('.history-content'),
            evidenceSection: document.querySelector('.evidence-section'),

            // 主内容区元素
            welcomeArea: document.getElementById('welcomeArea'),
            uploadPage: document.getElementById('uploadPage'),
            chatPage: document.getElementById('chatPage'),
            chatTitle: document.getElementById('chatTitle'),
            chatMessages: document.getElementById('chatMessages'),
            evidenceDetailPage: document.getElementById('evidenceDetailPage'),

            // 存证相关元素
            backFromEvidence: document.getElementById('backFromEvidence'),
            evidenceId: document.getElementById('evidenceId'),
            evidenceTime: document.getElementById('evidenceTime'),
            evidenceStatus: document.getElementById('evidenceStatus'),
            evidenceMessages: document.getElementById('evidenceMessages'),

            // 输入框相关
            chatInputBar: document.querySelector('.chat-input-bar'),
            userInput: document.getElementById('userInput'),
            sendBtn: document.getElementById('sendBtn'),
            addFileBtn: document.getElementById('addFileBtn'),

            // 上传页面元素
            backToChat: document.getElementById('backToChat'),
            uploadArea: document.querySelector('.upload-area'),
            fileInput: document.getElementById('fileInput'),
            selectFileBtn: document.getElementById('selectFileBtn'),
            confirmUpload: document.getElementById('confirmUpload'),
            fileRemove: document.getElementById('fileRemove'),
            reselectFileBtn: document.getElementById('reselectFileBtn'),
            uploadPlaceholder: document.querySelector('.upload-placeholder p')
        };

        console.log('DOM元素缓存完成');
    }

    /**
     * 验证关键元素是否存在
     */
    validateElements() {
        const criticalElements = ['uploadBtn', 'welcomeArea', 'uploadPage', 'backToChat'];
        const missing = [];

        criticalElements.forEach(key => {
            if (!this.elements[key]) {
                missing.push(key);
            }
        });

        if (missing.length > 0) {
            console.error('缺少关键DOM元素:', missing);
        } else {
            console.log('所有关键DOM元素验证通过');
        }
    }

    /**
     * 绑定事件监听器
     */
    bindEvents() {
        console.log('开始绑定事件监听器...');

        // 侧边栏收起/展开
        this.bindEvent('collapseToggle', 'click', () => this.toggleSidebar());

        // 功能按钮
        this.bindEvent('uploadBtn', 'click', () => {
            console.log('上传按钮被点击');
            this.showUploadPage();
        });

        this.bindEvent('askBtn', 'click', () => {
            console.log('提问按钮被点击');
            this.addSimpleHistoryRecord();
            this.showChatPage();
        });
        this.bindEvent('evidenceBtn', 'click', () => this.showEvidencePage());

        // 存证详情页面相关
        this.bindEvent('backFromEvidence', 'click', () => {
            console.log('从存证详情页面返回');
            this.showChatPage();
        });

        // 聊天相关
        this.bindEvent('sendBtn', 'click', () => this.sendMessage());
        this.bindEvent('addFileBtn', 'click', () => this.addFile());

        if (this.elements.userInput) {
            this.elements.userInput.addEventListener('keydown', (e) => this.handleInputKeydown(e));
        }

        // 上传页面相关
        this.bindEvent('backToChat', 'click', () => {
            console.log('返回对话按钮被点击');
            this.showChatPage();
        });

        this.bindEvent('fileInput', 'change', (e) => this.handleFileSelect(e));
        // selectFileBtn 的事件现在由 updateSelectFileButton 动态管理
        this.bindEvent('confirmUpload', 'click', () => this.confirmUpload());

        // 文件移除按钮
        this.bindEvent('fileRemove', 'click', () => this.removeSelectedFile());

        // 重新选择文件按钮
        this.bindEvent('reselectFileBtn', 'click', () => this.triggerFileSelect());

        // 拖拽上传
        this.setupDragAndDrop();

        console.log('事件监听器绑定完成');
    }

    /**
     * 安全绑定事件的辅助方法
     */
    bindEvent(elementKey, eventType, handler) {
        const element = this.elements[elementKey];
        if (element) {
            element.addEventListener(eventType, handler);
            console.log(`${elementKey} ${eventType} 事件已绑定`);
        } else {
            console.warn(`元素 ${elementKey} 不存在，无法绑定 ${eventType} 事件`);
        }
    }

    /**
     * 设置文本域自动调整高度
     */
    setupTextareaAutoResize() {
        if (this.elements.userInput) {
            this.elements.userInput.addEventListener('input', () => this.autoResizeTextarea());
        }
    }

    /**
     * 自动调整文本域高度
     */
    autoResizeTextarea() {
        const textarea = this.elements.userInput;
        if (!textarea) return;

        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }

    /**
     * 切换侧边栏收起/展开状态
     */
    toggleSidebar() {
        this.state.collapsed = !this.state.collapsed;

        if (this.elements.aside) {
            this.elements.aside.style.width = this.state.collapsed ? '60px' : '260px';
        }

        // 隐藏或显示文字内容
        const hideElements = document.querySelectorAll('.menu-btn, .section-title, .placeholder, .profile');
        hideElements.forEach(el => {
            el.style.display = this.state.collapsed ? 'none' : '';
        });

        if (this.elements.collapseToggle) {
            this.elements.collapseToggle.textContent = this.state.collapsed ? '»' : '«';
        }

        console.log(`侧边栏${this.state.collapsed ? '收起' : '展开'}`);
    }

    /**
     * 显示上传页面
     */
    showUploadPage() {
        console.log('准备切换到上传页面...');
        this.switchPage('upload');
        console.log('已切换到上传页面');
    }

    /**
     * 显示聊天页面
     */
    showChatPage(documentData = null) {
        console.log('准备切换到聊天页面...', documentData);

        // 重置历史对话状态
        this.state.inHistoryConversation = false;
        this.state.currentConversationId = null;

        // 如果有文档数据，使用文档名称作为标题
        const chatTitle = documentData ? documentData.filename : 'XX公司（2025）重大疾病保险合同';

        // 直接切换到对话页面并显示对话内容
        this.showChatConversation(chatTitle, documentData);

        console.log('已切换到聊天页面');
    }

    /**
     * 显示对话页面
     * @param {string} chatTitle - 对话标题
     * @param {object} documentData - 文档数据
     */
    showChatConversation(chatTitle, documentData = null) {
        console.log('准备显示对话:', chatTitle, documentData);

        // 设置对话标题
        if (this.elements.chatTitle) {
            this.elements.chatTitle.textContent = chatTitle;
        }

        // 如果有文档数据，保存到状态中
        if (documentData) {
            this.state.currentDocumentId = documentData.documentId;
            this.state.inHistoryConversation = false;
            this.state.currentConversationId = null;
        } else {
            // 标记为历史对话模式
            this.state.inHistoryConversation = true;
            this.state.currentConversationId = chatTitle;
        }

        // 切换到对话页面
        this.switchPage('chat');

        // 清空聊天消息区域和消息历史
        if (this.elements.chatMessages) {
            this.elements.chatMessages.innerHTML = '';
        }
        this.state.messages = [];

        // 重置存证状态
        this.state.evidenceStartIndex = null;

        // 自动显示欢迎消息
        setTimeout(() => {
            const welcomeMessage = `已成功阅读<strong>XX公司(2025)重大疾病保险合同.pdf</strong>，接下来，你可以选择以下常见问题：<br><br>
<span style="margin-left: 20px;">1. 这份保险保障哪些重大疾病？</span><br>
<span style="margin-left: 20px;">2. 我目前的健康状态能不能买？</span><br>
<span style="margin-left: 20px;">3. 买多少钱合适？保费怎么算？</span><br>
<span style="margin-left: 20px;">4. 理赔条件是什么？流程复杂吗？</span><br>
<span style="margin-left: 20px;">5. 以后不想要了能退吗？会不会亏？</span><br><br>
或直接提出你想了解的内容。`;
            this.displayMessage('assistant', welcomeMessage, true, true);
        }, 500);

        // 延迟一下聚焦输入框
        setTimeout(() => {
            this.focusInput();
        }, 100);

        console.log('已显示对话页面，进入历史对话模式');
    }

    /**
     * 页面切换核心方法
     * @param {string} page - 页面类型: 'welcome' | 'upload' | 'chat' | 'evidence-detail'
     */
    switchPage(page) {
        this.state.currentPage = page;

        // 清理审核进度定时器
        if (this.currentAuditTimer) {
            clearInterval(this.currentAuditTimer);
            this.currentAuditTimer = null;
        }

        // 如果切换到非对话页面，重置存证按钮状态和历史对话状态
        if (page !== 'chat') {
            this.resetEvidenceButtonState();

            if (page === 'welcome' || page === 'upload') {
                this.state.inHistoryConversation = false;
                this.state.currentConversationId = null;
                console.log('已退出历史对话模式');
            }
        }

        switch (page) {
            case 'upload':
                this.hideElement(this.elements.welcomeArea, '欢迎区域');
                this.hideElement(this.elements.chatInputBar, '聊天输入框');
                this.hideElement(this.elements.chatPage, '对话页面');
                this.hideElement(this.elements.evidenceDetailPage, '存证详情页面');
                this.showElement(this.elements.uploadPage, '上传页面');
                break;

            case 'chat':
                this.hideElement(this.elements.welcomeArea, '欢迎区域');
                this.hideElement(this.elements.uploadPage, '上传页面');
                this.hideElement(this.elements.evidenceDetailPage, '存证详情页面');
                this.showElement(this.elements.chatInputBar, '聊天输入框');
                this.showElement(this.elements.chatPage, '对话页面');
                break;

            case 'evidence-detail':
                this.hideElement(this.elements.welcomeArea, '欢迎区域');
                this.hideElement(this.elements.uploadPage, '上传页面');
                this.hideElement(this.elements.chatPage, '对话页面');
                this.hideElement(this.elements.chatInputBar, '聊天输入框');
                this.showElement(this.elements.evidenceDetailPage, '存证详情页面');
                break;

            case 'welcome':
            default:
                this.showElement(this.elements.welcomeArea, '欢迎区域');
                this.showElement(this.elements.chatInputBar, '聊天输入框');
                this.hideElement(this.elements.uploadPage, '上传页面');
                this.hideElement(this.elements.chatPage, '对话页面');
                this.hideElement(this.elements.evidenceDetailPage, '存证详情页面');
                break;
        }
    }

    /**
     * 显示元素
     * @param {HTMLElement} element 
     * @param {string} name - 元素名称（用于日志）
     */
    showElement(element, name = '元素') {
        if (element) {
            element.style.display = 'flex';
            element.classList.add('fade-in');
            console.log(`显示${name}`);
        } else {
            console.warn(`无法显示${name}：元素不存在`);
        }
    }

    /**
     * 隐藏元素
     * @param {HTMLElement} element 
     * @param {string} name - 元素名称（用于日志）
     */
    hideElement(element, name = '元素') {
        if (element) {
            element.style.display = 'none';
            element.classList.remove('fade-in');
            console.log(`隐藏${name}`);
        } else {
            console.warn(`无法隐藏${name}：元素不存在`);
        }
    }

    /**
     * 聚焦输入框
     */
    focusInput() {
        if (this.elements.userInput) {
            this.elements.userInput.focus();
            console.log('输入框已获得焦点');
        }
    }

    /**
     * 发送消息 - 使用真实API
     */
    async sendMessage() {
        const text = this.elements.userInput?.value?.trim();
        if (!text) return;

        console.log('🔥 用户发送消息:', text);

        // 检查是否有当前文档ID
        if (!this.state.currentDocumentId) {
            alert('请先上传文档后再进行问答');
            return;
        }

        // 显示用户消息
        this.displayMessage('user', text);

        // 清空输入框
        if (this.elements.userInput) {
            this.elements.userInput.value = '';
            this.autoResizeTextarea();
        }

        // 显示加载状态
        this.displayMessage('assistant', '正在思考中...');

        try {
            // 调用聊天API
            console.log('发送API请求，document_id:', this.state.currentDocumentId);
            const response = await fetch('http://localhost:8001/api/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    document_id: this.state.currentDocumentId,
                    question: text
                })
            });

            if (!response.ok) {
                throw new Error(`API错误: ${response.status}`);
            }

            const result = await response.json();
            console.log('🤖 API回复:', result);

            // 移除加载状态，显示真实回复
            this.removeLastMessage(); // 移除"正在思考中..."
            this.displayMessage('assistant', result.data.answer || '抱歉，我暂时无法回答这个问题。');

        } catch (error) {
            console.error('发送消息失败:', error);
            // 移除加载状态，显示错误信息
            this.removeLastMessage(); // 移除"正在思考中..."
            this.displayMessage('assistant', '抱歉，服务器暂时无法响应，请稍后重试。');
        }
    }

    /**
     * 处理输入框键盘事件
     * @param {KeyboardEvent} e 
     */
    handleInputKeydown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }

    /**
     * 移除最后一条消息
     */
    removeLastMessage() {
        const chatArea = this.elements.chatArea;
        if (chatArea && chatArea.lastElementChild) {
            chatArea.removeChild(chatArea.lastElementChild);
        }
    }

    /**
     * 生成AI回复
     * @param {string} userMessage - 用户输入的消息
     * @returns {string} AI回复内容
     */
    generateAIResponse(userMessage) {
        console.log('🤖 AI正在处理用户消息:', userMessage);
        const message = userMessage.toLowerCase().trim();

        // 高血压相关问题检测
        if (message.includes('高血压') && (message.includes('投保') || message.includes('保险') || message.includes('买'))) {
            console.log('🔍 检测到高血压投保相关问题');
            return `根据保险合同第 4.2 条关于重大疾病的定义，轻度高血压并不在拒保范围内，是可以投保的。

另外，根据《中国高血压防治指南》：

• 轻度高血压：140/90 mmHg ～ 160/100 mmHg
• 中度高血压：160/100 mmHg ～ 180/110 mmHg  
• 重度高血压：180/110 mmHg 以上

为了帮你更准确地判断投保资格，能否告诉我你的年龄和目前的血压范围呢？`;
        }

        // 年龄相关回复
        if (message.includes('年龄') || /\d+岁/.test(message)) {
            return '感谢你提供年龄信息。年龄是投保的重要因素之一，不同年龄段的保费和保障范围会有所不同。请问你还有其他健康状况需要说明吗？';
        }

        // 血压数值相关回复
        if (/\d+\/\d+/.test(message) || message.includes('血压')) {
            return '根据你提供的血压信息，我会为你做详细的投保资格评估。一般来说，如果血压控制在正常范围内，投保是没有问题的。如有疑问，建议咨询专业的保险顾问。';
        }

        // 保险条款相关
        if (message.includes('条款') || message.includes('合同') || message.includes('保障')) {
            return '我可以帮你解读保险合同的各项条款。请告诉我你想了解合同的哪个具体方面，比如保障范围、免责条款、理赔流程等？';
        }

        // 理赔相关
        if (message.includes('理赔') || message.includes('报销') || message.includes('赔付')) {
            return '关于理赔流程，你需要在确诊后及时联系保险公司，准备好相关医疗证明材料。具体的理赔标准和流程在合同第6-8条中有详细说明。有什么具体的理赔问题吗？';
        }

        // 默认回复
        return '我是你的保险合同解释助手，可以帮助你理解合同条款、评估投保资格、解答保险相关问题。请告诉我你想了解什么？';
    }

    /**
     * 显示消息
     * @param {string} sender - 发送者类型: 'user' | 'assistant'
     * @param {string} message - 消息内容
     */
    displayMessage(sender, message) {
        console.log(`[${sender}]`, message);

        const chatMessages = this.elements.chatMessages;
        if (!chatMessages) return;

        // 将消息保存到消息历史中
        const messageObj = {
            type: 'message',
            sender: sender,
            content: message,
            timestamp: new Date().toISOString()
        };
        this.state.messages.push(messageObj);

        // 创建消息容器
        const messageDiv = document.createElement('div');
        messageDiv.className = sender === 'user' ? 'user-message' : 'bot-message';

        if (sender === 'assistant') {
            // 机器人消息（包含头像、消息内容和操作按钮）
            messageDiv.innerHTML = `
                <div class="bot-avatar">
                    <img src="icon/robot.svg" alt="bot" />
                </div>
                <div class="bot-message-wrapper">
                    <div class="message-content">
                        <p lang="zh">${message}</p>
                    </div>
                    <div class="message-actions">
                        <button class="message-action-btn copy-btn" title="复制">
                            <img src="icon/copy.svg" alt="复制" />
                        </button>
                        <button class="message-action-btn regenerate-btn" title="重新生成">
                            <img src="icon/reload-svgrepo-com.svg" alt="重新生成" />
                        </button>
                    </div>
                </div>
            `;
        } else {
            // 用户消息（消息内容在上，操作按钮在下）
            messageDiv.innerHTML = `
                <div class="message-content">
                    <p lang="zh">${this.escapeHtml(message)}</p>
                </div>
                <div class="message-actions">
                    <button class="message-action-btn copy-btn" title="复制">
                        <img src="icon/copy.svg" alt="复制" />
                    </button>
                    <button class="message-action-btn edit-btn" title="编辑">
                        <img src="icon/edit.svg" alt="编辑" />
                    </button>
                </div>
            `;
        }

        chatMessages.appendChild(messageDiv);

        // 滚动到底部 - 滚动整个聊天页面而不是消息区域
        const chatPage = document.getElementById('chatPage');
        if (chatPage) {
            chatPage.scrollTop = chatPage.scrollHeight;
        }
    }

    /**
     * 转义HTML特殊字符
     * @param {string} text 
     * @returns {string}
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 添加文件
     */
    addFile() {
        console.log('添加文件功能');
        alert('TODO: 添加图片 / 附件等');
    }

    /**
     * 显示存证页面
     */
    showEvidencePage() {
        console.log('存证功能');

        // 检查是否在对话窗口且有消息
        if (!this.hasActiveConversation()) {
            // 根据当前状态给出不同的提示
            if (!this.state.inHistoryConversation) {
                alert('请点击历史记录进入具体对话后再进行存证哦！');
            } else {
                alert('请先在当前对话中发送消息后再进行存证！');
            }
            return;
        }

        // 如果满足条件，切换存证按钮状态
        this.toggleEvidenceButtonState();
    }

    /**
     * 检查是否有活跃的对话
     * @returns {boolean}
     */
    hasActiveConversation() {
        // 必须在历史对话模式中
        if (!this.state.inHistoryConversation) {
            console.log('不在历史对话模式中');
            return false;
        }

        // 必须在对话页面
        const isInChatMode = (this.state.currentPage === 'chat');

        // 检查是否有消息
        const chatMessages = this.elements.chatMessages;
        const hasMessages = chatMessages && chatMessages.children.length > 0;

        console.log('检查对话状态:', {
            currentPage: this.state.currentPage,
            inHistoryConversation: this.state.inHistoryConversation,
            currentConversationId: this.state.currentConversationId,
            isInChatMode: isInChatMode,
            hasMessages: hasMessages
        });

        return isInChatMode && hasMessages;
    }

    /**
     * 切换存证按钮状态
     */
    toggleEvidenceButtonState() {
        const evidenceBtn = this.elements.evidenceBtn;
        if (!evidenceBtn) return;

        // 检查当前状态
        const isActivated = evidenceBtn.classList.contains('evidence-activated');

        if (isActivated) {
            // 如果已经激活，结束存证并保存记录
            evidenceBtn.classList.remove('evidence-activated');
            console.log('存证按钮已取消激活');

            // 结束存证，生成第二条分割线并保存存证记录
            this.endEvidenceRecording();
        } else {
            // 激活存证按钮，开始存证
            evidenceBtn.classList.add('evidence-activated');
            console.log('存证按钮已激活');

            // 存证激活时，在对话中生成分割线并开始记录
            this.startEvidenceRecording();
        }
    }

    /**
     * 重置存证按钮状态
     */
    resetEvidenceButtonState() {
        const evidenceBtn = this.elements.evidenceBtn;
        if (!evidenceBtn) return;

        evidenceBtn.classList.remove('evidence-activated');
        console.log('存证按钮状态已重置');
    }

    /**
     * 添加存证分割线
     */
    addEvidenceDivider() {
        const chatMessages = this.elements.chatMessages;
        if (!chatMessages) return;

        console.log('正在添加存证分割线...');

        // 创建分割线容器
        const dividerDiv = document.createElement('div');
        dividerDiv.className = 'evidence-divider';

        // 添加样式 - 稍微粗一点的黑色线条
        dividerDiv.style.cssText = `
            width: 100%;
            height: 2px;
            background-color: #000000;
            margin: 20px 0;
        `;

        // 将分割线添加到聊天消息区域
        chatMessages.appendChild(dividerDiv);

        // 将分割线信息也记录到消息历史中
        const dividerMessage = {
            type: 'divider',
            timestamp: new Date().toISOString(),
            content: '存证分割线'
        };
        this.state.messages.push(dividerMessage);

        // 根据当前状态添加不同的AI提示消息
        setTimeout(() => {
            let evidenceMessage;
            if (this.state.evidenceStartIndex !== null) {
                // 这是开始分割线（已经设置了开始索引）
                evidenceMessage = '已为你开启存证服务！接下来的聊天都会被记录并进行存证，请将你的问题再问一遍。';
            } else {
                // 这是结束分割线（开始索引已被重置为null）
                evidenceMessage = '存证记录已完成！两条分割线之间的对话内容已保存到存证记录中。';
            }
            this.displayMessage('assistant', evidenceMessage);
        }, 300);

        // 滚动到底部
        const chatPage = document.getElementById('chatPage');
        if (chatPage) {
            chatPage.scrollTop = chatPage.scrollHeight;
        }

        console.log('存证分割线已添加');
    }

    /**
     * 开始存证记录
     */
    startEvidenceRecording() {
        // 记录当前消息索引作为存证开始位置
        this.state.evidenceStartIndex = this.state.messages.length;

        // 添加开始分割线
        this.addEvidenceDivider();

        console.log('存证记录开始，起始索引：', this.state.evidenceStartIndex);
    }

    /**
     * 结束存证记录
     */
    endEvidenceRecording() {
        if (this.state.evidenceStartIndex === null) {
            console.warn('未找到存证开始标记');
            return;
        }

        // 添加结束分割线
        this.addEvidenceDivider();

        // 直接获取聊天消息区域中从第一个存证分割线到最后一个分割线的所有DOM内容
        const chatMessages = this.elements.chatMessages;
        if (!chatMessages) return;

        // 找到所有存证分割线
        const dividers = chatMessages.querySelectorAll('.evidence-divider');
        if (dividers.length < 2) {
            console.warn('未找到足够的存证分割线');
            return;
        }

        // 获取第一个和最后一个分割线
        const firstDivider = dividers[dividers.length - 2]; // 倒数第二个是开始分割线
        const lastDivider = dividers[dividers.length - 1];  // 最后一个是结束分割线

        // 获取分割线之间的所有DOM元素（包括分割线本身）
        const evidenceContent = document.createElement('div');
        let currentElement = firstDivider;

        // 复制从第一个分割线到最后一个分割线的所有元素
        while (currentElement) {
            evidenceContent.appendChild(currentElement.cloneNode(true));
            if (currentElement === lastDivider) break;
            currentElement = currentElement.nextElementSibling;
        }

        // 创建存证记录
        const evidenceRecord = {
            id: Date.now(), // 使用时间戳作为ID
            time: new Date().toLocaleString(),
            status: 'pending', // 审核状态：pending(待审核), approved(已通过), rejected(已拒绝)
            htmlContent: evidenceContent.innerHTML // 保存原始HTML内容
        };

        // 保存存证记录
        this.state.evidenceRecords.push(evidenceRecord);

        console.log('存证记录已保存：', evidenceRecord);
        console.log('总存证记录数：', this.state.evidenceRecords.length);

        // 更新存证记录显示
        this.updateEvidenceDisplay();

        // 重置存证状态
        this.state.evidenceStartIndex = null;
    }

    /**
     * 更新存证记录显示
     */
    updateEvidenceDisplay() {
        if (!this.elements.evidenceSection) {
            console.warn('存证记录区域元素未找到');
            return;
        }

        // 清空现有内容
        const existingContent = this.elements.evidenceSection.querySelector('.evidence-content');
        if (existingContent) {
            existingContent.remove();
        }

        // 移除占位符
        const placeholder = this.elements.evidenceSection.querySelector('.placeholder');
        if (placeholder) {
            placeholder.remove();
        }

        // 如果没有存证记录，显示占位符
        if (this.state.evidenceRecords.length === 0) {
            const newPlaceholder = document.createElement('div');
            newPlaceholder.className = 'placeholder';
            newPlaceholder.textContent = '暂无记录';
            this.elements.evidenceSection.appendChild(newPlaceholder);
            return;
        }

        // 创建存证记录内容容器
        const evidenceContent = document.createElement('div');
        evidenceContent.className = 'evidence-content';

        // 为每个存证记录创建显示项
        this.state.evidenceRecords.forEach((record, index) => {
            const recordItem = document.createElement('div');
            recordItem.className = 'evidence-item';
            recordItem.innerHTML = `
                <div class="evidence-item-header">
                    <div class="evidence-item-title">XX公司（2025）重大疾病保险合同</div>
                </div>
                <div class="evidence-item-meta">
                    ${record.time}
                </div>
            `;

            // 添加点击事件，可以查看存证详情
            recordItem.addEventListener('click', () => {
                this.showEvidenceDetail(record);
            });

            evidenceContent.appendChild(recordItem);
        });

        // 将内容添加到存证区域
        this.elements.evidenceSection.appendChild(evidenceContent);

        console.log('存证记录显示已更新，共', this.state.evidenceRecords.length, '条记录');
    }

    /**
     * 显示存证详情
     * @param {Object} record 存证记录
     */
    showEvidenceDetail(record) {
        console.log('显示存证详情:', record);

        // 设置存证详情页面标题
        const evidenceDetailTitle = document.getElementById('evidenceDetailTitle');
        if (evidenceDetailTitle) {
            evidenceDetailTitle.textContent = 'XX公司（2025）重大疾病保险合同';
        }

        // 填充存证基本信息
        if (this.elements.evidenceId) {
            this.elements.evidenceId.textContent = record.id;
        }
        if (this.elements.evidenceTime) {
            this.elements.evidenceTime.textContent = record.time;
        }

        // 填充审核状态信息
        if (this.elements.evidenceStatus) {
            this.elements.evidenceStatus.textContent = this.getStatusText(record.status);
            this.elements.evidenceStatus.className = `status-badge ${record.status}`;
        }

        // 直接显示保存的HTML内容
        if (this.elements.evidenceMessages && record.htmlContent) {
            this.elements.evidenceMessages.innerHTML = record.htmlContent;
        }

        // 为下载按钮绑定事件
        const downloadBtn = document.getElementById('downloadEvidenceBtn');
        if (downloadBtn) {
            // 移除之前的事件监听器（如果有的话）
            const newDownloadBtn = downloadBtn.cloneNode(true);
            downloadBtn.parentNode.replaceChild(newDownloadBtn, downloadBtn);

            // 添加新的事件监听器
            newDownloadBtn.addEventListener('click', () => {
                this.downloadEvidenceRecord(record);
            });
        }

        // 如果是待审核状态，启动审核进度动画
        setTimeout(() => {
            if (record.status === 'pending') {
                this.startAuditProgress(record);
            } else if (record.status === 'approved') {
                // 如果已经通过审核，显示完成状态的进度条
                this.showApprovedProgress(record);
            }
        }, 1000); // 延迟1秒后开始审核进度

        // 切换到存证详情页面
        this.switchPage('evidence-detail');
    }

    /**
     * 获取审核状态的中文文本
     * @param {string} status - 审核状态
     * @returns {string} 中文状态文本
     */
    getStatusText(status) {
        const statusMap = {
            'pending': '待审核',
            'approved': '已通过',
            'rejected': '已拒绝'
        };
        return statusMap[status] || '未知状态';
    }

    /**
     * 开始审核进度动画
     * @param {Object} record - 存证记录
     */
    startAuditProgress(record) {
        const evidenceProgress = document.getElementById('evidenceProgress');
        const evidenceStatusIndicator = document.querySelector('.evidence-status-indicator');

        if (!evidenceProgress || record.status !== 'pending') {
            return;
        }

        // 保持状态指示器显示，同时显示进度条
        evidenceStatusIndicator.style.display = 'flex';
        evidenceProgress.style.display = 'block';

        // 审核步骤配置
        const auditSteps = [
            { id: 'step1', title: '用户审核提交', completed: true, time: '已完成' },
            { id: 'step2', title: '保险公司审核', completed: false, time: '处理中...' },
            { id: 'step3', title: '公证公司审核', completed: false, time: '等待中' },
            { id: 'step4', title: '法律顾问审核', completed: false, time: '等待中' }
        ];

        let currentStep = 1; // 从第二步开始（第一步已完成）

        // 初始化进度条状态
        this.updateProgressStep(auditSteps[0], true, false); // 第一步已完成
        this.updateProgressStep(auditSteps[1], false, true); // 第二步进行中

        const progressInterval = setInterval(() => {
            // 完成当前步骤
            this.updateProgressStep(auditSteps[currentStep], true, false);

            // 更新连接线状态
            const lineId = `line${currentStep}`;
            const line = document.getElementById(lineId);
            if (line) {
                line.classList.add('completed');
            }

            currentStep++;

            if (currentStep < auditSteps.length) {
                // 激活下一步
                this.updateProgressStep(auditSteps[currentStep], false, true);
            } else {
                // 所有步骤完成
                clearInterval(progressInterval);
                setTimeout(() => {
                    // 更新记录状态为已通过
                    record.status = 'approved';
                    this.showCompletedAudit(record);
                }, 1000);
            }
        }, 10000); // 每10秒进行下一步

        // 保存定时器引用，以便可能需要清除
        this.currentAuditTimer = progressInterval;
    }

    /**
     * 更新进度步骤状态
     * @param {Object} stepConfig - 步骤配置
     * @param {boolean} isCompleted - 是否已完成
     * @param {boolean} isActive - 是否正在进行
     */
    updateProgressStep(stepConfig, isCompleted, isActive) {
        const stepElement = document.getElementById(stepConfig.id);
        if (!stepElement) return;

        const stepTime = stepElement.querySelector('.step-time');

        // 移除所有状态类
        stepElement.classList.remove('active', 'completed');

        if (isCompleted) {
            stepElement.classList.add('completed');
            if (stepTime) {
                stepTime.textContent = '已完成';
                stepTime.style.color = '#10b981';
            }
        } else if (isActive) {
            stepElement.classList.add('active');
            if (stepTime) {
                stepTime.textContent = '处理中...';
                stepTime.style.color = '#3b82f6';
            }
        } else {
            if (stepTime) {
                stepTime.textContent = '等待中';
                stepTime.style.color = '#9ca3af';
            }
        }
    }

    /**
     * 显示审核完成状态
     * @param {Object} record - 存证记录
     */
    showCompletedAudit(record) {
        const evidenceProgress = document.getElementById('evidenceProgress');
        const evidenceStatusIndicator = document.querySelector('.evidence-status-indicator');
        const evidenceStatus = document.getElementById('evidenceStatus');

        // 保持进度条和状态指示器都显示
        evidenceProgress.style.display = 'block';
        evidenceStatusIndicator.style.display = 'flex';

        // 更新状态显示
        if (evidenceStatus) {
            evidenceStatus.textContent = this.getStatusText(record.status);
            evidenceStatus.className = `status-badge ${record.status}`;
        }

        // 确保所有步骤都显示为已完成
        const allSteps = ['step1', 'step2', 'step3', 'step4'];
        const allLines = ['line1', 'line2', 'line3'];

        allSteps.forEach(stepId => {
            const stepElement = document.getElementById(stepId);
            if (stepElement) {
                stepElement.classList.remove('active');
                stepElement.classList.add('completed');
                const stepTime = stepElement.querySelector('.step-time');
                if (stepTime) {
                    stepTime.textContent = '已完成';
                    stepTime.style.color = '#10b981';
                }
            }
        });

        allLines.forEach(lineId => {
            const line = document.getElementById(lineId);
            if (line) {
                line.classList.add('completed');
            }
        });

        // 更新存证记录列表中的状态
        this.updateEvidenceDisplay();

        // 添加审核通过后的基本信息
        this.addApprovedEvidenceInfo();

        console.log('审核流程已完成，状态更新为：', record.status);
    }

    /**
     * 显示已审核通过的进度条
     * @param {Object} record - 存证记录
     */
    showApprovedProgress(record) {
        const evidenceProgress = document.getElementById('evidenceProgress');
        const evidenceStatusIndicator = document.querySelector('.evidence-status-indicator');

        if (!evidenceProgress) return;

        // 保持状态指示器和进度条都显示
        evidenceStatusIndicator.style.display = 'flex';
        evidenceProgress.style.display = 'block';

        // 所有步骤都设置为已完成
        const allSteps = ['step1', 'step2', 'step3', 'step4'];
        const allLines = ['line1', 'line2', 'line3'];

        allSteps.forEach(stepId => {
            const stepElement = document.getElementById(stepId);
            if (stepElement) {
                stepElement.classList.remove('active');
                stepElement.classList.add('completed');
                const stepTime = stepElement.querySelector('.step-time');
                if (stepTime) {
                    stepTime.textContent = '已完成';
                    stepTime.style.color = '#10b981';
                }
            }
        });

        allLines.forEach(lineId => {
            const line = document.getElementById(lineId);
            if (line) {
                line.classList.add('completed');
            }
        });

        // 添加审核通过后的基本信息
        this.addApprovedEvidenceInfo();

        console.log('已审核通过状态的进度条已显示');
    }

    /**
     * 添加审核通过后的基本信息
     */
    addApprovedEvidenceInfo() {
        const evidenceInfoCard = document.querySelector('.evidence-info-card');
        if (!evidenceInfoCard) return;

        // 检查是否已经添加过发起方信息，避免重复添加
        const existingInitiator = evidenceInfoCard.querySelector('.initiator-row');
        if (existingInitiator) return;

        // 获取提交时间（从第二行获取）
        const timeRow = evidenceInfoCard.children[1];
        const submitTimeElement = timeRow?.querySelector('.evidence-info-value');
        const submitTimeStr = submitTimeElement?.textContent || new Date().toLocaleString();

        // 解析提交时间
        const submitTime = new Date(submitTimeStr);

        // 计算发起时间（比提交时间多2分30秒）
        const initiateTime = new Date(submitTime.getTime() + (2 * 60 + 30) * 1000);

        // 计算上链时间（比提交时间多28分23秒）
        const onChainTime = new Date(submitTime.getTime() + (28 * 60 + 23) * 1000);

        // 生成随机哈希
        const randomHash = this.generateRandomHash();

        // 创建要添加的信息行数组
        const newRows = [
            {
                className: 'evidence-info-row initiator-row',
                label: '发起方：',
                value: 'XX保险公司'
            },
            {
                className: 'evidence-info-row initiate-time-row',
                label: '发起时间：',
                value: initiateTime.toLocaleString()
            },
            {
                className: 'evidence-info-row onchain-time-row',
                label: '上链时间：',
                value: onChainTime.toLocaleString()
            },
            {
                className: 'evidence-info-row hash-row',
                label: '上链哈希：',
                value: randomHash
            }
        ];

        // 在第二行（提交时间）之后插入新信息
        let insertPosition = timeRow;

        newRows.forEach(rowData => {
            const row = document.createElement('div');
            row.className = rowData.className;
            row.innerHTML = `
                <span class="evidence-info-label">${rowData.label}</span>
                <span class="evidence-info-value">${rowData.value}</span>
            `;

            if (insertPosition && insertPosition.nextElementSibling) {
                evidenceInfoCard.insertBefore(row, insertPosition.nextElementSibling);
            } else {
                evidenceInfoCard.appendChild(row);
            }

            insertPosition = row; // 更新插入位置为刚插入的行
        });

        console.log('已添加审核通过后的详细信息');
    }

    /**
     * 生成随机哈希值
     * @returns {string} 64位十六进制哈希值
     */
    generateRandomHash() {
        const chars = '0123456789abcdef';
        let hash = '';
        for (let i = 0; i < 64; i++) {
            hash += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return hash;
    }

    /**
     * 下载存证记录
     * @param {Object} record - 存证记录
     */
    downloadEvidenceRecord(record) {
        try {
            // 创建下载内容
            const downloadContent = `
存证记录详情
=================

存证ID: ${record.id}
提交时间: ${record.time}
审核状态: ${this.getStatusText(record.status)}
文档标题: XX公司（2025）重大疾病保险合同

存证内容:
${this.extractTextFromHTML(record.htmlContent)}

---
此存证记录由保险合同解释助手系统生成
生成时间: ${new Date().toLocaleString()}
`;

            // 创建下载链接
            const blob = new Blob([downloadContent], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `存证记录_${record.id}_${new Date().toISOString().slice(0, 10)}.txt`;

            // 触发下载
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // 清理URL对象
            URL.revokeObjectURL(url);

            console.log('存证记录下载成功:', record.id);
        } catch (error) {
            console.error('下载存证记录失败:', error);
            alert('下载失败，请稍后重试');
        }
    }

    /**
     * 从HTML中提取纯文本内容
     * @param {string} html - HTML内容
     * @returns {string} 纯文本内容
     */
    extractTextFromHTML(html) {
        const div = document.createElement('div');
        div.innerHTML = html;

        // 移除分割线
        const dividers = div.querySelectorAll('.evidence-divider');
        dividers.forEach(divider => divider.remove());

        // 提取文本内容
        return div.textContent || div.innerText || '';
    }

    /**
     * 触发文件选择（测试模式：模拟选择test_contract.pdf）
     */
    triggerFileSelect() {
        console.log('测试模式：模拟选择test_contract.pdf文件');

        // 模拟创建一个文件对象
        const mockFile = new File([''], 'test_contract.pdf', { type: 'application/pdf' });
        this.state.uploadedFile = mockFile;

        // 显示文件预览信息
        this.showFilePreview({
            name: 'test_contract.pdf',
            type: 'application/pdf',
            size: 10992303 // 实际文件大小
        });

        // 更新按钮状态为"点击上传"
        this.updateSelectFileButton(true);
    }

    /**
     * 处理文件选择
     * @param {Event} e 
     */
    handleFileSelect(e) {
        const file = e.target.files[0];
        if (!file) return;

        this.state.uploadedFile = file;

        // 验证文件
        if (!this.validateFile(file)) {
            return;
        }

        // 显示文件预览
        this.showFilePreview(file);

        console.log('文件已选择:', file.name, this.formatFileSize(file.size), file.type);
    }

    /**
     * 显示文件预览
     * @param {File} file 
     */
    showFilePreview(file) {
        const uploadPlaceholder = document.getElementById('uploadPlaceholder');
        const filePreview = document.getElementById('filePreview');
        const fileName = document.getElementById('fileName');
        const fileType = document.getElementById('fileType');
        const fileSize = document.getElementById('fileSize');

        if (!filePreview || !fileName || !fileType || !fileSize) return;

        // 隐藏上传占位符，显示文件预览
        if (uploadPlaceholder) uploadPlaceholder.style.display = 'none';
        filePreview.style.display = 'block';

        // 填充文件信息
        fileName.textContent = file.name;
        fileSize.textContent = this.formatFileSize(file.size);

        // 根据文件类型设置图标和类型文字
        const fileTypeIcon = document.querySelector('.file-type-icon');
        if (file.type.includes('pdf')) {
            fileType.textContent = 'PDF文档';
            if (fileTypeIcon) {
                fileTypeIcon.src = 'https://api.iconify.design/vscode-icons:file-type-pdf2.svg';
                fileTypeIcon.alt = 'pdf';
            }
        } else if (file.type.includes('word') || file.type.includes('document')) {
            fileType.textContent = 'Word文档';
            if (fileTypeIcon) {
                fileTypeIcon.src = 'https://api.iconify.design/vscode-icons:file-type-word.svg';
                fileTypeIcon.alt = 'word';
            }
        } else if (file.type.includes('text')) {
            fileType.textContent = 'TXT文档';
            if (fileTypeIcon) {
                fileTypeIcon.src = 'https://api.iconify.design/vscode-icons:file-type-text.svg';
                fileTypeIcon.alt = 'txt';
            }
        } else if (file.type.includes('image')) {
            fileType.textContent = '图片文件';
            if (fileTypeIcon) {
                fileTypeIcon.src = 'https://api.iconify.design/vscode-icons:file-type-image.svg';
                fileTypeIcon.alt = 'image';
            }
        } else {
            fileType.textContent = '文档';
        }

        // 更改选择文件按钮为点击上传按钮
        this.updateSelectFileButton(true);
    }

    /**
     * 更新选择文件按钮状态
     * @param {boolean} fileSelected - 是否已选择文件
     */
    updateSelectFileButton(fileSelected) {
        const selectFileBtn = this.elements.selectFileBtn;
        if (!selectFileBtn) return;

        if (fileSelected) {
            selectFileBtn.textContent = '点击上传';
            selectFileBtn.onclick = () => this.confirmUpload();
        } else {
            selectFileBtn.textContent = '选择文件';
            selectFileBtn.onclick = () => this.triggerFileSelect();
        }
    }

    /**
     * 验证文件
     * @param {File} file 
     * @returns {boolean}
     */
    validateFile(file) {
        const maxSize = 10 * 1024 * 1024; // 10MB
        const allowedTypes = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'image/jpeg',
            'image/png',
            'image/jpg'
        ];

        if (file.size > maxSize) {
            alert('文件大小不能超过10MB');
            return false;
        }

        if (!allowedTypes.includes(file.type)) {
            alert('不支持的文件格式，请上传PDF、Word或图片文件');
            return false;
        }

        return true;
    }

    /**
     * 确认上传
     */
    async confirmUpload() {
        // 测试模式：忽略文件选择，直接使用test_contract.pdf
        console.log('测试模式：直接使用test_contract.pdf进行测试');

        // 使用硬编码的配置
        const apiBaseUrl = 'http://localhost:8001';
        const apiEndpoint = '/api/v1/documents/analyze';
        const fullUrl = `${apiBaseUrl}${apiEndpoint}`;

        console.log('使用API URL:', fullUrl);

        // 显示加载状态
        const uploadBtn = this.elements.confirmUpload;
        if (uploadBtn) {
            uploadBtn.classList.add('loading');
            uploadBtn.textContent = '分析中...';
            uploadBtn.disabled = true;
        }

        try {
            // 获取test_contract.pdf文件（现在在同一目录）
            const fileResponse = await fetch('./test_contract.pdf');
            if (!fileResponse.ok) {
                throw new Error('无法获取test_contract.pdf文件');
            }
            const fileBlob = await fileResponse.blob();

            // 创建FormData，完全模拟curl命令
            const formData = new FormData();
            formData.append('file', new File([fileBlob], 'test_contract.pdf', { type: 'application/pdf' }));

            console.log('准备发送请求到:', fullUrl);
            console.log('使用测试文件: test_contract.pdf');

            // 先测试服务器连通性
            try {
                const testResponse = await fetch(apiBaseUrl + '/', {
                    method: 'GET',
                    mode: 'cors'
                });
                console.log('服务器连通性测试:', testResponse.status);
            } catch (testError) {
                console.error('服务器连接失败:', testError);
                throw new Error('无法连接到API服务器，请确保服务器正在运行');
            }

            // 调用API
            const response = await fetch(fullUrl, {
                method: 'POST',
                body: formData,
                mode: 'cors', // 显式设置CORS模式
                credentials: 'same-origin' // 添加凭据设置
                // 注意：不要设置Content-Type，让浏览器自动设置multipart/form-data
            });

            console.log('响应状态:', response.status, response.statusText);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('API错误响应:', errorText);
                let errorData;
                try {
                    errorData = JSON.parse(errorText);
                } catch (e) {
                    errorData = { detail: errorText };
                }
                throw new Error(errorData.detail || `HTTP错误: ${response.status}`);
            }

            const result = await response.json();
            console.log('API成功响应:', result);

            if (result.success) {
                // 上传成功，保存文档信息
                const documentData = {
                    documentId: result.data.document_id,
                    filename: result.data.filename,
                    summary: result.data.summary,
                    uploadTime: new Date().toISOString()
                };

                // 保存到状态和历史记录
                this.state.currentDocumentId = documentData.documentId;
                this.state.uploadHistory.push(documentData);

                // 保存到本地存储
                const storageKey = (typeof CONFIG !== 'undefined' && CONFIG.storage?.uploadHistory)
                    ? CONFIG.storage.uploadHistory
                    : 'insurance_assistant_uploads';
                localStorage.setItem(storageKey, JSON.stringify(this.state.uploadHistory));

                console.log('文档上传成功:', documentData);
                alert(`文件 "${result.data.filename}" 上传成功！\n摘要: ${result.data.summary}`);

                // 添加历史对话记录（像点击提问按钮一样），使用真实文件名
                this.addSimpleHistoryRecord(result.data.filename);

                // 切换到对话页面
                this.showChatPage(documentData);
                this.resetUploadState();

            } else {
                throw new Error('API返回失败状态');
            }

        } catch (error) {
            console.error('文件上传失败:', error);
            alert(`文件上传失败: ${error.message}`);
        } finally {
            // 恢复按钮状态
            if (uploadBtn) {
                uploadBtn.classList.remove('loading');
                uploadBtn.textContent = '确认上传';
                uploadBtn.disabled = false;
            }
        }
    }

    /**
     * 重置上传状态
     */
    resetUploadState() {
        const uploadPlaceholder = document.getElementById('uploadPlaceholder');
        const filePreview = document.getElementById('filePreview');

        // 重置UI状态
        if (filePreview) filePreview.style.display = 'none';
        if (uploadPlaceholder) uploadPlaceholder.style.display = 'block';

        // 清除文件状态
        this.state.uploadedFile = null;
        if (this.elements.fileInput) {
            this.elements.fileInput.value = '';
        }

        // 恢复选择文件按钮
        this.updateSelectFileButton(false);

        console.log('上传状态已重置');
    }

    /**
     * 设置拖拽上传
     */
    setupDragAndDrop() {
        const uploadArea = this.elements.uploadArea;
        if (!uploadArea) return;

        // 阻止默认拖拽行为
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        // 拖拽进入
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.add('drag-over');
            });
        });

        // 拖拽离开
        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.remove('drag-over');
            });
        });

        // 文件放置
        uploadArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleDroppedFile(files[0]);
            }
        });

        console.log('拖拽上传功能已设置');
    }

    /**
     * 处理拖拽放置的文件
     * @param {File} file 
     */
    handleDroppedFile(file) {
        if (!this.validateFile(file)) {
            return;
        }

        this.state.uploadedFile = file;

        if (this.elements.uploadPlaceholder) {
            this.elements.uploadPlaceholder.textContent = `已选择文件: ${file.name}`;
        }

        console.log('拖拽文件已选择:', file.name);
    }

    /**
     * 格式化文件大小
     * @param {number} bytes 
     * @returns {string}
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * 移除选中的文件
     */
    removeSelectedFile() {
        const uploadPlaceholder = document.getElementById('uploadPlaceholder');
        const filePreview = document.getElementById('filePreview');

        // 隐藏文件预览，显示上传占位符
        if (filePreview) filePreview.style.display = 'none';
        if (uploadPlaceholder) uploadPlaceholder.style.display = 'block';

        // 清除文件状态
        this.state.uploadedFile = null;
        if (this.elements.fileInput) {
            this.elements.fileInput.value = '';
        }

        // 恢复选择文件按钮
        this.updateSelectFileButton(false);

        console.log('文件已移除');
    }

    /**
     * 简单添加历史记录（点击提问按钮时）
     * @param {string} fileName - 文件名，默认为通用名称
     */
    addSimpleHistoryRecord(fileName = 'XX公司（2025）重大疾病保险合同') {
        if (!this.elements.historyContent) {
            console.error('历史对话区域元素未找到');
            return;
        }

        // 如果是第一条记录，清除占位符
        const placeholder = this.elements.historyContent.querySelector('.placeholder');
        if (placeholder) {
            placeholder.remove();
        }

        // 创建历史记录元素
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        historyItem.innerHTML = `
            <div class="history-file-info">
                <div class="history-file-name">${fileName}</div>
            </div>
            <button class="history-menu-btn" title="更多选项">⋯</button>
            <div class="history-menu" style="display: none;">
                <div class="history-menu-item" data-action="rename">
                    <img src="https://api.iconify.design/tabler:edit.svg?color=%23666" alt="rename" />
                    重命名
                </div>
                <div class="history-menu-item" data-action="delete">
                    <img src="https://api.iconify.design/tabler:trash.svg?color=%23ff3b30" alt="delete" />
                    删除
                </div>
            </div>
        `;

        // 添加点击事件
        historyItem.addEventListener('click', (e) => {
            // 如果点击的是菜单按钮或菜单项，不触发记录点击事件
            if (e.target.classList.contains('history-menu-btn') ||
                e.target.closest('.history-menu') ||
                e.target.closest('.history-menu-item')) {
                return;
            }

            const recordName = historyItem.querySelector('.history-file-name').textContent;
            console.log('点击了历史记录:', recordName);
            this.showChatConversation(recordName);
        });

        // 插入到历史内容区域的顶部
        this.elements.historyContent.insertBefore(historyItem, this.elements.historyContent.firstChild);

        // 添加菜单功能
        this.setupHistoryItemMenu(historyItem);

        console.log('已添加简单历史记录');
    }

    /**
     * 设置历史记录项的菜单功能
     * @param {HTMLElement} historyItem 
     */
    setupHistoryItemMenu(historyItem) {
        const menuBtn = historyItem.querySelector('.history-menu-btn');
        const menu = historyItem.querySelector('.history-menu');
        const menuItems = historyItem.querySelectorAll('.history-menu-item');

        if (!menuBtn || !menu) return;

        // 菜单按钮点击事件
        menuBtn.addEventListener('click', (e) => {
            e.stopPropagation();

            // 关闭其他所有打开的菜单
            document.querySelectorAll('.history-menu').forEach(otherMenu => {
                if (otherMenu !== menu) {
                    otherMenu.style.display = 'none';
                }
            });

            // 切换当前菜单显示状态
            menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
        });

        // 菜单项点击事件
        menuItems.forEach(menuItem => {
            menuItem.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = menuItem.dataset.action;
                const recordName = historyItem.querySelector('.history-file-name').textContent;

                // 隐藏菜单
                menu.style.display = 'none';

                // 执行相应操作
                if (action === 'rename') {
                    this.renameHistoryRecord(historyItem, recordName);
                } else if (action === 'delete') {
                    this.deleteHistoryRecord(historyItem, recordName);
                }
            });
        });

        // 点击文档其他地方关闭菜单
        document.addEventListener('click', (e) => {
            if (!historyItem.contains(e.target)) {
                menu.style.display = 'none';
            }
        });
    }

    /**
     * 重命名历史记录
     * @param {HTMLElement} historyItem 
     * @param {string} currentName 
     */
    renameHistoryRecord(historyItem, currentName) {
        const fileNameElement = historyItem.querySelector('.history-file-name');

        // 创建输入框
        const input = document.createElement('input');
        input.type = 'text';
        input.value = currentName;
        input.className = 'history-rename-input';

        // 替换文本为输入框
        fileNameElement.style.display = 'none';
        fileNameElement.parentNode.insertBefore(input, fileNameElement.nextSibling);

        // 选中文本并聚焦
        input.select();
        input.focus();

        // 处理完成重命名
        const finishRename = () => {
            const newName = input.value.trim();
            if (newName && newName !== currentName) {
                fileNameElement.textContent = newName;
                console.log('历史记录已重命名:', currentName, '->', newName);
            }

            // 恢复显示
            input.remove();
            fileNameElement.style.display = 'block';
        };

        // 处理取消重命名
        const cancelRename = () => {
            input.remove();
            fileNameElement.style.display = 'block';
        };

        // 绑定事件
        input.addEventListener('blur', finishRename);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                finishRename();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                cancelRename();
            }
        });
    }

    /**
     * 删除历史记录
     * @param {HTMLElement} historyItem 
     * @param {string} recordName 
     */
    deleteHistoryRecord(historyItem, recordName) {
        if (confirm(`确定要删除历史记录"${recordName}"吗？`)) {
            historyItem.remove();
            console.log('历史记录已删除:', recordName);

            // 如果没有历史记录了，显示占位符
            if (this.elements.historyContent.children.length === 0) {
                const placeholder = document.createElement('div');
                placeholder.className = 'placeholder';
                placeholder.textContent = '暂无历史对话';
                this.elements.historyContent.appendChild(placeholder);
            }
        }
    }
}

/**
 * 应用程序入口
 */
console.log('JavaScript文件开始加载...');

// 创建应用实例
window.insuranceApp = new InsuranceAssistant();

// 全局错误处理
window.addEventListener('error', (e) => {
    console.error('应用程序错误:', e.error);
});

// 页面卸载前的清理
window.addEventListener('beforeunload', () => {
    console.log('应用程序正在卸载...');
});

console.log('JavaScript文件加载完成');
