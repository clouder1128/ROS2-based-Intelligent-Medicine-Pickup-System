// 全局配置
const API_BASE_URL = 'http://localhost:8001'; // 后端运行在8001端口

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

    // 创建审批（患者端）- 对应后端的 /api/approvals
    static async createApproval(data) {
        return this.request('/api/approvals', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    // 获取待审批列表（医生端）- 对应后端的 /api/approvals/pending
    static async getPendingApprovals() {
        return this.request('/api/approvals/pending');
    }

    // 获取审批详情 - 对应后端的 /api/approvals/{id}
    static async getApprovalDetail(approvalId) {
        return this.request(`/api/approvals/${approvalId}`);
    }

    // 获取审批状态 - 模拟接口（后端可能未实现单独的状态接口）
    static async getApprovalStatus(approvalId) {
        // 尝试调用详情接口获取状态
        try {
            const detail = await this.getApprovalDetail(approvalId);
            if (detail && detail.approval) {
                return detail.approval;
            }
        } catch (error) {
            // 如果详情接口失败，返回模拟数据
            console.log('使用模拟审批状态数据');
        }

        // 模拟数据
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({
                    approval_id: approvalId,
                    status: Math.random() > 0.3 ? 'pending' : (Math.random() > 0.5 ? 'approved' : 'rejected'),
                    doctor_id: 'dr_wang',
                    created_at: new Date().toISOString(),
                    approved_at: null,
                    reject_reason: '',
                });
            }, 500);
        });
    }

    // 审批操作 - 对应后端的 /api/approvals/{id}/approve 或 /api/approvals/{id}/reject
    static async approvePrescription(approvalId, action, doctorId, reason = '') {
        const endpoint = action === 'approve' ? 'approve' : 'reject';
        const body = { doctor_id: doctorId };
        if (action === 'reject' && reason) {
            body.reason = reason;
        }
        if (action === 'approve' && reason) {
            body.notes = reason;
        }
        return this.request(`/api/approvals/${approvalId}/${endpoint}`, {
            method: 'POST',
            body: JSON.stringify(body),
        });
    }

    // 获取订单列表 - 对应后端的 /api/orders
    static async getOrders() {
        return this.request('/api/orders');
    }

    // 获取药品列表 - 对应后端的 /api/drugs
    static async getDrugs() {
        return this.request('/api/drugs');
    }

    // 获取库存信息 - 对应后端的 /api/inventory
    static async getInventory() {
        return this.request('/api/inventory');
    }

    // 健康检查 - 对应后端的 /api/health
    static async checkHealth() {
        return this.request('/api/health');
    }

    // 创建订单 - 对应后端的 /api/order
    static async createOrder(orderData) {
        return this.request('/api/order', {
            method: 'POST',
            body: JSON.stringify(orderData),
        });
    }

    // 单个取药 - 对应后端的 /api/pickup
    static async pickupDrug(drugId, quantity) {
        return this.request('/api/pickup', {
            method: 'POST',
            body: JSON.stringify({ id: drugId, num: quantity }),
        });
    }

    // 配药 - 对应后端的 /api/dispense
    static async dispensePrescription(prescriptionId, patientName, drugs) {
        return this.request('/api/dispense', {
            method: 'POST',
            body: JSON.stringify({
                prescription_id: prescriptionId,
                patient_name: patientName,
                drugs: drugs
            }),
        });
    }

    // 确认患者取药 - 模拟接口（后端可能未实现）
    static async confirmPatientPickup(orderId) {
        // 模拟接口，实际应该调用ROS2状态接口或后端订单确认接口
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({
                    success: true,
                    message: '取药确认成功！小车已返回默认位置。',
                    order_id: orderId,
                    confirmed_at: new Date().toISOString(),
                });
            }, 800);
        });
    }

    // 获取配药状态 - 模拟接口
    static async getDispenseStatus(prescriptionId) {
        return new Promise(resolve => {
            setTimeout(() => {
                const statuses = ['pending', 'dispensing', 'ready_for_pickup', 'picked_up'];
                const cartStatuses = ['moving', 'at_pickup_station', 'returning'];
                const randomStatus = statuses[Math.floor(Math.random() * statuses.length)];
                const randomCartStatus = cartStatuses[Math.floor(Math.random() * cartStatuses.length)];

                resolve({
                    order_id: 'ORD-' + Date.now().toString().slice(-8),
                    prescription_id: prescriptionId,
                    dispense_status: randomStatus,
                    cart_status: randomCartStatus,
                    drugs: [
                        { name: '布洛芬', dosage: '200mg', quantity: 2 },
                        { name: '阿莫西林', dosage: '500mg', quantity: 1 }
                    ],
                    dispensed_at: new Date().toISOString(),
                    estimated_arrival: randomCartStatus === 'moving' ? '2分钟' : '已到达',
                });
            }, 600);
        });
    }

    // 获取小车状态 - 对应ROS2状态接口
    static async getCartStatus() {
        // 模拟接口，实际应该调用ROS2状态接口
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({
                    status: 'delivering',
                    location: '取药台',
                    eta: '2分钟',
                    order_id: '12345'
                });
            }, 500);
        });
    }

    // 更新小车状态 - 模拟接口
    static async updateCartStatus(status) {
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({ success: true, message: '状态已更新' });
            }, 300);
        });
    }

    // 发送聊天消息 - 模拟接口（后端未实现）
    static async sendChatMessage(message, patientId) {
        return new Promise(resolve => {
            setTimeout(() => {
                // 模拟AI回复，使用patientId参数
                const patientInfo = patientId ? ` (患者ID: ${patientId})` : '';
                const reply = `根据您的症状描述"${message}"${patientInfo}，我建议使用布洛芬缓解症状。请注意，此建议需要医生审批。`;
                const approvalId = 'AP-' + Date.now().toString().slice(-8);
                const steps = [
                    {
                        type: 'tool_call',
                        tool: 'query_drug',
                        input: { symptoms: message, patient_id: patientId },
                        result: '找到相关药品：布洛芬'
                    },
                    {
                        type: 'tool_call',
                        tool: 'check_allergy',
                        input: { drug: '布洛芬', patient_id: patientId },
                        result: '无已知过敏史'
                    },
                    {
                        type: 'tool_call',
                        tool: 'calc_dosage',
                        input: { drug: '布洛芬', weight: 70, patient_id: patientId },
                        result: '推荐剂量：200mg'
                    }
                ];
                resolve({ reply, approval_id: approvalId, steps });
            }, 1000);
        });
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