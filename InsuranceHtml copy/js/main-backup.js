/**
 * =================================================================
 * 保险合同解释助手 - 优化版主JavaScript文件
 * 版本: 1.1.0
 * 确保功能稳定可靠
 * =================================================================
 */

'use strict';

/**
 * 应用程序主类 - 优化版
 */
class InsuranceAssistant {
    constructor() {
        this.elements = {};
        this.state = {
            collapsed: false,
            currentPage: 'welcome',
            uploadedFile: null
        };

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

            // 主内容区元素
            welcomeArea: document.getElementById('welcomeArea'),
            uploadPage: document.getElementById('uploadPage'),
            chatPage: document.getElementById('chatPage'),

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
            reselectFileBtn: document.getElementById('reselectFileBtn'),
            uploadFileBtn: document.getElementById('uploadFileBtn'),
            uploadPlaceholder: document.querySelector('.upload-main-text')
        };

        console.log('DOM元素缓存完成');
    }

    /**
     * 验证关键元素是否存在
     */
    validateElements() {
        const criticalElements = ['uploadBtn', 'welcomeArea', 'uploadPage', 'chatPage', 'backToChat'];
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

        // Logo点击事件 - 回到首页
        this.bindEvent('logoIcon', 'click', () => {
            console.log('Logo被点击，回到首页');
            this.showHomePage();
        });

        // 功能按钮
        this.bindEvent('uploadBtn', 'click', () => {
            console.log('上传按钮被点击');
            this.showUploadPage();
        });

        this.bindEvent('askBtn', 'click', () => {
            console.log('提问按钮被点击');
            this.showChatPage();
        });
        this.bindEvent('evidenceBtn', 'click', () => this.showEvidencePage());

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

        this.bindEvent('uploadArea', 'click', (e) => this.handleUploadAreaClick(e));
        this.bindEvent('selectFileBtn', 'click', () => this.triggerFileSelect());
        this.bindEvent('reselectFileBtn', 'click', () => this.triggerFileSelect());
        this.bindEvent('uploadFileBtn', 'click', () => this.confirmUpload());
        this.bindEvent('fileInput', 'change', (e) => this.handleFileSelect(e));

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
            this.elements.aside.classList.toggle('collapsed', this.state.collapsed);
        }

        // 隐藏或显示非按钮的文字内容
        const hideElements = document.querySelectorAll('.section-title, .placeholder, .profile');
        hideElements.forEach(el => {
            el.style.display = this.state.collapsed ? 'none' : '';
        });

        // 调整按钮样式
        const menuButtons = document.querySelectorAll('.menu-btn');
        menuButtons.forEach(btn => {
            if (this.state.collapsed) {
                btn.classList.add('collapsed');
            } else {
                btn.classList.remove('collapsed');
            }
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
    showChatPage() {
        console.log('准备切换到聊天页面...');
        this.switchPage('chat');
        // 延迟一下聚焦输入框，确保DOM已经显示
        setTimeout(() => {
            this.focusInput();
        }, 100);
        console.log('已切换到聊天页面');
    }

    /**
     * 显示首页（欢迎页面但不显示输入框）
     */
    showHomePage() {
        console.log('准备切换到首页...');
        this.switchPage('home');
        console.log('已切换到首页');
    }

    /**
     * 页面切换核心方法
     * @param {string} page - 页面类型: 'welcome' | 'upload' | 'home'
     */
    switchPage(page) {
        this.state.currentPage = page;

        switch (page) {
            case 'upload':
                this.hideElement(this.elements.welcomeArea, '欢迎区域');
                this.hideElement(this.elements.chatInputBar, '聊天输入框');
                this.hideElement(this.elements.chatPage, '聊天页面');
                this.showElement(this.elements.uploadPage, '上传页面');
                break;

            case 'chat':
                this.hideElement(this.elements.welcomeArea, '欢迎区域');
                this.hideElement(this.elements.uploadPage, '上传页面');
                this.showElement(this.elements.chatPage, '聊天页面');
                this.showElement(this.elements.chatInputBar, '聊天输入框');
                break;

            case 'home':
                this.showElement(this.elements.welcomeArea, '欢迎区域');
                this.hideElement(this.elements.chatInputBar, '聊天输入框');
                this.hideElement(this.elements.uploadPage, '上传页面');
                this.hideElement(this.elements.chatPage, '聊天页面');
                break;

            case 'welcome':
            default:
                this.showElement(this.elements.welcomeArea, '欢迎区域');
                this.showElement(this.elements.chatInputBar, '聊天输入框');
                this.hideElement(this.elements.uploadPage, '上传页面');
                this.hideElement(this.elements.chatPage, '聊天页面');
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
     * 发送消息
     */
    sendMessage() {
        const text = this.elements.userInput?.value?.trim();
        if (!text) return;

        console.log('[发送消息]', text);

        // TODO: 这里可以添加实际的API调用逻辑
        this.displayMessage('user', text);

        // 清空输入框
        if (this.elements.userInput) {
            this.elements.userInput.value = '';
            this.autoResizeTextarea();
        }

        // 智能AI回复
        setTimeout(() => {
            const response = this.generateAIResponse(text);
            this.displayMessage('assistant', response);
        }, 500);
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
     * 生成AI回复
     * @param {string} userMessage - 用户输入的消息
     * @returns {string} AI回复内容
     */
    generateAIResponse(userMessage) {
        const message = userMessage.toLowerCase().trim();

        // 高血压相关问题检测
        if (message.includes('高血压') && (message.includes('投保') || message.includes('保险') || message.includes('买'))) {
            return `根据保险合同第 4.2 条关于重大疾病的定义，轻度高血压并不在拒保范围内，是可以投保的。

另外，根据《中国高血压防治指南》：

• 轻度高血压：140/90 mmHg ～ 160/100 mmHg
• 中度高血压：160/100 mmHg ～ 180/110 mmHg  
• 重度高血压：180/110 mmHg 以上

为了帮你更准确地判断投保资格，能否告诉我你的年龄和目前的血压范围呢？`;
        }

        // 年龄相关回复
        if (message.includes('年龄') || /\d+岁/.test(message)) {
            return '感谢您提供年龄信息。年龄是投保的重要因素之一，不同年龄段的保费和保障范围会有所不同。请问您还有其他健康状况需要说明吗？';
        }

        // 血压数值相关回复
        if (/\d+\/\d+/.test(message) || message.includes('血压')) {
            return '根据您提供的血压信息，我会为您做详细的投保资格评估。一般来说，如果血压控制在正常范围内，投保是没有问题的。如有疑问，建议咨询专业的保险顾问。';
        }

        // 保险条款相关
        if (message.includes('条款') || message.includes('合同') || message.includes('保障')) {
            return '我可以帮您解读保险合同的各项条款。请告诉我您想了解合同的哪个具体方面，比如保障范围、免责条款、理赔流程等？';
        }

        // 理赔相关
        if (message.includes('理赔') || message.includes('报销') || message.includes('赔付')) {
            return '关于理赔流程，您需要在确诊后及时联系保险公司，准备好相关医疗证明材料。具体的理赔标准和流程在合同第6-8条中有详细说明。有什么具体的理赔问题吗？';
        }

        // 默认回复
        return '我是您的保险合同解释助手，可以帮助您理解合同条款、评估投保资格、解答保险相关问题。请告诉我您想了解什么？';
    }

    /**
     * 显示消息（优化版）
     * @param {string} sender - 发送者类型: 'user' | 'assistant'
     * @param {string} message - 消息内容
     */
    displayMessage(sender, message) {
        console.log(`[${sender}]`, message);

        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) {
            console.error('聊天消息容器未找到');
            return;
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = sender === 'user' ? 'user-message' : 'bot-message';

        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="message-content">
                    <p>${message}</p>
                </div>
                <div class="message-actions">
                    <button class="message-action-btn" title="复制">
                        <img src="https://api.iconify.design/tabler:copy.svg?color=%236b7280" alt="copy" />
                    </button>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="bot-avatar">
                    <img src="icon/robot.svg" alt="bot" />
                </div>
                <div class="bot-message-wrapper">
                    <div class="message-content">
                        <p>${message}</p>
                    </div>
                    <div class="message-actions">
                        <button class="message-action-btn" title="复制">
                            <img src="https://api.iconify.design/tabler:copy.svg?color=%236b7280" alt="copy" />
                        </button>
                        <button class="message-action-btn" title="重新生成">
                            <img src="https://api.iconify.design/tabler:refresh.svg?color=%236b7280" alt="refresh" />
                        </button>
                    </div>
                </div>
            `;
        }

        // 添加消息到容器
        chatMessages.appendChild(messageDiv);

        // 滚动到底部
        chatMessages.scrollTop = chatMessages.scrollHeight;
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
        alert('TODO: 跳转到存证记录页或弹窗');
    }

    /**
     * 处理上传区域点击事件
     * @param {Event} e 
     */
    handleUploadAreaClick(e) {
        const uploadPlaceholder = document.getElementById('uploadPlaceholder');
        const filePreview = document.getElementById('filePreview');

        // 只有在上传占位符显示时才触发文件选择
        if (uploadPlaceholder && uploadPlaceholder.style.display !== 'none') {
            this.triggerFileSelect();
        }

        // 如果点击的是文件预览区域，不做任何操作
        if (filePreview && filePreview.style.display !== 'none') {
            // 检查是否点击的是移除按钮，如果是则阻止事件冒泡
            if (e.target.id === 'fileRemove' || e.target.closest('#fileRemove')) {
                e.stopPropagation();
                return;
            }
        }
    }

    /**
     * 触发文件选择
     */
    triggerFileSelect() {
        if (this.elements.fileInput) {
            this.elements.fileInput.click();
            console.log('触发文件选择对话框');
        }
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
        const fileIcon = document.querySelector('.file-type-icon');
        const selectFileBtn = document.getElementById('selectFileBtn');

        if (!filePreview || !fileName || !fileType || !fileSize) return;

        // 恢复上传成功状态（如果之前上传过）
        this.resetUploadSuccessState();

        // 隐藏上传占位符，显示文件预览
        if (uploadPlaceholder) uploadPlaceholder.style.display = 'none';
        filePreview.style.display = 'block';

        // 更改选择文件按钮为重新选择
        if (selectFileBtn) {
            selectFileBtn.textContent = '重新选择';
        }

        // 更新文件信息
        fileName.textContent = file.name;
        fileSize.textContent = this.formatFileSize(file.size);

        // 根据文件类型设置图标和类型文本
        const fileExtension = file.name.split('.').pop().toLowerCase();
        let typeText = '文档';
        let iconSrc = 'https://api.iconify.design/vscode-icons:default-file.svg';

        switch (fileExtension) {
            case 'pdf':
                typeText = 'PDF文档';
                iconSrc = 'https://api.iconify.design/vscode-icons:file-type-pdf2.svg';
                break;
            case 'doc':
            case 'docx':
                typeText = 'Word文档';
                iconSrc = 'https://api.iconify.design/vscode-icons:file-type-word2.svg';
                break;
            case 'txt':
                typeText = 'TXT文档';
                iconSrc = 'https://api.iconify.design/vscode-icons:file-type-text.svg';
                break;
            case 'jpg':
            case 'jpeg':
            case 'png':
                typeText = '图片文件';
                iconSrc = 'https://api.iconify.design/vscode-icons:file-type-image.svg';
                break;
        }

        fileType.textContent = typeText;
        if (fileIcon) fileIcon.src = iconSrc;

        // 绑定移除文件事件
        const fileRemove = document.getElementById('fileRemove');

        if (fileRemove) {
            fileRemove.onclick = (e) => {
                e.stopPropagation(); // 阻止事件冒泡
                this.removeFile();
            };
        }
    }

    /**
     * 移除选择的文件
     */
    removeFile() {
        this.state.uploadedFile = null;
        const uploadPlaceholder = document.getElementById('uploadPlaceholder');
        const filePreview = document.getElementById('filePreview');
        const fileInput = document.getElementById('fileInput');
        const selectFileBtn = document.getElementById('selectFileBtn');

        // 重置文件输入
        if (fileInput) fileInput.value = '';

        // 显示上传占位符，隐藏文件预览
        if (uploadPlaceholder) uploadPlaceholder.style.display = 'block';
        if (filePreview) filePreview.style.display = 'none';

        // 恢复选择文件按钮文本
        if (selectFileBtn) {
            selectFileBtn.textContent = '选择文件';
        }

        // 恢复上传成功状态
        this.resetUploadSuccessState();

        console.log('文件已移除');
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
     * 确认上传（测试模式 - 不发送实际文件）
     */
    async confirmUpload() {
        if (!this.state.uploadedFile) {
            alert('请先选择要上传的文件');
            return;
        }

        console.log('开始测试上传功能，文件:', this.state.uploadedFile.name);
        console.log('文件信息:', {
            name: this.state.uploadedFile.name,
            size: this.formatFileSize(this.state.uploadedFile.size),
            type: this.state.uploadedFile.type
        });

        // 显示加载状态 - 使用框内的"点击上传"按钮
        const uploadBtn = document.getElementById('uploadFileBtn');
        if (uploadBtn) {
            uploadBtn.classList.add('loading');
            uploadBtn.textContent = '测试中...';
            uploadBtn.disabled = true;
        }

        try {
            // 发送测试请求（不包含实际文件）
            console.log('发送测试请求到API...');
            const testData = {
                action: 'test_upload',
                filename: this.state.uploadedFile.name,
                filesize: this.state.uploadedFile.size,
                filetype: this.state.uploadedFile.type
            };

            const response = await fetch('http://localhost:8001/api/v1/documents/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(testData),
                mode: 'cors',
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`测试请求失败: ${response.status} ${response.statusText}`);
            }

            const result = await response.json();
            console.log('测试请求成功，服务器响应:', result);

            // 检查是否返回成功状态
            if (result.status === 'success' || result.message?.includes('success') || result.success === true) {
                console.log('服务器返回成功状态');
                // 显示上传成功状态
                this.showUploadSuccess();

                // 2秒后自动跳转到聊天页面
                setTimeout(() => {
                    this.showChatPage();
                }, 2000);
            } else {
                console.log('服务器返回其他状态:', result);
                // 显示服务器返回的信息
                alert(`服务器响应: ${JSON.stringify(result)}`);

                // 恢复按钮状态
                if (uploadBtn) {
                    uploadBtn.classList.remove('loading');
                    uploadBtn.textContent = '点击上传';
                    uploadBtn.disabled = false;
                }
            }

        } catch (error) {
            console.error('测试请求失败:', error);

            // 恢复按钮状态
            if (uploadBtn) {
                uploadBtn.classList.remove('loading');
                uploadBtn.textContent = '点击上传';
                uploadBtn.disabled = false;
            }

            // 显示错误信息
            alert(`测试请求失败: ${error.message}`);
        }
    }

    /**
     * 显示上传成功状态
     */
    showUploadSuccess() {
        const filePreviewHeader = document.querySelector('.file-preview-header');
        const uploadFileBtn = document.getElementById('uploadFileBtn');

        // 更改标题为"上传成功！"并设置绿色
        if (filePreviewHeader) {
            filePreviewHeader.textContent = '上传成功！';
            filePreviewHeader.style.color = '#22c55e';
        }

        // 隐藏"点击上传"按钮
        if (uploadFileBtn) {
            uploadFileBtn.style.display = 'none';
        }
    }

    /**
     * 重置上传成功状态
     */
    resetUploadSuccessState() {
        const filePreviewHeader = document.querySelector('.file-preview-header');
        const uploadFileBtn = document.getElementById('uploadFileBtn');

        // 恢复标题为"已选择的文件"并恢复原始颜色
        if (filePreviewHeader) {
            filePreviewHeader.textContent = '已选择的文件';
            filePreviewHeader.style.color = '';
        }

        // 显示"点击上传"按钮
        if (uploadFileBtn) {
            uploadFileBtn.style.display = 'inline-block';
        }
    }

    /**
     * 重置上传状态
     */
    resetUploadState() {
        this.state.uploadedFile = null;

        if (this.elements.fileInput) {
            this.elements.fileInput.value = '';
        }

        if (this.elements.uploadPlaceholder) {
            this.elements.uploadPlaceholder.textContent = '点击或拖拽文件到此处上传';
        }

        // 隐藏确认上传按钮
        if (this.elements.confirmUpload) {
            this.elements.confirmUpload.style.display = 'none';
        }

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
