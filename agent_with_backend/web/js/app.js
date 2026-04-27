/**
 * 智能药品管理系统 - API 客户端封装
 * 统一封装后端 API 调用，自动处理错误和认证
 */

const API_BASE = 'http://localhost:8001/api';

const ApiClient = {
    /**
     * 通用请求方法
     */
    async request(method, path, body = null) {
        const options = {
            method,
            headers: { 'Content-Type': 'application/json' },
        };
        if (body && method !== 'GET') {
            options.body = JSON.stringify(body);
        }
        try {
            const response = await fetch(`${API_BASE}${path}`, options);
            const data = await response.json();
            if (!response.ok && !data.success) {
                console.warn(`API ${method} ${path} failed:`, data);
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

    /* ===== 健康检查 ===== */
    health() { return this.get('/health'); },

    /* ===== 药品管理 ===== */
    getDrugs(nameFilter) {
        const query = nameFilter ? `?name=${encodeURIComponent(nameFilter)}` : '';
        return this.get(`/drugs${query}`);
    },
    getDrug(id) { return this.get(`/drugs/${id}`); },
    createDrug(drug) { return this.post('/drugs', drug); },
    updateDrug(id, data) { return this.put(`/drugs/${id}`, data); },
    deleteDrug(id) { return this.delete(`/drugs/${id}`); },
    drugStats() { return this.get('/drugs/stats'); },

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
};
