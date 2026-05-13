/**
 * 智能药品管理系统 - UI 工具函数
 * 页面渲染辅助、Modal、日期格式化等
 */

/* ===== 日期/时间格式化 ===== */
function formatTime(isoString) {
    if (!isoString) return '-';
    try {
        const d = new Date(isoString);
        const pad = n => String(n).padStart(2, '0');
        return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    } catch { return isoString; }
}

function timeAgo(isoString) {
    if (!isoString) return '-';
    try {
        const diff = Date.now() - new Date(isoString).getTime();
        const sec = Math.floor(diff / 1000);
        if (sec < 60) return '刚刚';
        const min = Math.floor(sec / 60);
        if (min < 60) return `${min}分钟前`;
        const hr = Math.floor(min / 60);
        if (hr < 24) return `${hr}小时前`;
        return `${Math.floor(hr / 24)}天前`;
    } catch { return isoString; }
}

/* ===== Modal 辅助 ===== */
function openModal(title, bodyHtml, footerHtml = '') {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
        <div class="modal-box">
            <div class="modal-header">
                <span>${title}</span>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
            </div>
            <div class="modal-body">${bodyHtml}</div>
            ${footerHtml ? `<div class="modal-footer">${footerHtml}</div>` : ''}
        </div>
    `;
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) overlay.remove();
    });
    document.body.appendChild(overlay);
    return overlay;
}

/* ===== 页面渲染辅助 ===== */
function setPageHeader(title) {
    const el = document.getElementById('pageTitle');
    if (el) el.textContent = title;
}

function renderSidebar(navItems, currentPage) {
    let html = '';
    for (const section of navItems) {
        html += `<div class="nav-section">${section.label}</div>`;
        for (const item of section.items) {
            const cls = item.page === currentPage ? 'active' : '';
            html += `<a href="${item.href}" class="${cls}"><i class="${item.icon}"></i>${item.label}</a>`;
        }
    }
    return html;
}

/* ===== 审批状态轮询 ===== */
function pollApprovalStatus(approvalId, onUpdate, interval = 3000, maxAttempts = 60) {
    let attempts = 0;
    const timer = setInterval(async () => {
        attempts++;
        const result = await ApiClient.getApproval(approvalId);
        if (result.success) {
            onUpdate(result.approval);
            if (result.approval.status !== 'pending' || attempts >= maxAttempts) {
                clearInterval(timer);
            }
        }
        if (attempts >= maxAttempts) clearInterval(timer);
    }, interval);
    return timer;
}

/* ===== 任务状态映射 ===== */
const TASK_STATE_LABELS = { 0: '待执行', 1: '执行中', 2: '已完成', 3: '失败' };
const TASK_STATE_COLORS = { 0: 'badge-pending', 1: 'badge-warning', 2: 'badge-approved', 3: 'badge-danger' };
