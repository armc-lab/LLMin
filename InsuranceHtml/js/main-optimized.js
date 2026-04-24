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

            // 主内容区元素
            welcomeArea: document.getElementById('welcomeArea'),
            uploadPage: document.getElementById('uploadPage'),

            // 输入框相关
            chatInputBar: document.querySelector('.chat-input-bar'),
            userInput: document.getElementById('userInput'),
            sendBtn: document.getElementById('sendBtn'),
            addFileBtn: document.getElementById('addFileBtn'),

            // 上传页面元素
            backToChat: document.getElementById('backToChat'),
            uploadArea: document.querySelector('.upload-area'),
            fileInput: document.getElementById('fileInput'),
            confirmUpload: document.getElementById('confirmUpload'),
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

        this.bindEvent('askBtn', 'click', () => this.focusInput());
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

        this.bindEvent('uploadArea', 'click', () => this.triggerFileSelect());
        this.bindEvent('fileInput', 'change', (e) => this.handleFileSelect(e));
        this.bindEvent('confirmUpload', 'click', () => this.confirmUpload());

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
    showChatPage() {
        console.log('准备切换到聊天页面...');
        this.switchPage('welcome');
        console.log('已切换到聊天页面');
    }

    /**
     * 页面切换核心方法
     * @param {string} page - 页面类型: 'welcome' | 'upload'
     */
    switchPage(page) {
        this.state.currentPage = page;

        switch (page) {
            case 'upload':
                this.hideElement(this.elements.welcomeArea, '欢迎区域');
                this.hideElement(this.elements.chatInputBar, '聊天输入框');
                this.showElement(this.elements.uploadPage, '上传页面');
                break;

            case 'welcome':
            default:
                this.showElement(this.elements.welcomeArea, '欢迎区域');
                this.showElement(this.elements.chatInputBar, '聊天输入框');
                this.hideElement(this.elements.uploadPage, '上传页面');
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

        // 模拟AI回复
        setTimeout(() => {
            this.displayMessage('assistant', '我已收到你的消息，正在处理中...');
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
     * 显示消息（占位方法）
     * @param {string} sender - 发送者类型: 'user' | 'assistant'
     * @param {string} message - 消息内容
     */
    displayMessage(sender, message) {
        console.log(`[${sender}]`, message);
        // TODO: 实现消息显示逻辑
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

        // 更新UI显示
        if (this.elements.uploadPlaceholder) {
            this.elements.uploadPlaceholder.textContent = `已选择文件: ${file.name}`;
        }

        console.log('文件已选择:', file.name, this.formatFileSize(file.size), file.type);
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
    confirmUpload() {
        if (!this.state.uploadedFile) {
            alert('请先选择要上传的文件');
            return;
        }

        console.log('开始上传文件:', this.state.uploadedFile.name);

        // 显示加载状态
        const uploadBtn = this.elements.confirmUpload;
        if (uploadBtn) {
            uploadBtn.classList.add('loading');
            uploadBtn.textContent = '上传中...';
            uploadBtn.disabled = true;
        }

        // 模拟上传过程
        setTimeout(() => {
            if (uploadBtn) {
                uploadBtn.classList.remove('loading');
                uploadBtn.textContent = '确认上传';
                uploadBtn.disabled = false;
            }

            alert(`文件 "${this.state.uploadedFile.name}" 上传成功！`);
            this.resetUploadState();
        }, 2000);
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
