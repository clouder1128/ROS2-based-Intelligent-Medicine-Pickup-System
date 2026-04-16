// 医生端专用功能

class DoctorApp {
    constructor() {
        this.doctorId = localStorage.getItem('doctor_id') || null;
        this.doctorName = localStorage.getItem('doctor_name') || null;
        this.currentPage = 1;
        this.pageSize = 10;
        this.totalPages = 1;
        this.currentFilters = {};
        this.currentApprovalId = null;

        this.approvalList = document.getElementById('approval-list');
        this.loadingState = document.getElementById('loading-state');
        this.emptyState = document.getElementById('empty-state');
        this.pagination = document.getElementById('pagination');
        this.filterBar = document.getElementById('filter-bar');
        this.approvalModal = document.getElementById('approval-modal');
        this.resultModal = document.getElementById('result-modal');
        this.loginModal = document.getElementById('login-modal');

        this.init();
    }

    init() {
        this.bindEvents();
        this.checkLogin();
    }

    bindEvents() {
        // 刷新按钮
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadApprovals());
        }

        // 筛选按钮
        const filterBtn = document.getElementById('filter-btn');
        if (filterBtn) {
            filterBtn.addEventListener('click', () => {
                this.filterBar.style.display = this.filterBar.style.display === 'none' ? 'block' : 'none';
            });
        }

        // 筛选操作
        const clearFiltersBtn = document.getElementById('clear-filters-btn');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => this.clearFilters());
        }

        const applyFiltersBtn = document.getElementById('apply-filters-btn');
        if (applyFiltersBtn) {
            applyFiltersBtn.addEventListener('click', () => this.applyFilters());
        }

        // 分页
        const prevPageBtn = document.getElementById('prev-page');
        const nextPageBtn = document.getElementById('next-page');
        if (prevPageBtn) {
            prevPageBtn.addEventListener('click', () => this.changePage(-1));
        }
        if (nextPageBtn) {
            nextPageBtn.addEventListener('click', () => this.changePage(1));
        }

        // 登录按钮
        const loginBtn = document.getElementById('doctor-login-btn');
        if (loginBtn) {
            loginBtn.addEventListener('click', () => this.doctorLogin());
        }

        // 退出按钮
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.doctorLogout());
        }

        // 审批操作
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('view-detail-btn')) {
                const approvalId = e.target.dataset.approvalId;
                this.showApprovalDetail(approvalId);
            }
        });

        // 模态框内审批按钮
        const approveBtn = document.getElementById('approve-btn');
        const rejectBtn = document.getElementById('reject-btn');
        if (approveBtn) {
            approveBtn.addEventListener('click', () => this.submitApproval('approve'));
        }
        if (rejectBtn) {
            rejectBtn.addEventListener('click', () => this.submitApproval('reject'));
        }
    }

    checkLogin() {
        if (!this.doctorId || !this.doctorName) {
            window.App.ModalManager.openModal('login-modal');
        } else {
            this.updateDoctorDisplay();
            this.loadApprovals();
            this.loadStats();
        }
    }

    doctorLogin() {
        const doctorIdInput = document.getElementById('doctor-id-input');
        const doctorNameInput = document.getElementById('doctor-name-input');

        const doctorId = doctorIdInput.value.trim();
        const doctorName = doctorNameInput.value.trim();

        if (!doctorId || !doctorName) {
            window.App.Utils.showNotification('请输入医生ID和姓名', 'warning');
            return;
        }

        this.doctorId = doctorId;
        this.doctorName = doctorName;

        localStorage.setItem('doctor_id', doctorId);
        localStorage.setItem('doctor_name', doctorName);

        window.App.ModalManager.closeModal('login-modal');
        this.updateDoctorDisplay();
        this.loadApprovals();
        this.loadStats();

        window.App.Utils.showNotification(`欢迎回来，${doctorName}医生`, 'success');
    }

    doctorLogout() {
        if (confirm('确定要退出登录吗？')) {
            localStorage.removeItem('doctor_id');
            localStorage.removeItem('doctor_name');
            this.doctorId = null;
            this.doctorName = null;
            window.location.reload();
        }
    }

    updateDoctorDisplay() {
        const doctorIdElement = document.getElementById('doctor-id');
        const doctorNameElement = document.getElementById('doctor-name');

        if (doctorIdElement) doctorIdElement.textContent = this.doctorId;
        if (doctorNameElement) doctorNameElement.textContent = this.doctorName;
    }

    async loadApprovals() {
        if (!this.doctorId) return;

        this.showLoading(true);

        try {
            // 调用API获取待审批列表（不需要doctorId参数）
            const response = await window.App.APIService.getPendingApprovals();
            let approvals = [];

            // 检查API响应格式
            if (response && response.success) {
                approvals = response.approvals || [];
            } else {
                // API调用失败，使用模拟数据
                console.log('使用模拟待审批数据');
                approvals = [
                    {
                        id: 'AP-20250414-001',
                        patient: '张三',
                        patient_age: 35,
                        patient_weight: 70,
                        symptoms: '头痛、发烧，体温38.5°C',
                        advice: '建议服用布洛芬缓解头痛和发烧，每次200mg，每日3次，饭后服用。',
                        drug_name: '布洛芬',
                        drug_type: 'prescription',
                        created_at: '2026-04-14T10:30:25Z'
                    },
                    {
                        id: 'AP-20250414-002',
                        patient: '李四',
                        patient_age: 28,
                        patient_weight: 65,
                        symptoms: '咳嗽、喉咙痛，无发烧',
                        advice: '建议服用阿莫西林，每次500mg，每日2次，连续7天。',
                        drug_name: '阿莫西林',
                        drug_type: 'prescription',
                        created_at: '2026-04-14T11:15:10Z'
                    },
                    {
                        id: 'AP-20250414-003',
                        patient: '王五',
                        patient_age: 45,
                        patient_weight: 80,
                        symptoms: '关节疼痛，活动受限',
                        advice: '建议服用双氯芬酸钠，每次25mg，每日3次，饭后服用。',
                        drug_name: '双氯芬酸钠',
                        drug_type: 'prescription',
                        created_at: '2026-04-14T13:45:30Z'
                    }
                ];
            }

            // 渲染列表
            this.renderApprovalList(approvals);
            this.updateStats(approvals.length);

        } catch (error) {
            console.error('加载审批列表失败:', error);
            this.showError('加载失败，请重试');
        } finally {
            this.showLoading(false);
        }
    }

    renderApprovalList(approvals) {
        if (!approvals || approvals.length === 0) {
            this.emptyState.style.display = 'block';
            this.approvalList.innerHTML = '';
            this.pagination.style.display = 'none';
            return;
        }

        this.emptyState.style.display = 'none';
        this.approvalList.innerHTML = '';

        approvals.forEach(approval => {
            const card = this.createApprovalCard(approval);
            this.approvalList.appendChild(card);
        });

        // 显示分页（如果有）
        this.updatePagination();
    }

    createApprovalCard(approval) {
        const card = document.createElement('div');
        card.className = 'approval-card';
        card.innerHTML = `
            <div class="approval-card-header">
                <div class="approval-id">审批ID: ${approval.id}</div>
                <div class="approval-time">${window.App.Utils.formatTime(approval.created_at)}</div>
            </div>
            <div class="approval-card-body">
                <div class="patient-info">
                    <h4><i class="fas fa-user"></i> ${approval.patient}</h4>
                    <div class="patient-details">
                        <span>年龄: ${approval.patient_age}岁</span>
                        <span>体重: ${approval.patient_weight}kg</span>
                    </div>
                </div>
                <div class="symptom-summary">
                    <h5><i class="fas fa-comment-medical"></i> 症状</h5>
                    <p>${approval.symptoms}</p>
                </div>
                <div class="advice-summary">
                    <h5><i class="fas fa-robot"></i> AI建议</h5>
                    <p>${approval.advice.substring(0, 100)}...</p>
                </div>
                <div class="drug-info">
                    <span class="drug-name">${approval.drug_name}</span>
                    <span class="drug-type ${approval.drug_type}">
                        ${approval.drug_type === 'prescription' ? '处方药' : '非处方药'}
                    </span>
                </div>
            </div>
            <div class="approval-card-footer">
                <button class="btn btn-primary view-detail-btn" data-approval-id="${approval.id}">
                    <i class="fas fa-search"></i> 查看详情并审批
                </button>
            </div>
        `;
        return card;
    }

    async showApprovalDetail(approvalId) {
        this.currentApprovalId = approvalId;

        try {
            window.App.Utils.showLoading(true);

            // 这里应该调用API获取审批详情
            // 暂时使用模拟数据
            const mockDetail = {
                id: approvalId,
                patient_name: '张三',
                patient_age: 35,
                patient_weight: 70,
                symptoms: '患者主诉头痛、发烧，体温38.5°C，伴有轻微咳嗽。无药物过敏史。',
                advice: '建议服用布洛芬缓解头痛和发烧，每次200mg，每日3次，饭后服用。同时建议多喝水，注意休息。如症状持续超过3天或加重，请及时就医。',
                drug_name: '布洛芬',
                drug_type: 'prescription',
                dosage: '200mg',
                usage: '每次1片，每日3次，饭后服用',
                created_at: '2026-04-14T10:30:25Z',
                thinking_steps: [
                    '分析症状：头痛、发烧 → 考虑使用解热镇痛药',
                    '查询药品库：布洛芬适合治疗头痛和发烧',
                    '剂量计算：根据体重70kg计算合适剂量',
                    '生成建议：考虑饭后服用减少胃部刺激'
                ]
            };

            this.renderApprovalDetail(mockDetail);
            window.App.ModalManager.openModal('approval-modal');

        } catch (error) {
            console.error('加载审批详情失败:', error);
            window.App.Utils.showNotification('加载详情失败', 'error');
        } finally {
            window.App.Utils.showLoading(false);
        }
    }

    renderApprovalDetail(detail) {
        // 更新基本信息
        document.getElementById('detail-approval-id').textContent = detail.id;
        document.getElementById('detail-patient-name').textContent = detail.patient_name;
        document.getElementById('detail-patient-age').textContent = detail.patient_age;
        document.getElementById('detail-patient-weight').textContent = detail.patient_weight + ' kg';
        document.getElementById('detail-created-at').textContent = window.App.Utils.formatTime(detail.created_at);

        // 更新症状
        document.getElementById('detail-symptoms').textContent = detail.symptoms;

        // 更新建议
        document.getElementById('detail-advice').textContent = detail.advice;
        document.getElementById('detail-drug-name').textContent = detail.drug_name;
        document.getElementById('detail-drug-type').textContent = detail.drug_type === 'prescription' ? '处方药' : '非处方药';
        document.getElementById('detail-dosage').textContent = detail.dosage;
        document.getElementById('detail-usage').textContent = detail.usage;

        // 更新思考过程
        const thinkingProcess = document.getElementById('detail-thinking-process');
        thinkingProcess.innerHTML = '';
        detail.thinking_steps.forEach((step, index) => {
            const stepDiv = document.createElement('div');
            stepDiv.className = 'thinking-step';
            stepDiv.innerHTML = `
                <span class="step-number">${index + 1}</span>
                <span class="step-text">${step}</span>
            `;
            thinkingProcess.appendChild(stepDiv);
        });

        // 清空审批理由输入框
        document.getElementById('approval-reason').value = '';
    }

    async submitApproval(action) {
        if (!this.currentApprovalId || !this.doctorId) {
            window.App.Utils.showNotification('缺少必要信息', 'error');
            return;
        }

        const reason = document.getElementById('approval-reason').value.trim();

        try {
            window.App.Utils.showLoading(true);

            // 调用API提交审批
            const result = await window.App.APIService.approvePrescription(
                this.currentApprovalId,
                action,
                this.doctorId,
                reason
            );

            // 显示结果
            this.showApprovalResult(action, result);

            // 关闭详情模态框
            window.App.ModalManager.closeModal('approval-modal');

            // 刷新列表
            this.loadApprovals();
            this.loadStats();

        } catch (error) {
            console.error('提交审批失败:', error);
            window.App.Utils.showNotification('提交失败: ' + error.message, 'error');
        } finally {
            window.App.Utils.showLoading(false);
        }
    }

    showApprovalResult(action, result) {
        const resultContent = document.getElementById('result-content');

        if (action === 'approve') {
            resultContent.innerHTML = `
                <div class="result-success">
                    <i class="fas fa-check-circle"></i>
                    <h4>审批通过</h4>
                    <p>✅ 已批准该用药建议。</p>
                    ${result.dispense_result ? `<p>${result.dispense_result}</p>` : ''}
                    <p>系统已自动配药，小车将送药至取药台，等待患者确认取药。</p>
                </div>
            `;
        } else {
            resultContent.innerHTML = `
                <div class="result-rejected">
                    <i class="fas fa-times-circle"></i>
                    <h4>审批拒绝</h4>
                    <p>❌ 已拒绝该用药建议。</p>
                    <p>建议已退回给患者，请向患者说明拒绝理由。</p>
                </div>
            `;
        }

        window.App.ModalManager.openModal('result-modal');
    }

    async loadStats() {
        // 这里应该调用API获取统计信息
        // 暂时模拟
        const mockStats = {
            pending: 3,
            approved: 12,
            rejected: 2,
            total: 17,
            today: 5
        };

        this.updateStatsDisplay(mockStats);
    }

    updateStatsDisplay(stats) {
        // 更新统计数字
        const todayElement = document.getElementById('today-approvals');
        if (todayElement) todayElement.textContent = stats.today;

        // 更新统计卡片
        const pendingElement = document.querySelector('.stat-item:nth-child(1) .stat-value');
        const approvedElement = document.querySelector('.stat-item:nth-child(2) .stat-value');
        const rejectedElement = document.querySelector('.stat-item:nth-child(3) .stat-value');
        const totalElement = document.querySelector('.stat-item:nth-child(4) .stat-value');

        if (pendingElement) pendingElement.textContent = stats.pending;
        if (approvedElement) approvedElement.textContent = stats.approved;
        if (rejectedElement) rejectedElement.textContent = stats.rejected;
        if (totalElement) totalElement.textContent = stats.total;
    }

    updateStats(pendingCount) {
        const pendingElement = document.querySelector('.stat-item:nth-child(1) .stat-value');
        if (pendingElement) pendingElement.textContent = pendingCount;

        const totalElement = document.querySelector('.stat-item:nth-child(4) .stat-value');
        if (totalElement) {
            const currentTotal = parseInt(totalElement.textContent) || 0;
            totalElement.textContent = currentTotal + 1;
        }

        const todayElement = document.getElementById('today-approvals');
        if (todayElement) {
            const todayCount = parseInt(todayElement.textContent) || 0;
            todayElement.textContent = todayCount + 1;
        }
    }

    clearFilters() {
        document.getElementById('filter-patient').value = '';
        document.getElementById('filter-date').value = '';
        document.getElementById('filter-drug').value = '';
        this.currentFilters = {};
        this.loadApprovals();
    }

    applyFilters() {
        const patient = document.getElementById('filter-patient').value.trim();
        const date = document.getElementById('filter-date').value;
        const drugType = document.getElementById('filter-drug').value;

        this.currentFilters = {};
        if (patient) this.currentFilters.patient = patient;
        if (date) this.currentFilters.date = date;
        if (drugType) this.currentFilters.drug_type = drugType;

        this.currentPage = 1;
        this.loadApprovals();
    }

    changePage(delta) {
        const newPage = this.currentPage + delta;
        if (newPage < 1 || newPage > this.totalPages) return;

        this.currentPage = newPage;
        this.loadApprovals();
    }

    updatePagination() {
        if (this.totalPages <= 1) {
            this.pagination.style.display = 'none';
            return;
        }

        this.pagination.style.display = 'flex';
        document.getElementById('current-page').textContent = this.currentPage;
        document.getElementById('total-pages').textContent = this.totalPages;

        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');

        prevBtn.disabled = this.currentPage <= 1;
        nextBtn.disabled = this.currentPage >= this.totalPages;
    }

    showLoading(show) {
        if (show) {
            this.loadingState.style.display = 'block';
            this.emptyState.style.display = 'none';
        } else {
            this.loadingState.style.display = 'none';
        }
    }

    showError(message) {
        this.approvalList.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>加载失败</h3>
                <p>${message}</p>
                <button class="btn btn-primary" onclick="window.doctorApp.loadApprovals()">重试</button>
            </div>
        `;
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    // 检查是否在医生页面
    if (document.getElementById('approval-list')) {
        window.doctorApp = new DoctorApp();
    }
});

// 添加一些额外的CSS样式
const style = document.createElement('style');
style.textContent = `
.approval-card {
    background-color: white;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
    margin-bottom: 20px;
    overflow: hidden;
    transition: var(--transition);
}

.approval-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-hover);
}

.approval-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
    background-color: #f8f9fa;
    border-bottom: 1px solid var(--light-color);
}

.approval-id {
    font-weight: 600;
    color: var(--dark-color);
}

.approval-time {
    color: var(--gray-color);
    font-size: 0.9rem;
}

.approval-card-body {
    padding: 20px;
}

.patient-info h4 {
    margin-bottom: 10px;
    color: var(--dark-color);
}

.patient-details {
    display: flex;
    gap: 20px;
    color: var(--gray-color);
    font-size: 0.9rem;
    margin-bottom: 15px;
}

.symptom-summary,
.advice-summary {
    margin-bottom: 15px;
}

.symptom-summary h5,
.advice-summary h5 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 5px;
    color: var(--dark-color);
    font-size: 1rem;
}

.symptom-summary p,
.advice-summary p {
    color: var(--dark-color);
    line-height: 1.5;
}

.drug-info {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px solid var(--light-color);
}

.drug-name {
    font-weight: 600;
    color: var(--primary-color);
}

.drug-type {
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
}

.drug-type.prescription {
    background-color: #e3f2fd;
    color: var(--primary-color);
}

.drug-type.otc {
    background-color: #e8f5e9;
    color: var(--secondary-color);
}

.approval-card-footer {
    padding: 15px 20px;
    background-color: #f8f9fa;
    border-top: 1px solid var(--light-color);
    text-align: right;
}

.filter-bar {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: var(--border-radius);
    margin-bottom: 20px;
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    align-items: flex-end;
}

.filter-group {
    display: flex;
    flex-direction: column;
    min-width: 150px;
}

.filter-group label {
    margin-bottom: 5px;
    font-size: 0.9rem;
    color: var(--dark-color);
}

.filter-actions {
    display: flex;
    gap: 10px;
    margin-left: auto;
}

.detail-section {
    margin-bottom: 25px;
    padding-bottom: 25px;
    border-bottom: 1px solid var(--light-color);
}

.detail-section:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
}

.detail-section h4 {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 15px;
    color: var(--dark-color);
}

.detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
}

.symptom-box,
.advice-box {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: var(--border-radius);
    line-height: 1.6;
    white-space: pre-wrap;
}

.advice-details {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-top: 15px;
}

.thinking-step {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 10px;
    padding: 10px;
    background-color: #f8f9fa;
    border-radius: var(--border-radius);
}

.step-number {
    background-color: var(--primary-color);
    color: white;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 600;
    flex-shrink: 0;
}

.step-text {
    flex: 1;
    line-height: 1.5;
}

.action-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 20px;
}

.result-success,
.result-rejected {
    text-align: center;
    padding: 20px;
}

.result-success i {
    color: var(--secondary-color);
    font-size: 3rem;
    margin-bottom: 15px;
}

.result-rejected i {
    color: var(--danger-color);
    font-size: 3rem;
    margin-bottom: 15px;
}

.loading-state {
    text-align: center;
    padding: 40px;
}

.error-state {
    text-align: center;
    padding: 40px;
    color: var(--danger-color);
}

.error-state i {
    font-size: 3rem;
    margin-bottom: 15px;
}

.stat-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid var(--light-color);
}

.stat-item:last-child {
    border-bottom: none;
}

.stat-label {
    color: var(--gray-color);
}

.stat-value {
    font-weight: 600;
    color: var(--dark-color);
}

.stat-value.pending {
    color: var(--warning-color);
}

.stat-value.approved {
    color: var(--secondary-color);
}

.stat-value.rejected {
    color: var(--danger-color);
}
`;
document.head.appendChild(style);