// 历史查询专用功能

class HistoryApp {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 10;
        this.totalPages = 1;
        this.currentFilters = {
            patient_name: '张三',
            start_date: '2026-04-01',
            end_date: '2026-04-14'
        };

        this.historyList = document.getElementById('history-list');
        this.loadingState = document.getElementById('loading-state');
        this.emptyState = document.getElementById('empty-state');
        this.pagination = document.getElementById('pagination');
        this.patientNameInput = document.getElementById('patient-name-input');
        this.startDateInput = document.getElementById('date-range-start');
        this.endDateInput = document.getElementById('date-range-end');
        this.drugTypeFilter = document.getElementById('drug-type-filter');

        this.init();
    }

    init() {
        this.bindEvents();
        this.loadHistory();
        this.updateStats();
    }

    bindEvents() {
        // 查询按钮
        const searchBtn = document.getElementById('search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => this.searchHistory());
        }

        // 重置按钮
        const resetBtn = document.getElementById('reset-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetFilters());
        }

        // 导出按钮
        const exportBtn = document.getElementById('export-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                window.App.ModalManager.openModal('export-modal');
            });
        }

        // 打印按钮
        const printBtn = document.getElementById('print-btn');
        if (printBtn) {
            printBtn.addEventListener('click', () => window.print());
        }

        // 确认导出按钮
        const confirmExportBtn = document.getElementById('confirm-export-btn');
        if (confirmExportBtn) {
            confirmExportBtn.addEventListener('click', () => this.exportHistory());
        }

        // 打印详情按钮
        const printDetailBtn = document.getElementById('print-detail-btn');
        if (printDetailBtn) {
            printDetailBtn.addEventListener('click', () => window.print());
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

        // 查看详情按钮
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('view-detail-btn')) {
                const prescriptionId = e.target.dataset.prescriptionId;
                this.showHistoryDetail(prescriptionId);
            }
        });

        // 初始化过滤器值
        if (this.patientNameInput) this.patientNameInput.value = this.currentFilters.patient_name;
        if (this.startDateInput) this.startDateInput.value = this.currentFilters.start_date;
        if (this.endDateInput) this.endDateInput.value = this.currentFilters.end_date;
    }

    async loadHistory() {
        this.showLoading(true);

        try {
            // 调用API获取用药历史
            // const data = await window.App.APIService.getPatientHistory(this.currentFilters.patient_name);

            // 模拟数据
            const mockData = [
                {
                    prescription_id: 'RX-20250414-001',
                    patient_name: '张三',
                    drugs: [
                        { name: '布洛芬', specification: '200mg/片', quantity: 2, price: 5.00 },
                        { name: '维生素C', specification: '100mg/片', quantity: 1, price: 3.00 }
                    ],
                    advice: '建议服用布洛芬缓解头痛和发烧，每次200mg，每日3次，饭后服用。',
                    total_price: 13.00,
                    status: 'dispensed',
                    created_at: '2026-04-14T10:30:25Z',
                    dispensed_at: '2026-04-14T11:15:30Z',
                    doctor_name: '王医生',
                    pharmacist_name: '张药师',
                    pickup_code: 'A1B2C3'
                },
                {
                    prescription_id: 'RX-20250413-002',
                    patient_name: '张三',
                    drugs: [
                        { name: '阿莫西林', specification: '500mg/粒', quantity: 1, price: 8.00 }
                    ],
                    advice: '建议服用阿莫西林治疗喉咙痛，每次500mg，每日2次，连续7天。',
                    total_price: 8.00,
                    status: 'dispensed',
                    created_at: '2026-04-13T09:15:10Z',
                    dispensed_at: '2026-04-13T10:30:45Z',
                    doctor_name: '李医生',
                    pharmacist_name: '李药师',
                    pickup_code: 'D4E5F6'
                },
                {
                    prescription_id: 'RX-20250412-003',
                    patient_name: '张三',
                    drugs: [
                        { name: '双氯芬酸钠', specification: '25mg/片', quantity: 3, price: 4.00 }
                    ],
                    advice: '建议服用双氯芬酸钠缓解关节疼痛，每次25mg，每日3次。',
                    total_price: 12.00,
                    status: 'rejected',
                    created_at: '2026-04-12T14:20:30Z',
                    dispensed_at: null,
                    doctor_name: '张医生',
                    pharmacist_name: null,
                    pickup_code: null,
                    reject_reason: '患者对非甾体抗炎药过敏'
                }
            ];

            this.renderHistoryList(mockData);
            this.updateStats(mockData);

        } catch (error) {
            console.error('加载历史记录失败:', error);
            this.showError('加载失败，请重试');
        } finally {
            this.showLoading(false);
        }
    }

    renderHistoryList(histories) {
        if (!histories || histories.length === 0) {
            this.emptyState.style.display = 'block';
            this.historyList.innerHTML = '';
            this.pagination.style.display = 'none';
            return;
        }

        this.emptyState.style.display = 'none';
        this.historyList.innerHTML = '';

        histories.forEach(history => {
            const card = this.createHistoryCard(history);
            this.historyList.appendChild(card);
        });

        this.updatePagination();
    }

    createHistoryCard(history) {
        const card = document.createElement('div');
        card.className = 'history-card';

        const statusClass = history.status === 'dispensed' ? 'approved' :
                          history.status === 'rejected' ? 'rejected' : 'pending';
        const statusText = history.status === 'dispensed' ? '已配药' :
                          history.status === 'rejected' ? '已拒绝' : '待处理';

        card.innerHTML = `
            <div class="history-card-header">
                <div class="prescription-id">处方号: ${history.prescription_id}</div>
                <div class="prescription-time">${window.App.Utils.formatTime(history.created_at)}</div>
            </div>
            <div class="history-card-body">
                <div class="prescription-info">
                    <div class="info-row">
                        <span class="info-label">患者:</span>
                        <span class="info-value">${history.patient_name}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">状态:</span>
                        <span class="status-value ${statusClass}">${statusText}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">审批医生:</span>
                        <span class="info-value">${history.doctor_name || '-'}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">配药药师:</span>
                        <span class="info-value">${history.pharmacist_name || '-'}</span>
                    </div>
                </div>
                <div class="drugs-summary">
                    <h5><i class="fas fa-pills"></i> 药品清单</h5>
                    <ul>
                        ${history.drugs.map(drug =>
                            `<li>${drug.name} (${drug.specification}) × ${drug.quantity}</li>`
                        ).join('')}
                    </ul>
                </div>
                <div class="advice-summary">
                    <h5><i class="fas fa-robot"></i> AI建议摘要</h5>
                    <p>${history.advice.substring(0, 100)}...</p>
                </div>
                <div class="prescription-footer">
                    <div class="total-price">总金额: ¥ ${history.total_price.toFixed(2)}</div>
                    ${history.pickup_code ? `<div class="pickup-code">取药码: ${history.pickup_code}</div>` : ''}
                </div>
            </div>
            <div class="history-card-actions">
                <button class="btn btn-primary view-detail-btn" data-prescription-id="${history.prescription_id}">
                    <i class="fas fa-search"></i> 查看详情
                </button>
            </div>
        `;
        return card;
    }

    async showHistoryDetail(prescriptionId) {
        try {
            window.App.Utils.showLoading(true);

            // 调用API获取历史详情
            // const history = await window.App.APIService.getPrescription(prescriptionId);

            // 模拟数据
            const mockHistory = {
                prescription_id: prescriptionId,
                patient_name: '张三',
                drugs: [
                    { name: '布洛芬', specification: '200mg/片', quantity: 2, price: 5.00, type: 'prescription' },
                    { name: '维生素C', specification: '100mg/片', quantity: 1, price: 3.00, type: 'otc' }
                ],
                total_price: 13.00,
                status: 'dispensed',
                created_at: '2026-04-14T10:30:25Z',
                dispensed_at: '2026-04-14T11:15:30Z',
                doctor_name: '王医生',
                pharmacist_name: '张药师',
                pickup_code: 'A1B2C3',
                symptoms: '患者主诉头痛、发烧，体温38.5°C，伴有轻微咳嗽。无药物过敏史。',
                advice: '建议服用布洛芬缓解头痛和发烧，每次200mg，每日3次，饭后服用。同时建议多喝水，注意休息。如症状持续超过3天或加重，请及时就医。',
                payment_method: '医保支付',
                pickup_method: '窗口自取'
            };

            this.renderHistoryDetail(mockHistory);
            window.App.ModalManager.openModal('history-modal');

        } catch (error) {
            console.error('加载历史详情失败:', error);
            window.App.Utils.showNotification('加载详情失败', 'error');
        } finally {
            window.App.Utils.showLoading(false);
        }
    }

    renderHistoryDetail(history) {
        // 更新处方信息
        document.getElementById('detail-prescription-id').textContent = history.prescription_id;
        document.getElementById('detail-patient-name').textContent = history.patient_name;
        document.getElementById('detail-status').textContent = history.status === 'dispensed' ? '已配药' :
                                                              history.status === 'rejected' ? '已拒绝' : '待处理';
        document.getElementById('detail-doctor').textContent = history.doctor_name;
        document.getElementById('detail-created-at').textContent = window.App.Utils.formatTime(history.created_at);
        document.getElementById('detail-dispensed-at').textContent = history.dispensed_at ?
            window.App.Utils.formatTime(history.dispensed_at) : '-';
        document.getElementById('detail-pharmacist').textContent = history.pharmacist_name || '-';
        document.getElementById('detail-pickup-code').textContent = history.pickup_code || '-';
        document.getElementById('detail-payment-method').textContent = history.payment_method || '-';
        document.getElementById('detail-pickup-method').textContent = history.pickup_method || '-';

        // 更新症状和建议
        document.getElementById('detail-symptoms').textContent = history.symptoms;
        document.getElementById('detail-advice').textContent = history.advice;

        // 更新药品表格
        const drugsTableBody = document.getElementById('drugs-table-body');
        drugsTableBody.innerHTML = '';

        history.drugs.forEach((drug, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${drug.name}</td>
                <td>${drug.specification}</td>
                <td>${drug.quantity}</td>
                <td>¥ ${drug.price.toFixed(2)}</td>
                <td>¥ ${(drug.quantity * drug.price).toFixed(2)}</td>
                <td><span class="drug-type ${drug.type}">${drug.type === 'prescription' ? '处方药' : '非处方药'}</span></td>
            `;
            drugsTableBody.appendChild(row);
        });

        // 更新总金额
        document.getElementById('detail-total-price').textContent = `¥ ${history.total_price.toFixed(2)}`;
    }

    searchHistory() {
        this.currentFilters = {
            patient_name: this.patientNameInput.value.trim(),
            start_date: this.startDateInput.value,
            end_date: this.endDateInput.value,
            drug_type: this.drugTypeFilter.value
        };

        this.currentPage = 1;
        this.loadHistory();
    }

    resetFilters() {
        this.patientNameInput.value = '';
        this.startDateInput.value = '';
        this.endDateInput.value = '';
        this.drugTypeFilter.value = '';

        this.currentFilters = {};
        this.currentPage = 1;
        this.loadHistory();
    }

    async exportHistory() {
        const format = document.getElementById('export-format').value;
        const range = document.getElementById('export-range').value;

        window.App.Utils.showNotification(`正在导出${format.toUpperCase()}格式的历史记录...`, 'info');

        // 模拟导出过程
        setTimeout(() => {
            window.App.Utils.showNotification('导出成功！文件已保存到下载文件夹', 'success');
            window.App.ModalManager.closeModal('export-modal');
        }, 2000);
    }

    updateStats(histories = []) {
        const total = histories.length;
        const approved = histories.filter(h => h.status === 'dispensed').length;
        const totalDrugs = histories.reduce((sum, h) => sum + h.drugs.length, 0);

        document.getElementById('total-prescriptions').textContent = total;
        document.getElementById('approved-prescriptions').textContent = approved;
        document.getElementById('total-drugs').textContent = totalDrugs;
    }

    changePage(delta) {
        const newPage = this.currentPage + delta;
        if (newPage < 1 || newPage > this.totalPages) return;

        this.currentPage = newPage;
        this.loadHistory();
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
        this.historyList.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>加载失败</h3>
                <p>${message}</p>
                <button class="btn btn-primary" onclick="window.historyApp.loadHistory()">重试</button>
            </div>
        `;
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    // 检查是否在历史查询页面
    if (document.getElementById('history-list')) {
        window.historyApp = new HistoryApp();
    }
});

// 添加一些额外的CSS样式
const style = document.createElement('style');
style.textContent = `
.history-card {
    background-color: white;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
    margin-bottom: 20px;
    overflow: hidden;
    transition: var(--transition);
}

.history-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-hover);
}

.history-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
    background-color: #f8f9fa;
    border-bottom: 1px solid var(--light-color);
}

.prescription-id {
    font-weight: 600;
    color: var(--dark-color);
}

.prescription-time {
    color: var(--gray-color);
    font-size: 0.9rem;
}

.history-card-body {
    padding: 20px;
}

.prescription-info {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
}

.info-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.info-label {
    color: var(--gray-color);
    font-weight: 500;
}

.info-value {
    color: var(--dark-color);
    font-weight: 500;
}

.status-value {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 600;
}

.status-value.approved {
    background-color: #d4edda;
    color: #155724;
}

.status-value.rejected {
    background-color: #f8d7da;
    color: #721c24;
}

.status-value.pending {
    background-color: #fff3cd;
    color: #856404;
}

.drugs-summary {
    margin-bottom: 15px;
    padding-bottom: 15px;
    border-bottom: 1px solid var(--light-color);
}

.drugs-summary h5,
.advice-summary h5 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    color: var(--dark-color);
    font-size: 1rem;
}

.drugs-summary ul {
    list-style: none;
    padding-left: 20px;
}

.drugs-summary li {
    margin-bottom: 5px;
    color: var(--dark-color);
}

.advice-summary {
    margin-bottom: 15px;
}

.advice-summary p {
    color: var(--dark-color);
    line-height: 1.5;
}

.prescription-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 15px;
    border-top: 1px solid var(--light-color);
}

.total-price {
    font-weight: 600;
    color: var(--primary-color);
}

.pickup-code {
    color: var(--gray-color);
    font-family: monospace;
    letter-spacing: 1px;
}

.history-card-actions {
    padding: 15px 20px;
    background-color: #f8f9fa;
    border-top: 1px solid var(--light-color);
    text-align: right;
}

.two-column {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

@media (max-width: 768px) {
    .two-column {
        grid-template-columns: 1fr;
    }
}

.content-box {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: var(--border-radius);
    line-height: 1.6;
    height: 150px;
    overflow-y: auto;
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

.timeline {
    position: relative;
    padding-left: 20px;
}

.timeline:before {
    content: '';
    position: absolute;
    left: 6px;
    top: 0;
    bottom: 0;
    width: 2px;
    background-color: var(--light-color);
}

.timeline-item {
    position: relative;
    margin-bottom: 20px;
}

.timeline-dot {
    position: absolute;
    left: -20px;
    top: 5px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background-color: var(--gray-color);
}

.timeline-dot.approved {
    background-color: var(--secondary-color);
}

.timeline-content {
    padding-left: 10px;
}

.timeline-title {
    font-weight: 600;
    color: var(--dark-color);
    margin-bottom: 5px;
}

.timeline-time {
    color: var(--gray-color);
    font-size: 0.9rem;
    margin-bottom: 5px;
}

.timeline-desc {
    color: var(--dark-color);
    line-height: 1.5;
}

.stats-overview {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 15px;
    margin-top: 15px;
}

.stat-card {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 15px;
    background-color: #f8f9fa;
    border-radius: var(--border-radius);
}

.stat-icon {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.stat-icon i {
    font-size: 1.2rem;
}

.stat-content {
    display: flex;
    flex-direction: column;
}

.stat-number {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--dark-color);
}

.stat-label {
    font-size: 0.9rem;
    color: var(--gray-color);
}

.filter-form {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.checkbox-group {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-top: 10px;
}

.checkbox-group label {
    display: flex;
    align-items: center;
    gap: 5px;
    color: var(--dark-color);
    font-size: 0.9rem;
}

.wide-modal {
    max-width: 800px;
}
`;
document.head.appendChild(style);