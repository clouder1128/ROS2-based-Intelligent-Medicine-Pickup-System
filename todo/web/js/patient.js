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

        // 打印取药码
        const printPickupBtn = document.getElementById('print-pickup-btn');
        if (printPickupBtn) {
            printPickupBtn.addEventListener('click', () => window.print());
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
                <p>医生将尽快审批您的建议。审批通过后，系统会自动配药并生成取药码。</p>
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
        try {
            // 这里应该调用获取处方信息的API
            // 暂时模拟
            const mockPrescription = {
                prescription_id: 'RX-20250414-001',
                status: 'dispensed',
                pickup_code: 'A1B2C3',
                drugs: [
                    { name: '阿莫西林', dosage: '500mg', quantity: 2 }
                ],
                dispensed_at: new Date().toISOString(),
            };

            this.updatePickupInfoUI(mockPrescription);

        } catch (error) {
            console.error('获取取药信息失败:', error);
        }
    }

    updatePickupInfoUI(prescription) {
        if (!prescription) {
            this.pickupInfo.innerHTML = '<p class="no-info">暂无取药信息</p>';
            return;
        }

        if (prescription.status === 'dispensed' && prescription.pickup_code) {
            this.pickupInfo.innerHTML = `
                <div class="pickup-item">
                    <div class="detail-item">
                        <span class="detail-label">处方号</span>
                        <span class="detail-value">${prescription.prescription_id}</span>
                    </div>
                </div>
                <div class="pickup-item">
                    <div class="detail-item">
                        <span class="detail-label">取药码</span>
                        <span class="detail-value pickup-code">${prescription.pickup_code}</span>
                    </div>
                </div>
                <div class="pickup-item">
                    <div class="detail-label">药品清单</div>
                    <ul style="margin-top: 5px;">
                        ${prescription.drugs.map(drug =>
                            `<li>${drug.name} - ${drug.dosage} × ${drug.quantity}</li>`
                        ).join('')}
                    </ul>
                </div>
                <button class="btn btn-primary btn-block" id="show-pickup-modal-btn">
                    <i class="fas fa-qrcode"></i> 查看取药码
                </button>
            `;

            // 添加查看取药码按钮事件
            const showBtn = document.getElementById('show-pickup-modal-btn');
            if (showBtn) {
                showBtn.addEventListener('click', () => {
                    this.showPickupModal(prescription);
                });
            }
        } else {
            this.pickupInfo.innerHTML = `
                <div class="pickup-item">
                    <p>处方状态: <span class="status-value pending">${prescription.status}</span></p>
                    <p>审批已通过，等待配药中...</p>
                </div>
            `;
        }
    }

    showPickupModal(prescription) {
        const pickupCodeValue = document.getElementById('pickup-code-value');
        const pickupDetails = document.getElementById('pickup-details');

        if (pickupCodeValue) {
            pickupCodeValue.textContent = prescription.pickup_code;
        }

        if (pickupDetails) {
            pickupDetails.innerHTML = `
                <div class="pickup-item">
                    <div class="detail-item">
                        <span class="detail-label">处方号</span>
                        <span class="detail-value">${prescription.prescription_id}</span>
                    </div>
                </div>
                <div class="pickup-item">
                    <div class="detail-item">
                        <span class="detail-label">患者姓名</span>
                        <span class="detail-value">${this.patientName}</span>
                    </div>
                </div>
                <div class="pickup-item">
                    <div class="detail-label">药品清单</div>
                    <ul>
                        ${prescription.drugs.map(drug =>
                            `<li><strong>${drug.name}</strong> - ${drug.dosage} × ${drug.quantity}</li>`
                        ).join('')}
                    </ul>
                </div>
                <div class="pickup-item">
                    <div class="detail-item">
                        <span class="detail-label">配药时间</span>
                        <span class="detail-value">${window.App.Utils.formatTime(prescription.dispensed_at)}</span>
                    </div>
                </div>
            `;
        }

        window.App.ModalManager.openModal('pickup-modal');
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