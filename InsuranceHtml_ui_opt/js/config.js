/**
 * =================================================================
 * 保险合同解释助手 - 配置文件
 * =================================================================
 */

const CONFIG = {
    // API 配置
    api: {
        // 优先使用同源路径，便于通过本地代理无缝连接后端。
        // 可用 window.__API_BASEURL__ 显式覆盖，例如：
        // window.__API_BASEURL__ = 'http://10.201.87.224:8001'
        baseUrl: (typeof window !== 'undefined' && window.__API_BASEURL__)
            ? window.__API_BASEURL__
            : ((typeof window !== 'undefined' && window.location && /^https?:$/i.test(window.location.protocol))
                ? ''
                : 'http://127.0.0.1:8001'),
        timeout: 90000, // 90秒，因为AI处理需要时间
        retryCount: 3,
        endpoints: {
            documentAnalyze: '/api/v1/documents/analyze',
            chatCompletion: '/api/v1/chat/completions',
            archive: '/api/v1/archive/generate-and-submit'
        }
    },

    // 文件上传配置
    upload: {
        maxSize: 10 * 1024 * 1024, // 10MB
        allowedTypes: [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'image/jpeg',
            'image/png',
            'image/jpg'
        ],
        allowedExtensions: ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
    },

    // UI 配置
    ui: {
        animationDuration: 300,
        debounceDelay: 300,
        maxMessageLength: 1000,
        autoSaveInterval: 5000
    },

    // 本地存储键名
    storage: {
        userPreferences: 'insurance_assistant_preferences',
        chatHistory: 'insurance_assistant_history',
        uploadHistory: 'insurance_assistant_uploads'
    },

    // 错误消息
    messages: {
        error: {
            fileTooBig: '文件大小不能超过10MB',
            fileTypeNotSupported: '不支持的文件格式，请上传PDF、Word或图片文件',
            uploadFailed: '文件上传失败，请重试',
            networkError: '网络连接错误，请检查网络设置',
            serverError: '服务器错误，请稍后重试'
        },
        success: {
            fileUploaded: '文件上传成功',
            messageSent: '消息发送成功'
        },
        info: {
            uploading: '正在上传文件...',
            processing: '正在处理你的请求...'
        }
    }
};

// 导出配置
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
} else if (typeof window !== 'undefined') {
    window.CONFIG = CONFIG;
}
