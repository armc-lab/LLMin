/**
 * 保险合同解释助手 - 简化版主JavaScript文件
 * 确保基础功能正常工作
 */

console.log('JavaScript文件开始加载...');

// 等待DOM完全加载
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM加载完成，开始初始化...');
    
    // 获取所有需要的DOM元素
    const elements = {
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
    
    // 验证关键元素是否存在
    console.log('关键元素检查:');
    console.log('uploadBtn:', elements.uploadBtn);
    console.log('welcomeArea:', elements.welcomeArea);
    console.log('uploadPage:', elements.uploadPage);
    console.log('backToChat:', elements.backToChat);
    
    // 状态管理
    let currentPage = 'welcome';
    let collapsed = false;
    
    // 页面切换函数
    function showUploadPage() {
        console.log('准备切换到上传页面...');
        
        if (elements.welcomeArea) {
            elements.welcomeArea.style.display = 'none';
            console.log('隐藏欢迎区域');
        }
        
        if (elements.chatInputBar) {
            elements.chatInputBar.style.display = 'none';
            console.log('隐藏聊天输入框');
        }
        
        if (elements.uploadPage) {
            elements.uploadPage.style.display = 'flex';
            console.log('显示上传页面');
        }
        
        currentPage = 'upload';
        console.log('页面切换完成: upload');
    }
    
    function showChatPage() {
        console.log('准备切换到聊天页面...');
        
        if (elements.welcomeArea) {
            elements.welcomeArea.style.display = 'flex';
            console.log('显示欢迎区域');
        }
        
        if (elements.chatInputBar) {
            elements.chatInputBar.style.display = 'flex';
            console.log('显示聊天输入框');
        }
        
        if (elements.uploadPage) {
            elements.uploadPage.style.display = 'none';
            console.log('隐藏上传页面');
        }
        
        currentPage = 'welcome';
        console.log('页面切换完成: welcome');
    }
    
    // 侧边栏收起/展开
    function toggleSidebar() {
        collapsed = !collapsed;
        
        if (elements.aside) {
            elements.aside.style.width = collapsed ? '60px' : '260px';
        }
        
        // 隐藏或显示文字内容
        const hideElements = document.querySelectorAll('.menu-btn, .section-title, .placeholder, .profile');
        hideElements.forEach(el => {
            el.style.display = collapsed ? 'none' : '';
        });
        
        if (elements.collapseToggle) {
            elements.collapseToggle.textContent = collapsed ? '»' : '«';
        }
        
        console.log(`侧边栏${collapsed ? '收起' : '展开'}`);
    }
    
    // 自适应输入框高度
    function autoResizeTextarea() {
        if (elements.userInput) {
            elements.userInput.style.height = 'auto';
            elements.userInput.style.height = Math.min(elements.userInput.scrollHeight, 200) + 'px';
        }
    }
    
    // 发送消息
    function sendMessage() {
        const text = elements.userInput?.value?.trim();
        if (!text) return;
        
        console.log('[发送消息]', text);
        
        // 清空输入框
        if (elements.userInput) {
            elements.userInput.value = '';
            autoResizeTextarea();
        }
    }
    
    // 处理文件选择
    function handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        console.log('文件已选择:', file.name);
        
        if (elements.uploadPlaceholder) {
            elements.uploadPlaceholder.textContent = `已选择文件: ${file.name}`;
        }
    }
    
    // 确认上传
    function confirmUpload() {
        const fileInput = elements.fileInput;
        if (fileInput && fileInput.files.length > 0) {
            console.log('开始上传文件:', fileInput.files[0].name);
            alert(`文件 "${fileInput.files[0].name}" 上传成功！`);
        } else {
            alert('请先选择要上传的文件');
        }
    }
    
    // 绑定事件监听器
    console.log('开始绑定事件...');
    
    // 侧边栏收起/展开
    if (elements.collapseToggle) {
        elements.collapseToggle.addEventListener('click', toggleSidebar);
        console.log('收起按钮事件已绑定');
    }
    
    // 上传合同文档按钮
    if (elements.uploadBtn) {
        elements.uploadBtn.addEventListener('click', function() {
            console.log('上传按钮被点击');
            showUploadPage();
        });
        console.log('上传按钮事件已绑定');
    } else {
        console.error('上传按钮未找到！');
    }
    
    // 提问按钮
    if (elements.askBtn) {
        elements.askBtn.addEventListener('click', function() {
            if (elements.userInput) {
                elements.userInput.focus();
            }
        });
        console.log('提问按钮事件已绑定');
    }
    
    // 存证按钮
    if (elements.evidenceBtn) {
        elements.evidenceBtn.addEventListener('click', function() {
            alert('TODO: 跳转到存证记录页或弹窗');
        });
        console.log('存证按钮事件已绑定');
    }
    
    // 发送按钮
    if (elements.sendBtn) {
        elements.sendBtn.addEventListener('click', sendMessage);
        console.log('发送按钮事件已绑定');
    }
    
    // 输入框键盘事件
    if (elements.userInput) {
        elements.userInput.addEventListener('input', autoResizeTextarea);
        elements.userInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        console.log('输入框事件已绑定');
    }
    
    // 返回对话按钮
    if (elements.backToChat) {
        elements.backToChat.addEventListener('click', function() {
            console.log('返回对话按钮被点击');
            showChatPage();
        });
        console.log('返回对话按钮事件已绑定');
    } else {
        console.error('返回对话按钮未找到！');
    }
    
    // 上传区域点击
    if (elements.uploadArea) {
        elements.uploadArea.addEventListener('click', function() {
            if (elements.fileInput) {
                elements.fileInput.click();
            }
        });
        console.log('上传区域事件已绑定');
    }
    
    // 文件选择
    if (elements.fileInput) {
        elements.fileInput.addEventListener('change', handleFileSelect);
        console.log('文件选择事件已绑定');
    }
    
    // 确认上传按钮
    if (elements.confirmUpload) {
        elements.confirmUpload.addEventListener('click', confirmUpload);
        console.log('确认上传按钮事件已绑定');
    }
    
    // 添加文件按钮
    if (elements.addFileBtn) {
        elements.addFileBtn.addEventListener('click', function() {
            alert('TODO: 添加图片 / 附件等');
        });
        console.log('添加文件按钮事件已绑定');
    }
    
    console.log('所有事件绑定完成！');
    console.log('应用初始化完成！');
});

console.log('JavaScript文件加载完成');
