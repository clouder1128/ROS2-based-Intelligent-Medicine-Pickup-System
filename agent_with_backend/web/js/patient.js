// 患者端专用功能

class PatientApp {
    constructor() {
        this.chatContainer = document.getElementById('chat-container');
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.statusIndicator = document.getElementById('status-indicator');
        this.statusText = document.getElementById('status-text');
        this.statusDot = this.statusIndicator.querySelector('.status-dot');
        this.approvalStatus = document.getElementById('approval-status');
        this.pickupInfo = document.getElementById('pickup-info');
        this.patientModal = document.getElementById('patient-modal');
        this.pickupModal = document.getElementById('pickup-modal');
        this.changePatientBtn = document.getElementById('change-patient-btn');
        this.refreshStatusBtn = document.getElementById('refresh-status-btn');
        this.currentApprovalId = null;
        this.patientId = window.App.SessionManager.getPatient().id;
        this.patientName = window.App.SessionManager.getPatient().name;

        this.init();
    }

    init() {
        this.bindEvents();
        this.checkPatient();
        this.updateStatus();
        this.startStatusPolling();
    }

    bindEvents() {
        // 发送消息
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // 切换患者
        if (this.changePatientBtn) {
            this.changePatientBtn.addEventListener('click', () => {
                window.App.ModalManager.openModal('patient-modal');
            });
        }

        // 保存患者信息
        const savePatientBtn = document.getElementById('save-patient-btn');
        if (savePatientBtn) {
            savePatientBtn.addEventListener('click', () => this.savePatientInfo());
        }

        // 刷新状态
        if (this.refreshStatusBtn) {
            this.refreshStatusBtn.addEventListener('click', () => this.updateStatus());
        }

    }

    checkPatient() {
        if (!this.patientId || !this.patientName) {
            window.App.Utils.showNotification('请先设置患者信息', 'warning');
            setTimeout(() => {
                window.App.ModalManager.openModal('patient-modal');
            }, 1000);
        } else {
            this.updatePatientDisplay();
        }
    }

    updatePatientDisplay() {
        const patientIdElement = document.getElementById('patient-id');
        if (patientIdElement) {
            patientIdElement.textContent = this.patientId;
        }
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) {
            window.App.Utils.showNotification('请输入症状描述', 'warning');
            return;
        }

        if (!this.patientId || !this.patientName) {
            window.App.Utils.showNotification('请先设置患者信息', 'warning');
            window.App.ModalManager.openModal('patient-modal');
            return;
        }

        // 添加用户消息到聊天界面
        this.addMessageToChat('user', message);

        // 清空输入框
        this.messageInput.value = '';

        // 更新状态
        this.setStatus('thinking', 'AI正在分析症状...');

        try {
            // 发送请求
            window.App.Utils.showLoading(true);
            const response = await window.App.APIService.sendChatMessage(message, this.patientId);

            // 添加AI回复
            this.addMessageToChat('ai', response.reply);

            // 如果有审批ID，保存并更新状态
            if (response.approval_id) {
                this.currentApprovalId = response.approval_id;
                this.showApprovalSubmitted(response.approval_id);
                this.updateStatus();
            }

            // 显示执行步骤（调试用）
            if (response.steps && response.steps.length > 0) {
                this.showToolSteps(response.steps);
            }

            window.App.Utils.showNotification('咨询完成，等待医生审批', 'success');

        } catch (error) {
            console.error('发送消息失败:', error);
            this.addMessageToChat('ai', '抱歉，处理您的请求时出现错误。请稍后再试。');
            window.App.Utils.showNotification('发送失败: ' + error.message, 'error');
        } finally {
            window.App.Utils.showLoading(false);
            this.setStatus('idle', '等待输入');
        }
    }

    addMessageToChat(type, content) {
        const messageDiv = document.createElement('div');
        const timestamp = new Date().toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
        });

        let icon, sender, className;
        switch (type) {
            case 'user':
                icon = 'fas fa-user';
                sender = '您';
                className = 'message user-message';
                break;
            case 'ai':
                icon = 'fas fa-robot';
                sender = 'AI开药助手';
                className = 'message ai-message';
                break;
            case 'tool':
                icon = 'fas fa-tools';
                sender = '工具调用';
                className = 'message tool-message';
                break;
        }

        messageDiv.className = className;
        messageDiv.innerHTML = `
            <div class="message-header">
                <i class="${icon}"></i>
                <span class="sender">${sender}</span>
                <span class="timestamp">${timestamp}</span>
            </div>
            <div class="message-content">${this.escapeHtml(content)}</div>
        `;

        this.chatContainer.appendChild(messageDiv);
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }

    showToolSteps(steps) {
        steps.forEach(step => {
            if (step.type === 'tool_call') {
                const toolInfo = `工具调用: ${step.tool}\n输入: ${JSON.stringify(step.input, null, 2)}\n结果: ${step.result}`;
                this.addMessageToChat('tool', toolInfo);
            }
        });
    }

    showApprovalSubmitted(approvalId) {
        const approvalDiv = document.createElement('div');
        approvalDiv.className = 'message ai-message';
        approvalDiv.innerHTML = `
            <div class="message-header">
                <i class="fas fa-clipboard-check"></i>
                <span class="sender">系统通知</span>
                <span class="timestamp">刚刚</span>
            </div>
            <div class="message-content">
                <p>✅ 您的用药建议已提交审批，审批ID: <strong>${approvalId}</strong></p>
                <p>医生将尽快审批您的建议。审批通过后，系统会自动配药，小车将送药至取药台。</p>
            </div>
        `;
        this.chatContainer.appendChild(approvalDiv);
    }

    async updateStatus() {
        if (!this.currentApprovalId) {
            this.updateApprovalStatusUI(null);
            return;
        }

        try {
            // 这里应该调用一个获取审批状态的API
            // 暂时模拟API调用
            // const status = await window.App.APIService.getApprovalStatus(this.currentApprovalId);

            // 模拟数据
            const mockStatus = {
                approval_id: this.currentApprovalId,
                status: 'pending', // pending, approved, rejected
                doctor_id: 'dr_wang',
                created_at: new Date().toISOString(),
                approved_at: null,
                reject_reason: '',
            };

            this.updateApprovalStatusUI(mockStatus);

            // 如果已批准，检查是否有取药码
            if (mockStatus.status === 'approved') {
                this.checkPickupInfo();
            }

        } catch (error) {
            console.error('获取状态失败:', error);
        }
    }

    updateApprovalStatusUI(status) {
        if (!status) {
            this.approvalStatus.innerHTML = `
                <div class="status-item">
                    <span class="status-label">建议状态:</span>
                    <span class="status-value pending">无待审批建议</span>
                </div>
                <div class="status-item">
                    <span class="status-label">审批医生:</span>
                    <span class="status-value">-</span>
                </div>
                <div class="status-item">
                    <span class="status-label">提交时间:</span>
                    <span class="status-value">-</span>
                </div>
            `;
            return;
        }

        const statusClass = status.status;
        const statusText = {
            pending: '待审批',
            approved: '已批准',
            rejected: '已拒绝'
        }[status.status] || status.status;

        this.approvalStatus.innerHTML = `
            <div class="status-item">
                <span class="status-label">审批ID:</span>
                <span class="status-value">${status.approval_id}</span>
            </div>
            <div class="status-item">
                <span class="status-label">建议状态:</span>
                <span class="status-value ${statusClass}">${statusText}</span>
            </div>
            <div class="status-item">
                <span class="status-label">审批医生:</span>
                <span class="status-value">${status.doctor_id || '-'}</span>
            </div>
            <div class="status-item">
                <span class="status-label">提交时间:</span>
                <span class="status-value">${window.App.Utils.formatTime(status.created_at)}</span>
            </div>
            ${status.status === 'rejected' && status.reject_reason ? `
                <div class="status-item">
                    <span class="status-label">拒绝理由:</span>
                    <span class="status-value">${status.reject_reason}</span>
                </div>
            ` : ''}
        `;

        // 显示刷新按钮
        const actionsDiv = document.getElementById('approval-actions');
        if (actionsDiv) {
            actionsDiv.style.display = 'block';
        }
    }

    async checkPickupInfo() {
        if (!this.currentApprovalId) {
            this.updatePickupInfoUI(null);
            return;
        }

        try {
            // 使用approvalId作为prescriptionId获取配药状态
            const dispense = await window.App.APIService.getDispenseStatus(this.currentApprovalId);
            this.updatePickupInfoUI(dispense);
        } catch (error) {
            console.error('获取配药信息失败:', error);
            // 失败时显示模拟数据
            const mockDispense = {
                order_id: 'ORD-' + Date.now().toString().slice(-8),
                prescription_id: this.currentApprovalId,
                dispense_status: 'ready_for_pickup',
                cart_status: 'at_pickup_station',
                drugs: [
                    { name: '阿莫西林', dosage: '500mg', quantity: 2 }
                ],
                dispensed_at: new Date().toISOString(),
                estimated_arrival: '2分钟',
            };
            this.updatePickupInfoUI(mockDispense);
        }
    }

    updatePickupInfoUI(dispense) {
        if (!dispense) {
            this.pickupInfo.innerHTML = '<p class="no-info">暂无配药信息</p>';
            return;
        }

        const statusText = {
            pending: '待配药',
            dispensing: '配药中',
            ready_for_pickup: '待取药',
            picked_up: '已取药'
        }[dispense.dispense_status] || dispense.dispense_status;

        const statusClass = {
            pending: 'pending',
            dispensing: 'pending',
            ready_for_pickup: 'approved',
            picked_up: 'dispensed'
        }[dispense.dispense_status] || 'pending';

        let actionButton = '';
        if (dispense.dispense_status === 'ready_for_pickup') {
            actionButton = `
                <button class="btn btn-primary btn-block" id="confirm-pickup-btn">
                    <i class="fas fa-check-circle"></i> 确认取药
                </button>
            `;
        }

        this.pickupInfo.innerHTML = `
            <div class="pickup-item">
                <div class="detail-item">
                    <span class="detail-label">订单号</span>
                    <span class="detail-value">${dispense.order_id}</span>
                </div>
            </div>
            <div class="pickup-item">
                <div class="detail-item">
                    <span class="detail-label">配药状态</span>
                    <span class="status-value ${statusClass}">${statusText}</span>
                </div>
            </div>
            <div class="pickup-item">
                <div class="detail-item">
                    <span class="detail-label">小车状态</span>
                    <span class="detail-value">${dispense.cart_status === 'at_pickup_station' ? '已到达取药台' : '运送中'}</span>
                </div>
            </div>
            ${dispense.dispense_status === 'dispensing' ? `
                <div class="pickup-item">
                    <div class="detail-item">
                        <span class="detail-label">预计到达</span>
                        <span class="detail-value">${dispense.estimated_arrival}</span>
                    </div>
                </div>
            ` : ''}
            <div class="pickup-item">
                <div class="detail-label">药品清单</div>
                <ul style="margin-top: 5px;">
                    ${dispense.drugs.map(drug =>
                        `<li>${drug.name} - ${drug.dosage} × ${drug.quantity}</li>`
                    ).join('')}
                </ul>
            </div>
            ${actionButton}
        `;

        // 添加确认取药按钮事件
        if (dispense.dispense_status === 'ready_for_pickup') {
            const confirmBtn = document.getElementById('confirm-pickup-btn');
            if (confirmBtn) {
                confirmBtn.addEventListener('click', () => {
                    this.confirmPickup(dispense.order_id);
                });
            }
        }
    }

    async confirmPickup(orderId) {
        try {
            window.App.Utils.showLoading(true);
            // 调用API确认取药
            const result = await window.App.APIService.confirmPatientPickup(orderId);

            window.App.Utils.showNotification(result.message || '取药确认成功！小车已返回默认位置。', 'success');

            // 刷新状态
            this.updateStatus();

        } catch (error) {
            console.error('确认取药失败:', error);
            window.App.Utils.showNotification('确认取药失败: ' + error.message, 'error');
        } finally {
            window.App.Utils.showLoading(false);
        }
    }


    savePatientInfo() {
        const patientIdInput = document.getElementById('patient-id-input');
        const patientNameInput = document.getElementById('patient-name-input');

        const patientId = patientIdInput.value.trim();
        const patientName = patientNameInput.value.trim();

        if (!patientId || !patientName) {
            window.App.Utils.showNotification('请输入完整的患者信息', 'warning');
            return;
        }

        // 保存患者信息
        window.App.SessionManager.setPatient(patientId, patientName);
        this.patientId = patientId;
        this.patientName = patientName;

        // 更新显示
        this.updatePatientDisplay();

        // 关闭模态框
        window.App.ModalManager.closeModal('patient-modal');

        // 清空输入框
        patientIdInput.value = '';
        patientNameInput.value = '';
    }

    setStatus(type, text) {
        this.statusText.textContent = text;
        this.statusDot.className = 'status-dot';

        switch (type) {
            case 'thinking':
                this.statusDot.classList.add('thinking');
                break;
            case 'error':
                this.statusDot.classList.add('error');
                break;
            case 'idle':
                this.statusDot.classList.add('idle');
                break;
        }
    }

    startStatusPolling() {
        // 每30秒轮询一次状态
        setInterval(() => {
            if (this.currentApprovalId) {
                this.updateStatus();
            }
        }, 30000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    // 检查是否在患者页面
    if (document.getElementById('chat-container')) {
        window.patientApp = new PatientApp();
    }
});