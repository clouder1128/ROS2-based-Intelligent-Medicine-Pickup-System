/**
 * 智能药品管理系统 - 工具函数
 */

/* ===== 认证管理 ===== */
const DEMO_USERS = {
    patient1: { password: '123456', role: 'patient', name: '张患者', id: 'patient1' },
    patient2: { password: '123456', role: 'patient', name: '李患者', id: 'patient2' },
    doctor1:  { password: '123456', role: 'doctor', name: '王医生', id: 'doctor1' },
    doctor2:  { password: '123456', role: 'doctor', name: '赵医生', id: 'doctor2' },
    admin1:   { password: '123456', role: 'admin', name: '陈管理员', id: 'admin1' },
};

function doLogin(username, password) {
    const user = DEMO_USERS[username];
    if (!user || user.password !== password) {
        return null;
    }
    const session = { ...user };
    delete session.password;
    session.loginTime = new Date().toISOString();
    sessionStorage.setItem('currentUser', JSON.stringify(session));
    return session;
}

function doLogout() {
    sessionStorage.removeItem('currentUser');
    window.location.href = 'index.html';
}

function getCurrentUser() {
    try {
        const data = sessionStorage.getItem('currentUser');
        return data ? JSON.parse(data) : null;
    } catch { return null; }
}

function requireAuth(expectedRole) {
    const user = getCurrentUser();
    if (!user) {
        window.location.href = 'index.html';
        return null;
    }
    if (expectedRole && user.role !== expectedRole) {
        window.location.href = `${user.role}.html`;
        return null;
    }
    return user;
}

function getUserDisplay(user) {
    if (!user) return '';
    const roleMap = { patient: '患者', doctor: '医生', admin: '管理员' };
    return `${user.name} (${roleMap[user.role] || user.role})`;
}

/* ===== Toast 通知 ===== */
function showToast(message, type = 'info', duration = 3000) {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

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

/* ===== 症状关键词匹配（客户端模拟 P1 agent 逻辑） ===== */
const SYMPTOM_DRUG_MAP = {
    '头痛': ['布洛芬', '阿司匹林'],
    '偏头痛': ['布洛芬'],
    '发热': ['布洛芬', '对乙酰氨基酚'],
    '发烧': ['布洛芬', '对乙酰氨基酚'],
    '咳嗽': ['头孢克肟'],
    '感冒': ['维生素C', '布洛芬'],
    '过敏': ['氯雷他定', '西替利嗪'],
    '感染': ['阿莫西林', '头孢克肟', '阿奇霉素'],
    '炎症': ['布洛芬'],
    '疼痛': ['布洛芬', '阿司匹林'],
    '牙痛': ['布洛芬'],
    '咽喉痛': ['阿莫西林'],
    '流鼻涕': ['氯雷他定'],
    '鼻塞': ['氯雷他定'],
    '乏力': ['维生素C'],
    '维生素缺乏': ['维生素C'],
};

function extractSymptoms(text) {
    const found = [];
    for (const keyword of Object.keys(SYMPTOM_DRUG_MAP)) {
        if (text.includes(keyword)) {
            found.push(keyword);
        }
    }
    return [...new Set(found)];
}

function matchDrugsForSymptoms(symptoms) {
    const drugNames = new Set();
    for (const s of symptoms) {
        const names = SYMPTOM_DRUG_MAP[s] || [];
        names.forEach(n => drugNames.add(n));
    }
    return [...drugNames];
}

function filterAvailableDrugs(drugNames, allDrugs) {
    const available = [];
    for (const name of drugNames) {
        const match = allDrugs.find(d => d.name === name && d.quantity > 0 && d.expiry_date > 0);
        if (match) available.push(match);
    }
    return available;
}

function generateAdviceText(drug, symptoms, patientInfo) {
    const lines = [];
    lines.push(`【用药建议】`);
    lines.push(`推荐药品: ${drug.name}`);
    lines.push(`针对症状: ${symptoms.join('、')}`);
    lines.push(`用法用量: 每次1粒，每日3次，饭后服用`);
    lines.push(`注意事项: 如出现不良反应请立即停药并就医`);
    if (patientInfo.allergies && patientInfo.allergies !== '无') {
        lines.push(`⚠ 过敏提醒: 患者有${patientInfo.allergies}过敏史，请确认药品成分`);
    }
    lines.push(`库存: ${drug.quantity}盒，有效期剩余${drug.expiry_date}天`);
    lines.push(`货架位置: 货架${drug.shelve_id}, (${drug.shelf_x}, ${drug.shelf_y})`);
    return lines.join('\n');
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
