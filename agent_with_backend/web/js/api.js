/**
 * 智能药品管理系统 - API 客户端
 * 统一封装后端 API 调用，自动管理 JWT 令牌和错误处理
 */

const API_BASE = 'http://localhost:8001/api';

const ApiClient = {
    /**
     * 通用请求方法
     */
    async request(method, path, body = null) {
        const headers = { 'Content-Type': 'application/json' };
        const token = localStorage.getItem('auth_token');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const options = { method, headers };
            if (body && method !== 'GET') {
                options.body = JSON.stringify(body);
            }
            const response = await fetch(`${API_BASE}${path}`, options);
            const data = await response.json();

            // 令牌失效（401）跳回登录页；权限不足（403）等仅返回错误
            if (data.success === false && data.error_code && (data.error_code === 'AUTH_001' || data.error_code === 'AUTH_002')) {
                localStorage.clear();
                window.location.href = 'index.html';
                return data;
            }
            return data;
        } catch (err) {
            console.error(`API ${method} ${path} error:`, err);
            return { success: false, error: `网络错误: ${err.message}`, code: 'NETWORK_ERROR' };
        }
    },

    get(path) { return this.request('GET', path); },
    post(path, body) { return this.request('POST', path, body); },
    put(path, body) { return this.request('PUT', path, body); },
    delete(path) { return this.request('DELETE', path); },

    /**
     * 构建 query string（忽略 null/undefined/空字符串）
     */
    _buildQuery(params) {
        const sp = new URLSearchParams();
        Object.entries(params || {}).forEach(([key, val]) => {
            if (val !== null && val !== undefined && val !== '') {
                sp.set(key, String(val));
            }
        });
        const qs = sp.toString();
        return qs ? `?${qs}` : '';
    },

    /**
     * 非 JSON 响应（如 CSV 导出）
     */
    async requestRaw(method, path, { accept, body } = {}) {
        const headers = {};
        const token = localStorage.getItem('auth_token');
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        if (accept) {
            headers['Accept'] = accept;
        }
        if (body !== undefined && body !== null) {
            headers['Content-Type'] = 'application/json';
        }
        try {
            const options = { method, headers };
            if (body !== undefined && body !== null && method !== 'GET') {
                options.body = JSON.stringify(body);
            }
            const response = await fetch(`${API_BASE}${path}`, options);
            const contentType = response.headers.get('content-type') || '';
            if (!response.ok) {
                let errMsg = `HTTP ${response.status}`;
                try {
                    if (contentType.includes('application/json')) {
                        const errData = await response.json();
                        errMsg = errData.error?.message || errData.message || errMsg;
                    }
                } catch (_) { /* ignore */ }
                return { success: false, error: errMsg, code: 'HTTP_ERROR' };
            }
            if (contentType.includes('application/json')) {
                return await response.json();
            }
            const text = await response.text();
            return { success: true, data: text, contentType };
        } catch (err) {
            console.error(`API raw ${method} ${path} error:`, err);
            return { success: false, error: `网络错误: ${err.message}`, code: 'NETWORK_ERROR' };
        }
    },

    /* ===== 认证 ===== */
    login(username, password) { return this.post('/auth/login', { username, password }); },
    logout(token) { return this.post('/auth/logout', { refresh_token: token }); },
    refresh(refreshToken) { return this.post('/auth/refresh', { refresh_token: refreshToken }); },
    getProfile() { return this.get('/auth/profile'); },
    register(data) { return this.post('/auth/register', data); },

    /* ===== 健康检查 ===== */
    health() { return this.get('/health'); },

    /* ===== 药品管理 ===== */
    /**
     * 药品列表 GET /api/drugs
     * @param {string} [nameFilter] - name 模糊筛选
     * @param {string} [categoryFilter] - category 精确筛选
     * @param {string} [symptomFilter] - symptom 适应症筛选（第三参兼容旧名 indicationFilter）
     * @param {object} [extra] - page, limit, sort_by, order
     */
    getDrugs(nameFilter, categoryFilter, symptomFilter, extra = {}) {
        if (typeof nameFilter === 'object' && nameFilter !== null) {
            extra = nameFilter;
            nameFilter = extra.name || extra.nameFilter;
            categoryFilter = extra.category || extra.categoryFilter;
            symptomFilter = extra.symptom || extra.symptomFilter || extra.indicationFilter;
        }
        const query = this._buildQuery({
            name: nameFilter,
            category: categoryFilter,
            symptom: symptomFilter,
            page: extra.page,
            limit: extra.limit,
            sort_by: extra.sort_by,
            order: extra.order,
        });
        return this.get(`/drugs${query}`);
    },

    getDrug(id) { return this.get(`/drugs/${id}`); },
    createDrug(drug) { return this.post('/drugs', drug); },
    updateDrug(id, data) { return this.put(`/drugs/${id}`, data); },
    deleteDrug(id) { return this.delete(`/drugs/${id}`); },

    /**
     * 综合搜索 GET /api/drugs/search
     * @param {string} keyword - keyword 或 q
     * @param {object} [extra] - category, page, limit, sort_by, order
     */
    searchDrugs(keyword, extra = {}) {
        const query = this._buildQuery({
            keyword: keyword || extra.keyword || extra.q,
            q: keyword || extra.q || extra.keyword,
            category: extra.category,
            page: extra.page,
            limit: extra.limit,
            sort_by: extra.sort_by,
            order: extra.order,
        });
        return this.get(`/drugs/search${query}`);
    },

    /**
     * 拣货/库区视图 GET /api/inventory
     */
    getInventory(extra = {}) {
        const query = this._buildQuery({
            name: extra.name || extra.nameFilter,
            category: extra.category || extra.categoryFilter,
            symptom: extra.symptom || extra.symptomFilter,
            threshold: extra.threshold,
            expiring_window: extra.expiring_window,
            page: extra.page,
            limit: extra.limit,
            sort_by: extra.sort_by,
            order: extra.order,
        });
        return this.get(`/inventory${query}`);
    },

    adjustInventory(id, data) { return this.post(`/drugs/${id}/adjust`, data); },
    batchImport(drugs) { return this.post('/drugs/batch-import', drugs); },

    drugStats() { return this.get('/drugs/stats'); },

    getLowStockDrugs(threshold, extra = {}) {
        const query = this._buildQuery({
            threshold: threshold ?? extra.threshold,
            page: extra.page,
            limit: extra.limit,
        });
        return this.get(`/drugs/low-stock${query}`);
    },

    getExpiringSoonDrugs(days, extra = {}) {
        const query = this._buildQuery({
            days: days ?? extra.days,
            page: extra.page,
            limit: extra.limit,
        });
        return this.get(`/drugs/expiring-soon${query}`);
    },

    /** GET /api/categories */
    getCategories(tree = false, extra = {}) {
        if (typeof tree === 'object' && tree !== null) {
            extra = tree;
            tree = !!extra.tree;
        }
        const query = this._buildQuery({
            tree: tree ? 1 : null,
            page: extra.page,
            limit: extra.limit,
        });
        return this.get(`/categories${query}`);
    },

    createCategory(data) { return this.post('/categories', data); },

    /** @deprecated 请用 getCategories() */
    drugCategories() { return this.getCategories(); },

    /**
     * 导出药品 GET /api/drugs/export
     * @param {'json'|'csv'} format
     */
    exportDrugs(format = 'json') {
        if (format === 'csv') {
            return this.requestRaw('GET', '/drugs/export?format=csv', { accept: 'text/csv' });
        }
        return this.get('/drugs/export?format=json');
    },

    /**
     * 触发浏览器下载导出文件
     */
    async downloadDrugExport(format = 'csv') {
        const result = await this.exportDrugs(format);
        if (!result.success) {
            return result;
        }
        let blob;
        let filename;
        if (format === 'csv') {
            blob = new Blob(['\ufeff' + (result.data || '')], { type: 'text/csv;charset=utf-8' });
            filename = 'drugs_export.csv';
        } else {
            const json = JSON.stringify(result.data ?? result, null, 2);
            blob = new Blob([json], { type: 'application/json;charset=utf-8' });
            filename = 'drugs_export.json';
        }
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
        return { success: true, filename };
    },

    /* ===== 订单管理 ===== */
    getOrders() { return this.get('/orders'); },
    createOrder(items) { return this.post('/order', items); },
    pickupSingle(item) { return this.post('/pickup', item); },
    dispense(data) { return this.post('/dispense', data); },

    /* ===== 审批管理 ===== */
    createApproval(data) { return this.post('/approvals', data); },
    getApproval(id) { return this.get(`/approvals/${id}`); },
    getPendingApprovals(limit = 100) { return this.get(`/approvals/pending?limit=${limit}`); },
    approveApproval(id, doctorId, notes) {
        return this.post(`/approvals/${id}/approve`, { doctor_id: doctorId, notes });
    },
    rejectApproval(id, doctorId, reason) {
        return this.post(`/approvals/${id}/reject`, { doctor_id: doctorId, reason });
    },
    completeApproval(id) {
        return this.post(`/approvals/${id}/complete`);
    },

    /* ===== AI 医疗咨询 ===== */
    sendConsultation(message, patientId) {
        return this.post('/consultation', { message, patient_id: patientId });
    },
    resetConsultation() {
        return this.post('/consultation/reset');
    },

    /* ===== 取药确认 ===== */
    confirmPickup(taskId) {
        return this.post(`/orders/${taskId}/complete`);
    },

    /* ===== 用户管理 ===== */
    getUsers(params) { return this.get(`/users${params ? '?' + params : ''}`); },
    getUser(id) { return this.get(`/users/${id}`); },
    updateUser(id, data) { return this.put(`/users/${id}`, data); },
    getRoles() { return this.get('/roles'); },
    getPermissions() { return this.get('/permissions'); },
    getUserPermissions(id) { return this.get(`/users/${id}/permissions`); },

    /* ===== 审计日志 ===== */
    getAuditLogs(params) { return this.get(`/audit/logs${params ? '?' + params : ''}`); },
    getAuditStats(period) { return this.get(`/audit/stats${period ? '?period=' + period : ''}`); },

    /* ===== 智能筛选 ===== */
    screeningQuery(data) { return this.post('/screening/query', data); },
    screeningBatch(queries) { return this.post('/screening/batch', queries); },
    standardizeSymptoms(text) { return this.post('/symptoms/standardize', { symptom_text: text }); },
    getSymptomSynonyms(name) { return this.get(`/symptoms/synonyms${name ? '?symptom_name=' + encodeURIComponent(name) : ''}`); },
    getScreeningConfig() { return this.get('/screening/config'); },
    updateScreeningConfig(config) { return this.put('/screening/config', config); },
    getScreeningHistory(params) { return this.get(`/screening/history${params ? '?' + params : ''}`); },
    getScreeningHistoryDetail(id) { return this.get(`/screening/history/${id}`); },
    getScreeningStatus() { return this.get('/screening/status'); },

    /* ===== ROS2 仿真状态 ===== */
    returnToQueue() { return this.post('/ros/return-to-queue'); },
    getRosStatus() { return this.get('/ros/status'); },
    getCarStates() { return this.get('/ros/car-states'); },
    getTaskStates() { return this.get('/ros/task-states'); },
    getTaskState(id) { return this.get(`/ros/task-states/${id}`); },
    getCabinetStates() { return this.get('/ros/cabinet-states'); },
};

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

/* ===== 认证辅助 ===== */
function getCurrentUser() {
    try {
        return JSON.parse(localStorage.getItem('currentUser'));
    } catch { return null; }
}

function requireAuth(expectedRole) {
    const token = localStorage.getItem('auth_token');
    const user = getCurrentUser();
    if (!token || !user) {
        window.location.href = 'index.html';
        return null;
    }
    if (expectedRole && user.role !== expectedRole) {
        const pages = { patient: 'patient.html', doctor: 'doctor.html', admin: 'admin.html' };
        window.location.href = pages[user.role] || 'index.html';
        return null;
    }
    return user;
}

function getUserDisplay(user) {
    if (!user) return '';
    const roleMap = { patient: '患者', doctor: '医生', admin: '管理员' };
    return `${user.display_name || user.username} (${roleMap[user.role] || user.role})`;
}

function doLogout() {
    const token = localStorage.getItem('refresh_token');
    if (token) ApiClient.logout(token).catch(() => {});
    // 只清除认证信息，保留咨询历史、取药记录等本地数据
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('currentUser');
    window.location.href = 'index.html';
}
