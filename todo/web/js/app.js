// 全局配置
const API_BASE_URL = 'http://localhost:8000'; // 假设后端运行在8000端口

// 全局状态
let currentPatientId = localStorage.getItem('patient_id') || null;
let currentPatientName = localStorage.getItem('patient_name') || null;

// 工具函数
class Utils {
    // 显示通知
    static showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
            <span>${message}</span>
            <button class="notification-close">&times;</button>
        `;

        document.body.appendChild(notification);

        // 关闭按钮事件
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            notification.remove();
        });

        // 自动关闭
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, duration);
        }
    }

    // 显示加载动画
    static showLoading(show = true) {
        let overlay = document.getElementById('loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loading-overlay';
            overlay.className = 'loading-overlay';
            overlay.innerHTML = '<div class="loading-spinner"></div>';
            document.body.appendChild(overlay);
        }

        if (show) {
            overlay.classList.add('active');
        } else {
            overlay.classList.remove('active');
        }
    }

    // 格式化时间
    static formatTime(date) {
        if (!date) return '未知';
        if (typeof date === 'string') {
            date = new Date(date);
        }
        return date.toLocaleString('zh-CN');
    }

    // 防抖函数
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // 节流函数
    static throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

// API服务
class APIService {
    static async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        try {
            const response = await fetch(url, {
                ...defaultOptions,
                ...options,
                headers: {
                    ...defaultOptions.headers,
                    ...options.headers,
                },
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API请求失败:', error);
            Utils.showNotification(`请求失败: ${error.message}`, 'error');
            throw error;
        }
    }

    // 聊天接口
    static async sendChatMessage(message, patientId) {
        return this.request('/chat', {
            method: 'POST',
            body: JSON.stringify({
                message,
                patient_id: patientId,
            }),
        });
    }

    // 获取待审批列表（医生端）
    static async getPendingApprovals(doctorId) {
        return this.request(`/pending?doctor_id=${doctorId}`);
    }

    // 审批操作
    static async approvePrescription(approvalId, action, doctorId, reason = '') {
        return this.request('/approve', {
            method: 'POST',
            body: JSON.stringify({
                approval_id: approvalId,
                action,
                doctor_id: doctorId,
                reject_reason: reason,
            }),
        });
    }

    // 获取处方详情
    static async getPrescription(prescriptionId) {
        return this.request(`/prescription/${prescriptionId}`);
    }

    // 获取用药历史
    static async getPatientHistory(patientName) {
        return this.request(`/history?patient_name=${encodeURIComponent(patientName)}`);
    }

    // 获取药品列表（管理员）
    static async getDrugs(page = 1, limit = 20) {
        return this.request(`/admin/drugs?page=${page}&limit=${limit}`);
    }

    // 添加药品（管理员）
    static async addDrug(drugData) {
        return this.request('/admin/drugs', {
            method: 'POST',
            body: JSON.stringify(drugData),
        });
    }

    // 更新药品（管理员）
    static async updateDrug(drugId, drugData) {
        return this.request(`/admin/drugs/${drugId}`, {
            method: 'PUT',
            body: JSON.stringify(drugData),
        });
    }

    // 删除药品（管理员）
    static async deleteDrug(drugId) {
        return this.request(`/admin/drugs/${drugId}`, {
            method: 'DELETE',
        });
    }

    // 获取报表（管理员）
    static async getReport(startDate, endDate) {
        return this.request(`/admin/report?start=${startDate}&end=${endDate}`);
    }

    // 获取采购建议（管理员）
    static async getPurchaseSuggestions() {
        return this.request('/admin/purchase-suggestions');
    }

    // 药房：确认取药
    static async confirmDispense(pickupCode) {
        return this.request(`/pharmacy/dispense/${pickupCode}`, {
            method: 'POST',
        });
    }

    // 药房：获取待取药列表
    static async getPendingDispenses() {
        return this.request('/pharmacy/pending');
    }
}

// 模态框管理
class ModalManager {
    static openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    static closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    static closeAllModals() {
        const modals = document.querySelectorAll('.modal.active');
        modals.forEach(modal => {
            modal.classList.remove('active');
        });
        document.body.style.overflow = '';
    }

    static initModalCloseListeners() {
        // 点击关闭按钮关闭模态框
        document.querySelectorAll('.modal-close').forEach(button => {
            button.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                if (modal) {
                    this.closeModal(modal.id);
                }
            });
        });

        // 点击模态框背景关闭
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });

        // ESC键关闭所有模态框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    }
}

// 会话管理
class SessionManager {
    static setPatient(patientId, patientName) {
        currentPatientId = patientId;
        currentPatientName = patientName;
        localStorage.setItem('patient_id', patientId);
        localStorage.setItem('patient_name', patientName);
        Utils.showNotification(`患者已切换为: ${patientName} (${patientId})`, 'success');
    }

    static getPatient() {
        return {
            id: currentPatientId,
            name: currentPatientName,
        };
    }

    static clearPatient() {
        currentPatientId = null;
        currentPatientName = null;
        localStorage.removeItem('patient_id');
        localStorage.removeItem('patient_name');
    }

    static isPatientSet() {
        return !!currentPatientId && !!currentPatientName;
    }
}

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化模态框关闭监听
    ModalManager.initModalCloseListeners();

    // 显示当前患者信息
    const patient = SessionManager.getPatient();
    if (patient.id && patient.name) {
        const patientIdElements = document.querySelectorAll('#patient-id');
        patientIdElements.forEach(el => {
            if (el) el.textContent = patient.id;
        });
    }

    // 退出按钮
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            if (confirm('确定要退出吗？')) {
                SessionManager.clearPatient();
                window.location.href = 'index.html'; // 假设有登录页
            }
        });
    }

    // 全局错误处理
    window.addEventListener('error', (event) => {
        console.error('全局错误:', event.error);
        Utils.showNotification('发生了一个错误，请刷新页面重试', 'error');
    });

    // 未处理的Promise rejection
    window.addEventListener('unhandledrejection', (event) => {
        console.error('未处理的Promise rejection:', event.reason);
        Utils.showNotification('请求失败，请检查网络连接', 'error');
    });
});

// 导出全局对象
window.App = {
    Utils,
    APIService,
    ModalManager,
    SessionManager,
    API_BASE_URL,
};