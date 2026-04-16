// 药房端专用功能

class PharmacyApp {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 10;
        this.totalPages = 1;
        this.currentFilters = {};
        this.selectedPrescriptions = new Set();

        this.prescriptionList = document.getElementById('prescription-list');
        this.loadingState = document.getElementById('loading-state');
        this.emptyState = document.getElementById('empty-state');
        this.pagination = document.getElementById('pagination');
        this.searchInput = document.getElementById('search-input');
        this.warningList = document.getElementById('warning-list');

        this.init();
    }

    init() {
        this.bindEvents();
        this.loadPrescriptions();
        this.loadWarnings();
        this.setupSearch();
    }

    bindEvents() {
        // 刷新按钮
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadPrescriptions();
                this.loadWarnings();
            });
        }

        // 扫码取药按钮
        const scanBtn = document.getElementById('scan-btn');
        if (scanBtn) {
            scanBtn.addEventListener('click', () => {
                window.App.ModalManager.openModal('scan-modal');
            });
        }

        // 手动输入取药码按钮
        const manualDispenseBtn = document.getElementById('manual-dispense-btn');
        if (manualDispenseBtn) {
            manualDispenseBtn.addEventListener('click', () => {
                window.App.ModalManager.openModal('scan-modal');
            });
        }

        // 批量确认按钮
        const batchDispenseBtn = document.getElementById('batch-dispense-btn');
        if (batchDispenseBtn) {
            batchDispenseBtn.addEventListener('click', () => this.batchDispense());
        }

        // 查看库存按钮
        const viewInventoryBtn = document.getElementById('view-inventory-btn');
        if (viewInventoryBtn) {
            viewInventoryBtn.addEventListener('click', () => this.showInventory());
        }

        // 扫码模态框中的确认按钮
        const confirmManualCodeBtn = document.getElementById('confirm-manual-code');
        if (confirmManualCodeBtn) {
            confirmManualCodeBtn.addEventListener('click', () => this.processManualCode());
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

        // 处方详情模态框中的按钮
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('view-prescription-btn')) {
                const prescriptionId = e.target.dataset.prescriptionId;
                this.showPrescriptionDetail(prescriptionId);
            }

            if (e.target.classList.contains('select-prescription')) {
                const prescriptionId = e.target.dataset.prescriptionId;
                this.toggleSelectPrescription(prescriptionId, e.target);
            }
        });

        // 确认配药按钮
        const confirmDispenseBtn = document.getElementById('confirm-dispense-btn');
        if (confirmDispenseBtn) {
            confirmDispenseBtn.addEventListener('click', () => this.confirmDispense());
        }

        // 打印收据按钮
        const printReceiptBtn = document.getElementById('print-receipt-btn');
        if (printReceiptBtn) {
            printReceiptBtn.addEventListener('click', () => window.print());
        }
    }

    setupSearch() {
        if (this.searchInput) {
            // 防抖搜索
            this.searchInput.addEventListener('input', window.App.Utils.debounce(() => {
                this.currentFilters.search = this.searchInput.value.trim();
                this.currentPage = 1;
                this.loadPrescriptions();
            }, 500));
        }
    }

    async loadPrescriptions() {
        this.showLoading(true);

        try {
            // 调用API获取待配药处方列表
            // const data = await window.App.APIService.getPendingDispenses();

            // 模拟数据
            const mockData = [
                {
                    id: 'RX-20250414-001',
                    patient_name: '张三',
                    pickup_code: 'A1B2C3',
                    drugs: [
                        { name: '布洛芬', specification: '200mg/片', quantity: 2, price: 5.00 },
                        { name: '维生素C', specification: '100mg/片', quantity: 1, price: 3.00 }
                    ],
                    total_price: 13.00,
                    created_at: '2026-04-14T10:30:25Z',
                    doctor_name: '王医生',
                    status: 'pending'
                },
                {
                    id: 'RX-20250414-002',
                    patient_name: '李四',
                    pickup_code: 'D4E5F6',
                    drugs: [
                        { name: '阿莫西林', specification: '500mg/粒', quantity: 1, price: 8.00 }
                    ],
                    total_price: 8.00,
                    created_at: '2026-04-14T11:15:10Z',
                    doctor_name: '李医生',
                    status: 'pending'
                },
                {
                    id: 'RX-20250414-003',
                    patient_name: '王五',
                    pickup_code: 'G7H8I9',
                    drugs: [
                        { name: '双氯芬酸钠', specification: '25mg/片', quantity: 3, price: 4.00 },
                        { name: '胃复安', specification: '10mg/片', quantity: 2, price: 3.50 }
                    ],
                    total_price: 19.00,
                    created_at: '2026-04-14T13:45:30Z',
                    doctor_name: '张医生',
                    status: 'pending'
                }
            ];

            this.renderPrescriptionList(mockData);

        } catch (error) {
            console.error('加载处方列表失败:', error);
            this.showError('加载失败，请重试');
        } finally {
            this.showLoading(false);
        }
    }

    renderPrescriptionList(prescriptions) {
        if (!prescriptions || prescriptions.length === 0) {
            this.emptyState.style.display = 'block';
            this.prescriptionList.innerHTML = '';
            this.pagination.style.display = 'none';
            return;
        }

        this.emptyState.style.display = 'none';
        this.prescriptionList.innerHTML = '';

        prescriptions.forEach(prescription => {
            const card = this.createPrescriptionCard(prescription);
            this.prescriptionList.appendChild(card);
        });

        this.updatePagination();
    }

    createPrescriptionCard(prescription) {
        const card = document.createElement('div');
        card.className = 'prescription-card';
        card.innerHTML = `
            <div class="prescription-card-header">
                <div class="checkbox">
                    <input type="checkbox" class="select-prescription"
                           data-prescription-id="${prescription.id}"
                           id="select-${prescription.id}">
                    <label for="select-${prescription.id}"></label>
                </div>
                <div class="prescription-id">处方号: ${prescription.id}</div>
                <div class="prescription-time">${window.App.Utils.formatTime(prescription.created_at)}</div>
            </div>
            <div class="prescription-card-body">
                <div class="patient-info">
                    <h4><i class="fas fa-user"></i> ${prescription.patient_name}</h4>
                    <div class="patient-details">
                        <span>取药码: <strong class="pickup-code">${prescription.pickup_code}</strong></span>
                        <span>审批医生: ${prescription.doctor_name}</span>
                    </div>
                </div>
                <div class="drugs-summary">
                    <h5><i class="fas fa-pills"></i> 药品清单</h5>
                    <ul>
                        ${prescription.drugs.map(drug =>
                            `<li>${drug.name} (${drug.specification}) × ${drug.quantity}</li>`
                        ).join('')}
                    </ul>
                </div>
                <div class="prescription-info">
                    <div class="info-item">
                        <span class="info-label">总金额:</span>
                        <span class="info-value">¥ ${prescription.total_price.toFixed(2)}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">状态:</span>
                        <span class="status-value pending">待配药</span>
                    </div>
                </div>
            </div>
            <div class="prescription-card-footer">
                <button class="btn btn-primary view-prescription-btn" data-prescription-id="${prescription.id}">
                    <i class="fas fa-search"></i> 查看详情并配药
                </button>
            </div>
        `;
        return card;
    }

    async loadWarnings() {
        try {
            // 调用API获取库存预警
            // const warnings = await window.App.APIService.getInventoryWarnings();

            // 模拟数据
            const mockWarnings = [
                { drug_name: '阿莫西林', current_stock: 15, min_threshold: 20 },
                { drug_name: '布洛芬', current_stock: 32, min_threshold: 30 },
                { drug_name: '维生素C', current_stock: 8, min_threshold: 10 }
            ];

            this.renderWarnings(mockWarnings);

        } catch (error) {
            console.error('加载库存预警失败:', error);
        }
    }

    renderWarnings(warnings) {
        if (!warnings || warnings.length === 0) {
            this.warningList.innerHTML = '<p class="no-warning">无库存预警</p>';
            return;
        }

        this.warningList.innerHTML = '';
        warnings.forEach(warning => {
            const level = warning.current_stock < warning.min_threshold ? 'low' :
                         warning.current_stock < warning.min_threshold * 1.5 ? 'medium' : 'normal';

            const warningItem = document.createElement('div');
            warningItem.className = 'warning-item';
            warningItem.innerHTML = `
                <span class="drug-name">${warning.drug_name}</span>
                <span class="stock-level ${level}">库存: ${warning.current_stock}</span>
            `;
            this.warningList.appendChild(warningItem);
        });
    }

    async showPrescriptionDetail(prescriptionId) {
        try {
            window.App.Utils.showLoading(true);

            // 调用API获取处方详情
            // const prescription = await window.App.APIService.getPrescription(prescriptionId);

            // 模拟数据
            const mockPrescription = {
                id: prescriptionId,
                patient_name: '张三',
                pickup_code: 'A1B2C3',
                drugs: [
                    { name: '布洛芬', specification: '200mg/片', quantity: 2, price: 5.00, stock_available: true },
                    { name: '维生素C', specification: '100mg/片', quantity: 1, price: 3.00, stock_available: true }
                ],
                total_price: 13.00,
                created_at: '2026-04-14T10:30:25Z',
                doctor_name: '王医生',
                status: 'pending'
            };

            this.renderPrescriptionDetail(mockPrescription);
            window.App.ModalManager.openModal('prescription-modal');

        } catch (error) {
            console.error('加载处方详情失败:', error);
            window.App.Utils.showNotification('加载详情失败', 'error');
        } finally {
            window.App.Utils.showLoading(false);
        }
    }

    renderPrescriptionDetail(prescription) {
        // 更新处方信息
        document.getElementById('detail-prescription-id').textContent = prescription.id;
        document.getElementById('detail-pickup-code').textContent = prescription.pickup_code;
        document.getElementById('detail-patient-name').textContent = prescription.patient_name;
        document.getElementById('detail-status').textContent = prescription.status === 'pending' ? '待配药' : '已配药';
        document.getElementById('detail-created-at').textContent = window.App.Utils.formatTime(prescription.created_at);
        document.getElementById('detail-doctor').textContent = prescription.doctor_name;

        // 更新药品清单
        const drugsList = document.getElementById('drugs-list');
        drugsList.innerHTML = '';

        prescription.drugs.forEach((drug, index) => {
            const drugItem = document.createElement('div');
            drugItem.className = 'drug-item';
            drugItem.innerHTML = `
                <div class="drug-info">
                    <span class="drug-number">${index + 1}.</span>
                    <span class="drug-name">${drug.name}</span>
                    <span class="drug-spec">${drug.specification}</span>
                </div>
                <div class="drug-details">
                    <span class="drug-quantity">数量: ${drug.quantity}</span>
                    <span class="drug-price">单价: ¥ ${drug.price.toFixed(2)}</span>
                    <span class="drug-total">小计: ¥ ${(drug.quantity * drug.price).toFixed(2)}</span>
                    <span class="stock-status ${drug.stock_available ? 'available' : 'unavailable'}">
                        ${drug.stock_available ? '库存充足' : '库存不足'}
                    </span>
                </div>
            `;
            drugsList.appendChild(drugItem);
        });

        // 更新总数信息
        document.getElementById('detail-drug-count').textContent = prescription.drugs.length;
        document.getElementById('detail-total-price').textContent = `¥ ${prescription.total_price.toFixed(2)}`;

        // 更新库存检查
        const inventoryCheck = document.getElementById('inventory-check');
        const allAvailable = prescription.drugs.every(drug => drug.stock_available);

        if (allAvailable) {
            inventoryCheck.innerHTML = `
                <div class="inventory-status success">
                    <i class="fas fa-check-circle"></i>
                    <span>所有药品库存充足，可以配药</span>
                </div>
            `;
        } else {
            const unavailableDrugs = prescription.drugs.filter(drug => !drug.stock_available);
            inventoryCheck.innerHTML = `
                <div class="inventory-status error">
                    <i class="fas fa-exclamation-circle"></i>
                    <span>以下药品库存不足:</span>
                    <ul>
                        ${unavailableDrugs.map(drug => `<li>${drug.name}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // 清空备注输入框
        document.getElementById('dispense-notes').value = '';
    }

    async confirmDispense() {
        const prescriptionId = document.getElementById('detail-prescription-id').textContent;
        const notes = document.getElementById('dispense-notes').value.trim();

        try {
            window.App.Utils.showLoading(true);

            // 调用API确认配药
            const result = await window.App.APIService.confirmDispense(prescriptionId);

            // 显示结果
            this.showDispenseResult(true, result);

            // 关闭详情模态框
            window.App.ModalManager.closeModal('prescription-modal');

            // 刷新列表和预警
            this.loadPrescriptions();
            this.loadWarnings();

        } catch (error) {
            console.error('配药失败:', error);
            this.showDispenseResult(false, error.message);
        } finally {
            window.App.Utils.showLoading(false);
        }
    }

    showDispenseResult(success, result) {
        const resultContent = document.getElementById('dispense-result-content');

        if (success) {
            resultContent.innerHTML = `
                <div class="result-success">
                    <i class="fas fa-check-circle"></i>
                    <h4>配药成功</h4>
                    <p>✅ 处方 ${result.prescription_id} 已配药完成。</p>
                    <p>取药时间: ${window.App.Utils.formatTime(new Date())}</p>
                    <p>配药药师: 张药师</p>
                    <div class="receipt-info">
                        <h5>收据信息</h5>
                        <p>总金额: ¥ ${result.total_price?.toFixed(2) || '0.00'}</p>
                        <p>支付方式: 医保/自费</p>
                        <p>感谢您的使用！</p>
                    </div>
                </div>
            `;
        } else {
            resultContent.innerHTML = `
                <div class="result-error">
                    <i class="fas fa-times-circle"></i>
                    <h4>配药失败</h4>
                    <p>❌ 配药过程中出现错误。</p>
                    <p>错误信息: ${result}</p>
                    <p>请检查库存或联系系统管理员。</p>
                </div>
            `;
        }

        window.App.ModalManager.openModal('dispense-result-modal');
    }

    processManualCode() {
        const codeInput = document.getElementById('manual-code-input');
        const code = codeInput.value.trim();

        if (!code || code.length !== 6) {
            window.App.Utils.showNotification('请输入6位取药码', 'warning');
            return;
        }

        // 模拟通过取药码查找处方
        window.App.Utils.showNotification(`正在查找取药码 ${code} 对应的处方...`, 'info');

        // 这里应该调用API通过取药码查找处方
        // 暂时模拟
        setTimeout(() => {
            const mockPrescriptionId = 'RX-20250414-001';
            this.showPrescriptionDetail(mockPrescriptionId);
            window.App.ModalManager.closeModal('scan-modal');
            codeInput.value = '';
        }, 1000);
    }

    toggleSelectPrescription(prescriptionId, checkbox) {
        if (checkbox.checked) {
            this.selectedPrescriptions.add(prescriptionId);
        } else {
            this.selectedPrescriptions.delete(prescriptionId);
        }

        // 更新批量确认按钮状态
        const batchBtn = document.getElementById('batch-dispense-btn');
        if (batchBtn) {
            batchBtn.disabled = this.selectedPrescriptions.size === 0;
        }
    }

    async batchDispense() {
        if (this.selectedPrescriptions.size === 0) {
            window.App.Utils.showNotification('请选择至少一个处方', 'warning');
            return;
        }

        if (!confirm(`确定要批量配药 ${this.selectedPrescriptions.size} 个处方吗？`)) {
            return;
        }

        try {
            window.App.Utils.showLoading(true);

            // 调用API批量配药
            // 暂时模拟
            await new Promise(resolve => setTimeout(resolve, 2000));

            window.App.Utils.showNotification(`成功配药 ${this.selectedPrescriptions.size} 个处方`, 'success');

            // 清空选择
            this.selectedPrescriptions.clear();
            document.querySelectorAll('.select-prescription').forEach(cb => {
                cb.checked = false;
            });

            // 刷新列表
            this.loadPrescriptions();
            this.loadWarnings();

        } catch (error) {
            console.error('批量配药失败:', error);
            window.App.Utils.showNotification('批量配药失败: ' + error.message, 'error');
        } finally {
            window.App.Utils.showLoading(false);
        }
    }

    async showInventory() {
        try {
            window.App.Utils.showLoading(true);

            // 调用API获取库存列表
            // const inventory = await window.App.APIService.getDrugs();

            // 模拟数据
            const mockInventory = [
                { name: '阿莫西林', specification: '500mg/粒', stock: 15, min_threshold: 20, status: 'low' },
                { name: '布洛芬', specification: '200mg/片', stock: 32, min_threshold: 30, status: 'medium' },
                { name: '维生素C', specification: '100mg/片', stock: 8, min_threshold: 10, status: 'low' },
                { name: '双氯芬酸钠', specification: '25mg/片', stock: 45, min_threshold: 20, status: 'normal' },
                { name: '胃复安', specification: '10mg/片', stock: 25, min_threshold: 15, status: 'normal' },
                { name: '头孢克肟', specification: '100mg/粒', stock: 18, min_threshold: 15, status: 'normal' }
            ];

            this.renderInventory(mockInventory);
            window.App.ModalManager.openModal('inventory-modal');

        } catch (error) {
            console.error('加载库存失败:', error);
            window.App.Utils.showNotification('加载库存失败', 'error');
        } finally {
            window.App.Utils.showLoading(false);
        }
    }

    renderInventory(inventory) {
        const inventoryBody = document.getElementById('inventory-body');
        inventoryBody.innerHTML = '';

        inventory.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.name}</td>
                <td>${item.specification}</td>
                <td class="${item.status === 'low' ? 'low-stock' : item.status === 'medium' ? 'medium-stock' : ''}">
                    ${item.stock}
                </td>
                <td>${item.min_threshold}</td>
                <td>
                    <span class="status-badge ${item.status}">
                        ${item.status === 'low' ? '库存不足' : item.status === 'medium' ? '库存预警' : '库存正常'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-primary" data-drug="${item.name}">补货</button>
                </td>
            `;
            inventoryBody.appendChild(row);
        });
    }

    changePage(delta) {
        const newPage = this.currentPage + delta;
        if (newPage < 1 || newPage > this.totalPages) return;

        this.currentPage = newPage;
        this.loadPrescriptions();
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
        this.prescriptionList.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>加载失败</h3>
                <p>${message}</p>
                <button class="btn btn-primary" onclick="window.pharmacyApp.loadPrescriptions()">重试</button>
            </div>
        `;
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    // 检查是否在药房页面
    if (document.getElementById('prescription-list')) {
        window.pharmacyApp = new PharmacyApp();
    }
});

// 添加一些额外的CSS样式
const style = document.createElement('style');
style.textContent = `
.prescription-card {
    background-color: white;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
    margin-bottom: 20px;
    overflow: hidden;
    transition: var(--transition);
}

.prescription-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-hover);
}

.prescription-card-header {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 15px 20px;
    background-color: #f8f9fa;
    border-bottom: 1px solid var(--light-color);
}

.checkbox {
    display: flex;
    align-items: center;
}

.checkbox input[type="checkbox"] {
    display: none;
}

.checkbox label {
    width: 20px;
    height: 20px;
    border: 2px solid var(--gray-color);
    border-radius: 4px;
    cursor: pointer;
    position: relative;
}

.checkbox input[type="checkbox"]:checked + label {
    background-color: var(--primary-color);
    border-color: var(--primary-color);
}

.checkbox input[type="checkbox"]:checked + label:after {
    content: '✓';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: white;
    font-weight: bold;
}

.prescription-id {
    font-weight: 600;
    color: var(--dark-color);
    flex: 1;
}

.prescription-time {
    color: var(--gray-color);
    font-size: 0.9rem;
}

.prescription-card-body {
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

.pickup-code {
    color: var(--primary-color);
    font-weight: 600;
    font-family: monospace;
    letter-spacing: 1px;
}

.drugs-summary {
    margin-bottom: 15px;
}

.drugs-summary h5 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 5px;
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

.prescription-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 15px;
    border-top: 1px solid var(--light-color);
}

.info-item {
    display: flex;
    align-items: center;
    gap: 8px;
}

.info-label {
    color: var(--gray-color);
}

.info-value {
    font-weight: 600;
    color: var(--dark-color);
}

.status-value {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 600;
}

.status-value.pending {
    background-color: #fff3cd;
    color: #856404;
}

.status-value.dispensed {
    background-color: #d4edda;
    color: #155724;
}

.prescription-card-footer {
    padding: 15px 20px;
    background-color: #f8f9fa;
    border-top: 1px solid var(--light-color);
    text-align: right;
}

.quick-actions {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}

.scan-container {
    text-align: center;
}

.scanner-placeholder {
    padding: 30px;
    background-color: #f8f9fa;
    border-radius: var(--border-radius);
    margin-bottom: 20px;
}

.scanner-placeholder i {
    font-size: 4rem;
    color: var(--gray-light);
    margin-bottom: 15px;
}

.scanner-frame {
    width: 200px;
    height: 200px;
    border: 2px dashed var(--primary-color);
    margin: 20px auto;
    position: relative;
}

.scanner-frame:before, .scanner-frame:after {
    content: '';
    position: absolute;
    width: 20px;
    height: 20px;
    border: 2px solid var(--primary-color);
}

.scanner-frame:before {
    top: 0;
    left: 0;
    border-right: none;
    border-bottom: none;
}

.scanner-frame:after {
    bottom: 0;
    right: 0;
    border-left: none;
    border-top: none;
}

.scan-input {
    margin-top: 20px;
}

.scan-input input {
    width: 200px;
    padding: 10px;
    font-size: 1.2rem;
    text-align: center;
    letter-spacing: 3px;
    margin: 10px;
}

.wide-modal {
    max-width: 800px;
}

.warning-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid var(--light-color);
}

.warning-item:last-child {
    border-bottom: none;
}

.stock-level {
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.9rem;
    font-weight: 600;
}

.stock-level.low {
    background-color: #f8d7da;
    color: #721c24;
}

.stock-level.medium {
    background-color: #fff3cd;
    color: #856404;
}

.stock-level.normal {
    background-color: #d4edda;
    color: #155724;
}

.drug-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px;
    background-color: #f8f9fa;
    border-radius: var(--border-radius);
    margin-bottom: 10px;
}

.drug-info {
    display: flex;
    align-items: center;
    gap: 15px;
}

.drug-number {
    font-weight: 600;
    color: var(--gray-color);
}

.drug-name {
    font-weight: 600;
    color: var(--dark-color);
}

.drug-spec {
    color: var(--gray-color);
    font-size: 0.9rem;
}

.drug-details {
    display: flex;
    align-items: center;
    gap: 20px;
}

.stock-status {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 600;
}

.stock-status.available {
    background-color: #d4edda;
    color: #155724;
}

.stock-status.unavailable {
    background-color: #f8d7da;
    color: #721c24;
}

.inventory-status {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 15px;
    border-radius: var(--border-radius);
}

.inventory-status.success {
    background-color: #d4edda;
    color: #155724;
}

.inventory-status.error {
    background-color: #f8d7da;
    color: #721c24;
}

.inventory-status i {
    font-size: 1.2rem;
    margin-top: 2px;
}

.total-info {
    display: flex;
    justify-content: space-between;
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid var(--light-color);
}

.low-stock {
    color: var(--danger-color);
    font-weight: 600;
}

.medium-stock {
    color: var(--warning-color);
    font-weight: 600;
}

.status-badge {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.9rem;
    font-weight: 600;
}

.status-badge.low {
    background-color: #f8d7da;
    color: #721c24;
}

.status-badge.medium {
    background-color: #fff3cd;
    color: #856404;
}

.status-badge.normal {
    background-color: #d4edda;
    color: #155724;
}
`;
document.head.appendChild(style);