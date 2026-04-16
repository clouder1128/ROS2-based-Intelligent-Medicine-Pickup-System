// 管理员端专用功能

class AdminApp {
    constructor() {
        this.chartData = {
            prescriptions: [],
            drugTypes: []
        };

        this.init();
    }

    init() {
        this.bindEvents();
        this.loadDashboardData();
        this.loadInventoryWarnings();
        this.loadRecentActivities();
        this.setupCharts();
    }

    bindEvents() {
        // 快速操作按钮
        const addDrugBtn = document.getElementById('add-drug-btn');
        if (addDrugBtn) {
            addDrugBtn.addEventListener('click', () => {
                window.App.ModalManager.openModal('add-drug-modal');
            });
        }

        const generateReportBtn = document.getElementById('generate-report-btn');
        if (generateReportBtn) {
            generateReportBtn.addEventListener('click', () => {
                window.App.ModalManager.openModal('report-modal');
            });
        }

        const viewAlertsBtn = document.getElementById('view-alerts-btn');
        if (viewAlertsBtn) {
            viewAlertsBtn.addEventListener('click', () => {
                window.App.ModalManager.openModal('alerts-modal');
                this.loadAlerts();
            });
        }

        const backupSystemBtn = document.getElementById('backup-system-btn');
        if (backupSystemBtn) {
            backupSystemBtn.addEventListener('click', () => {
                window.App.ModalManager.openModal('backup-modal');
            });
        }

        // 图表周期选择
        const chartPeriod = document.getElementById('chart-period');
        if (chartPeriod) {
            chartPeriod.addEventListener('change', () => {
                this.loadChartData(chartPeriod.value);
            });
        }

        // 管理库存按钮
        const manageInventoryBtn = document.getElementById('manage-inventory-btn');
        if (manageInventoryBtn) {
            manageInventoryBtn.addEventListener('click', () => {
                window.location.href = 'admin-drugs.html';
            });
        }

        // 查看全部活动按钮
        const viewAllActivitiesBtn = document.getElementById('view-all-activities-btn');
        if (viewAllActivitiesBtn) {
            viewAllActivitiesBtn.addEventListener('click', () => {
                window.location.href = 'admin-users.html';
            });
        }

        // 添加药品表单提交
        const submitAddDrugBtn = document.getElementById('submit-add-drug-btn');
        if (submitAddDrugBtn) {
            submitAddDrugBtn.addEventListener('click', () => this.addNewDrug());
        }

        // 生成报告按钮
        const generateReportNowBtn = document.getElementById('generate-report-now-btn');
        if (generateReportNowBtn) {
            generateReportNowBtn.addEventListener('click', () => this.generateReport());
        }

        // 开始备份按钮
        const startBackupBtn = document.getElementById('start-backup-btn');
        if (startBackupBtn) {
            startBackupBtn.addEventListener('click', () => this.startBackup());
        }

        // 标记所有警报为已读
        const markAllReadBtn = document.getElementById('mark-all-read-btn');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => this.markAllAlertsRead());
        }
    }

    async loadDashboardData() {
        try {
            // 调用API获取仪表板数据
            // const data = await window.App.APIService.getDashboardStats();

            // 模拟数据
            const mockData = {
                total_prescriptions: 1245,
                active_doctors: 24,
                total_drugs: 156,
                approval_rate: 98.5,
                prescription_trend: [45, 52, 48, 55, 58, 62, 65],
                drug_type_distribution: [
                    { type: 'prescription', count: 120, percentage: 77 },
                    { type: 'otc', count: 36, percentage: 23 }
                ]
            };

            this.updateOverviewCards(mockData);
            this.chartData.prescriptions = mockData.prescription_trend;
            this.chartData.drugTypes = mockData.drug_type_distribution;
            this.updateCharts();

        } catch (error) {
            console.error('加载仪表板数据失败:', error);
            window.App.Utils.showNotification('加载仪表板数据失败', 'error');
        }
    }

    updateOverviewCards(data) {
        document.getElementById('total-prescriptions').textContent = data.total_prescriptions.toLocaleString();
        document.getElementById('active-doctors').textContent = data.active_doctors;
        document.getElementById('total-drugs').textContent = data.total_drugs;
        document.getElementById('approval-rate').textContent = `${data.approval_rate}%`;
    }

    setupCharts() {
        // 初始化图表
        this.loadChartData('7days');
    }

    async loadChartData(period) {
        try {
            // 根据周期加载图表数据
            let mockData;
            if (period === '7days') {
                mockData = [45, 52, 48, 55, 58, 62, 65];
            } else if (period === '30days') {
                mockData = Array.from({length: 30}, (_, i) => 40 + Math.floor(Math.random() * 30));
            } else {
                mockData = Array.from({length: 90}, (_, i) => 35 + Math.floor(Math.random() * 40));
            }

            this.chartData.prescriptions = mockData;
            this.updatePrescriptionChart();

        } catch (error) {
            console.error('加载图表数据失败:', error);
        }
    }

    updatePrescriptionChart() {
        const chartData = this.chartData.prescriptions;
        const maxValue = Math.max(...chartData);
        const chartBody = document.getElementById('chart-data');

        chartBody.innerHTML = '';
        chartData.forEach((value, index) => {
            const percentage = (value / maxValue) * 100;
            const row = document.createElement('tr');
            row.style.setProperty('--size', `${percentage}%`);
            row.innerHTML = `<th scope="row">第${index + 1}天</th>`;
            chartBody.appendChild(row);
        });

        // 更新图表标题
        const chart = document.getElementById('prescription-chart');
        if (chart) {
            chart.querySelector('caption').textContent = `每日处方量统计 (最大值: ${maxValue})`;
        }
    }

    updateCharts() {
        this.updatePrescriptionChart();
        this.updateDrugTypeChart();
    }

    updateDrugTypeChart() {
        const pieData = this.chartData.drugTypes;
        const pieBody = document.getElementById('pie-data');

        pieBody.innerHTML = '';
        pieData.forEach(item => {
            const row = document.createElement('tr');
            row.style.setProperty('--start', '0');
            row.style.setProperty('--end', `${item.percentage}%`);
            row.innerHTML = `<th scope="row">${item.type === 'prescription' ? '处方药' : '非处方药'}</th>`;
            pieBody.appendChild(row);
        });
    }

    async loadInventoryWarnings() {
        try {
            // 调用API获取库存预警
            // const warnings = await window.App.APIService.getPurchaseSuggestions();

            // 模拟数据
            const mockWarnings = [
                {
                    drug_name: '阿莫西林',
                    specification: '500mg/粒',
                    current_stock: 15,
                    min_threshold: 20,
                    daily_avg_out: 5,
                    suggested: 80,
                    days_left: 3
                },
                {
                    drug_name: '布洛芬',
                    specification: '200mg/片',
                    current_stock: 32,
                    min_threshold: 30,
                    daily_avg_out: 8,
                    suggested: 100,
                    days_left: 4
                },
                {
                    drug_name: '维生素C',
                    specification: '100mg/片',
                    current_stock: 8,
                    min_threshold: 10,
                    daily_avg_out: 3,
                    suggested: 50,
                    days_left: 2
                }
            ];

            this.renderInventoryWarnings(mockWarnings);

        } catch (error) {
            console.error('加载库存预警失败:', error);
        }
    }

    renderInventoryWarnings(warnings) {
        const tableBody = document.getElementById('inventory-warning-body');
        tableBody.innerHTML = '';

        warnings.forEach(warning => {
            const daysLeft = warning.days_left;
            const rowClass = daysLeft < 3 ? 'warning-high' : daysLeft < 7 ? 'warning-medium' : '';

            const row = document.createElement('tr');
            if (rowClass) row.className = rowClass;

            row.innerHTML = `
                <td>${warning.drug_name}</td>
                <td>${warning.specification}</td>
                <td class="${warning.current_stock < warning.min_threshold ? 'low-stock' : ''}">
                    ${warning.current_stock}
                </td>
                <td>${warning.min_threshold}</td>
                <td>${warning.daily_avg_out}</td>
                <td>
                    <span class="days-left ${daysLeft < 3 ? 'danger' : daysLeft < 7 ? 'warning' : 'normal'}">
                        ${daysLeft} 天
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-primary" data-drug="${warning.drug_name}">
                        立即补货
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        });

        // 添加补货按钮事件
        tableBody.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const drugName = e.target.dataset.drug;
                this.replenishDrug(drugName);
            });
        });
    }

    async loadRecentActivities() {
        try {
            // 调用API获取最近活动
            // const activities = await window.App.APIService.getRecentActivities();

            // 模拟数据
            const mockActivities = [
                {
                    timestamp: '2026-04-14T14:30:25Z',
                    user: '王医生',
                    action: '批准处方',
                    details: '处方 RX-20250414-005',
                    status: 'success'
                },
                {
                    timestamp: '2026-04-14T13:45:10Z',
                    user: '张药师',
                    action: '配药完成',
                    details: '取药码 A1B2C3',
                    status: 'success'
                },
                {
                    timestamp: '2026-04-14T12:20:30Z',
                    user: '系统',
                    action: '库存预警',
                    details: '阿莫西林库存低于预警线',
                    status: 'warning'
                },
                {
                    timestamp: '2026-04-14T11:15:45Z',
                    user: '李医生',
                    action: '拒绝处方',
                    details: '患者过敏史不符',
                    status: 'error'
                },
                {
                    timestamp: '2026-04-14T10:05:20Z',
                    user: '管理员',
                    action: '添加药品',
                    details: '新增药品: 头孢克肟',
                    status: 'success'
                }
            ];

            this.renderRecentActivities(mockActivities);

        } catch (error) {
            console.error('加载最近活动失败:', error);
        }
    }

    renderRecentActivities(activities) {
        const tableBody = document.getElementById('recent-activities-body');
        tableBody.innerHTML = '';

        activities.forEach(activity => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${window.App.Utils.formatTime(activity.timestamp)}</td>
                <td>${activity.user}</td>
                <td>${activity.action}</td>
                <td>${activity.details}</td>
                <td>
                    <span class="status-badge ${activity.status}">
                        ${activity.status === 'success' ? '成功' :
                          activity.status === 'warning' ? '警告' : '错误'}
                    </span>
                </td>
            `;
            tableBody.appendChild(row);
        });
    }

    async loadAlerts() {
        try {
            // 调用API获取系统警报
            // const alerts = await window.App.APIService.getSystemAlerts();

            // 模拟数据
            const mockAlerts = [
                {
                    id: 1,
                    type: 'warning',
                    title: '数据库连接缓慢',
                    message: '数据库查询响应时间超过阈值',
                    timestamp: '2026-04-14T14:30:25Z',
                    read: false
                },
                {
                    id: 2,
                    type: 'error',
                    title: '药房API连接失败',
                    message: '无法连接到药房仿真系统',
                    timestamp: '2026-04-14T13:15:10Z',
                    read: false
                },
                {
                    id: 3,
                    type: 'info',
                    title: '系统备份完成',
                    message: '每日自动备份已完成',
                    timestamp: '2026-04-14T03:00:00Z',
                    read: true
                }
            ];

            this.renderAlerts(mockAlerts);

        } catch (error) {
            console.error('加载警报失败:', error);
        }
    }

    renderAlerts(alerts) {
        const alertsList = document.getElementById('alerts-list');
        alertsList.innerHTML = '';

        if (alerts.length === 0) {
            alertsList.innerHTML = '<p class="no-alerts">暂无系统警报</p>';
            return;
        }

        alerts.forEach(alert => {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert-item ${alert.type} ${alert.read ? 'read' : 'unread'}`;
            alertDiv.innerHTML = `
                <div class="alert-icon">
                    <i class="fas fa-${alert.type === 'warning' ? 'exclamation-triangle' :
                                        alert.type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                </div>
                <div class="alert-content">
                    <div class="alert-title">${alert.title}</div>
                    <div class="alert-message">${alert.message}</div>
                    <div class="alert-time">${window.App.Utils.formatTime(alert.timestamp)}</div>
                </div>
                ${!alert.read ? '<div class="alert-badge">NEW</div>' : ''}
            `;
            alertsList.appendChild(alertDiv);
        });
    }

    async addNewDrug() {
        const form = document.getElementById('add-drug-form');
        if (!form.checkValidity()) {
            window.App.Utils.showNotification('请填写所有必填字段', 'warning');
            return;
        }

        const drugData = {
            name: document.getElementById('drug-name').value,
            specification: document.getElementById('drug-specification').value,
            price: parseFloat(document.getElementById('drug-price').value),
            stock: parseInt(document.getElementById('drug-stock').value),
            is_prescription: document.getElementById('drug-type').value === 'prescription',
            min_stock_threshold: parseInt(document.getElementById('min-stock').value),
            description: document.getElementById('drug-description').value,
            category: document.getElementById('drug-category').value
        };

        try {
            window.App.Utils.showLoading(true);

            // 调用API添加药品
            // const result = await window.App.APIService.addDrug(drugData);

            // 模拟成功
            await new Promise(resolve => setTimeout(resolve, 1000));

            window.App.Utils.showNotification(`药品 "${drugData.name}" 添加成功`, 'success');
            window.App.ModalManager.closeModal('add-drug-modal');
            form.reset();

            // 刷新数据
            this.loadDashboardData();
            this.loadInventoryWarnings();

        } catch (error) {
            console.error('添加药品失败:', error);
            window.App.Utils.showNotification('添加药品失败: ' + error.message, 'error');
        } finally {
            window.App.Utils.showLoading(false);
        }
    }

    async generateReport() {
        const reportType = document.getElementById('report-type').value;
        const reportMonth = document.getElementById('report-month').value;
        const reportFormat = document.getElementById('report-format').value;
        const email = document.getElementById('report-email').value;

        window.App.Utils.showLoading(true);
        window.App.Utils.showNotification(`正在生成${reportType}报告...`, 'info');

        try {
            // 模拟报告生成过程
            await new Promise(resolve => setTimeout(resolve, 2000));

            window.App.Utils.showNotification('报告生成成功！', 'success');
            window.App.ModalManager.closeModal('report-modal');

            if (email) {
                window.App.Utils.showNotification(`报告已发送到 ${email}`, 'info');
            }

        } catch (error) {
            console.error('生成报告失败:', error);
            window.App.Utils.showNotification('生成报告失败: ' + error.message, 'error');
        } finally {
            window.App.Utils.showLoading(false);
        }
    }

    async startBackup() {
        const description = document.getElementById('backup-description').value;

        window.App.Utils.showLoading(true);
        window.App.Utils.showNotification('系统备份中，请稍候...', 'info');

        try {
            // 模拟备份过程
            await new Promise(resolve => setTimeout(resolve, 3000));

            window.App.Utils.showNotification('系统备份完成！', 'success');
            window.App.ModalManager.closeModal('backup-modal');

            // 更新备份时间显示
            const now = new Date();
            document.getElementById('last-backup-time').textContent = window.App.Utils.formatTime(now);

        } catch (error) {
            console.error('备份失败:', error);
            window.App.Utils.showNotification('备份失败: ' + error.message, 'error');
        } finally {
            window.App.Utils.showLoading(false);
        }
    }

    async replenishDrug(drugName) {
        if (!confirm(`确定要为药品 "${drugName}" 进行补货吗？`)) {
            return;
        }

        try {
            window.App.Utils.showLoading(true);

            // 调用API进行补货
            // await window.App.APIService.replenishDrug(drugName);

            // 模拟成功
            await new Promise(resolve => setTimeout(resolve, 1000));

            window.App.Utils.showNotification(`药品 "${drugName}" 补货请求已提交`, 'success');
            this.loadInventoryWarnings();

        } catch (error) {
            console.error('补货失败:', error);
            window.App.Utils.showNotification('补货失败: ' + error.message, 'error');
        } finally {
            window.App.Utils.showLoading(false);
        }
    }

    markAllAlertsRead() {
        const alertItems = document.querySelectorAll('.alert-item.unread');
        alertItems.forEach(item => {
            item.classList.remove('unread');
            item.classList.add('read');
            const badge = item.querySelector('.alert-badge');
            if (badge) badge.remove();
        });

        window.App.Utils.showNotification('所有警报已标记为已读', 'success');
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    // 检查是否在管理员页面
    if (document.getElementById('total-prescriptions')) {
        window.adminApp = new AdminApp();
    }
});

// 添加一些额外的CSS样式
const style = document.createElement('style');
style.textContent = `
.dashboard {
    display: flex;
    flex-direction: column;
    gap: 30px;
}

.overview-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
}

.overview-card {
    background-color: white;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
    padding: 25px;
    display: flex;
    align-items: center;
    gap: 20px;
    transition: var(--transition);
}

.overview-card:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-hover);
}

.card-icon {
    width: 60px;
    height: 60px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.card-icon i {
    font-size: 1.8rem;
}

.card-content {
    flex: 1;
}

.card-number {
    font-size: 2rem;
    font-weight: 700;
    color: var(--dark-color);
    margin-bottom: 5px;
}

.card-label {
    font-size: 0.9rem;
    color: var(--gray-color);
    margin-bottom: 8px;
}

.card-change {
    font-size: 0.85rem;
    font-weight: 600;
}

.card-change.positive {
    color: var(--secondary-color);
}

.card-change.negative {
    color: var(--danger-color);
}

.chart-section {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
}

@media (max-width: 1024px) {
    .chart-section {
        grid-template-columns: 1fr;
    }
}

.chart-card {
    background-color: white;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
    padding: 25px;
}

.chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.chart-header h3 {
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--dark-color);
}

.chart-container {
    height: 300px;
    position: relative;
}

.table-section {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

@media (max-width: 1024px) {
    .table-section {
        grid-template-columns: 1fr;
    }
}

.table-card {
    background-color: white;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
    padding: 25px;
}

.table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.table-header h3 {
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--dark-color);
}

.quick-actions-section {
    background-color: white;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
    padding: 25px;
}

.quick-actions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-top: 20px;
}

.quick-action-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding: 25px 15px;
    background-color: #f8f9fa;
    border: 2px solid transparent;
    border-radius: var(--border-radius);
    color: var(--dark-color);
    font-weight: 500;
    cursor: pointer;
    transition: var(--transition);
}

.quick-action-btn:hover {
    background-color: white;
    border-color: var(--primary-color);
    color: var(--primary-color);
    transform: translateY(-2px);
}

.quick-action-btn i {
    font-size: 2rem;
}

.low-stock {
    color: var(--danger-color);
    font-weight: 600;
}

.days-left {
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 600;
}

.days-left.danger {
    background-color: #f8d7da;
    color: #721c24;
}

.days-left.warning {
    background-color: #fff3cd;
    color: #856404;
}

.days-left.normal {
    background-color: #d4edda;
    color: #155724;
}

.status-badge {
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
}

.status-badge.success {
    background-color: #d4edda;
    color: #155724;
}

.status-badge.warning {
    background-color: #fff3cd;
    color: #856404;
}

.status-badge.error {
    background-color: #f8d7da;
    color: #721c24;
}

tr.warning-high {
    background-color: #fff5f5;
}

tr.warning-medium {
    background-color: #fffbf0;
}

.form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
}

@media (max-width: 768px) {
    .form-row {
        grid-template-columns: 1fr;
    }
}

.alert-item {
    display: flex;
    align-items: flex-start;
    gap: 15px;
    padding: 15px;
    border-radius: var(--border-radius);
    margin-bottom: 10px;
    background-color: #f8f9fa;
    border-left: 4px solid var(--gray-color);
    transition: var(--transition);
}

.alert-item.warning {
    border-left-color: var(--warning-color);
}

.alert-item.error {
    border-left-color: var(--danger-color);
}

.alert-item.info {
    border-left-color: var(--primary-color);
}

.alert-item.unread {
    background-color: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.alert-icon {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background-color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.alert-icon i {
    font-size: 1.2rem;
}

.alert-item.warning .alert-icon i {
    color: var(--warning-color);
}

.alert-item.error .alert-icon i {
    color: var(--danger-color);
}

.alert-item.info .alert-icon i {
    color: var(--primary-color);
}

.alert-content {
    flex: 1;
}

.alert-title {
    font-weight: 600;
    color: var(--dark-color);
    margin-bottom: 5px;
}

.alert-message {
    color: var(--gray-color);
    font-size: 0.9rem;
    margin-bottom: 5px;
}

.alert-time {
    color: var(--gray-light);
    font-size: 0.8rem;
}

.alert-badge {
    background-color: var(--danger-color);
    color: white;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 0.7rem;
    font-weight: 600;
    align-self: flex-start;
}

.backup-info {
    margin-bottom: 25px;
}

.backup-options {
    border-top: 1px solid var(--light-color);
    padding-top: 25px;
}

.checkbox-group {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 10px;
    margin: 15px 0;
}

.checkbox-group label {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--dark-color);
    font-size: 0.9rem;
}

.no-alerts {
    text-align: center;
    padding: 40px;
    color: var(--gray-color);
    font-style: italic;
}
`;
document.head.appendChild(style);