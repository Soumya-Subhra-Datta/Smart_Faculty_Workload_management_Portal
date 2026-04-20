/**
 * ============================================================================
 * Faculty Workload Portal — Core Application Module
 * Client-side router, API utilities, and shared functions.
 * ============================================================================
 */

const App = {
    currentPage: null,
    user: null,
    token: null,
    notifInterval: null,

    /** Initialize the application */
    init() {
        this.token = localStorage.getItem('jwt_token');
        const userData = localStorage.getItem('user_data');
        if (userData) {
            try { this.user = JSON.parse(userData); } catch(e) { this.user = null; }
        }

        if (this.token && this.user) {
            this.showApp();
        } else {
            this.showLogin();
        }

        // Global event listeners
        document.getElementById('logout-btn').addEventListener('click', () => this.logout());
        document.getElementById('notif-btn').addEventListener('click', () => this.toggleNotifPanel());
        document.getElementById('close-notif-btn').addEventListener('click', () => this.toggleNotifPanel());
        document.getElementById('mark-all-read-btn').addEventListener('click', () => this.markAllNotifRead());
        document.getElementById('clear-history-btn').addEventListener('click', () => this.clearNotifHistory());
        document.getElementById('modal-close').addEventListener('click', () => this.closeModal());
        document.getElementById('modal-overlay').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeModal();
        });
        document.getElementById('menu-toggle').addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('open');
        });
    },

    /** Show login screen */
    showLogin() {
        document.getElementById('login-screen').classList.remove('hidden');
        document.getElementById('app-shell').classList.add('hidden');
        if (this.notifInterval) clearInterval(this.notifInterval);
    },

    /** Show main app after login */
    showApp() {
        document.getElementById('login-screen').classList.add('hidden');
        document.getElementById('app-shell').classList.remove('hidden');

        // Update user info in sidebar
        document.getElementById('user-display-name').textContent = this.user.full_name;
        document.getElementById('user-role-display').textContent = this.user.role === 'admin' ? 'Administrator' : 'Faculty';
        document.getElementById('user-avatar').textContent = this.user.full_name.charAt(0).toUpperCase();

        // Build navigation based on role
        this.buildNavigation();

        // Navigate to default page
        if (this.user.role === 'admin') {
            this.navigate('dashboard');
        } else {
            this.navigate('my-timetable');
        }

        // Start notification polling
        this.pollNotifications();
        this.notifInterval = setInterval(() => this.pollNotifications(), 30000);
    },

    /** Build sidebar navigation based on user role */
    buildNavigation() {
        const nav = document.getElementById('sidebar-nav');
        nav.innerHTML = '';

        if (this.user.role === 'admin') {
            nav.innerHTML = `
                <div class="nav-section-title">Overview</div>
                <button class="nav-item active" data-page="dashboard" id="nav-dashboard">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
                    Dashboard
                </button>
                <div class="nav-section-title">Management</div>
                <button class="nav-item" data-page="faculty-mgmt" id="nav-faculty-mgmt">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>
                    Faculty Management
                </button>
                <button class="nav-item" data-page="duty-mgmt" id="nav-duty-mgmt">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                    Duty Management
                </button>
                <button class="nav-item" data-page="substitutions" id="nav-substitutions">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 014-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 01-4 4H3"/></svg>
                    Substitutions
                </button>
            `;
        } else {
            nav.innerHTML = `
                <div class="nav-section-title">My Schedule</div>
                <button class="nav-item active" data-page="my-timetable" id="nav-my-timetable">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                    My Timetable
                </button>
                <button class="nav-item" data-page="my-duties" id="nav-my-duties">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                    My Duties
                </button>
                <button class="nav-item" data-page="my-substitutions" id="nav-my-substitutions">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 014-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 01-4 4H3"/></svg>
                    Substitutions
                </button>
            `;
        }

        // Add click handlers
        nav.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', () => {
                const page = item.dataset.page;
                this.navigate(page);
            });
        });
    },

    /** Navigate to a page */
    navigate(page) {
        // Update active nav
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.page === page);
        });

        // Close mobile sidebar
        document.getElementById('sidebar').classList.remove('open');

        this.currentPage = page;

        // Route to page
        switch(page) {
            case 'dashboard':
                document.getElementById('page-title').textContent = 'Dashboard';
                AdminModule.loadDashboard();
                break;
            case 'faculty-mgmt':
                document.getElementById('page-title').textContent = 'Faculty Management';
                AdminModule.loadFacultyManagement();
                break;
            case 'duty-mgmt':
                document.getElementById('page-title').textContent = 'Duty Management';
                AdminModule.loadDutyManagement();
                break;
            case 'substitutions':
                document.getElementById('page-title').textContent = 'Substitution Tracking';
                AdminModule.loadSubstitutions();
                break;
            case 'my-timetable':
                document.getElementById('page-title').textContent = 'My Timetable';
                FacultyModule.loadTimetable();
                break;
            case 'my-duties':
                document.getElementById('page-title').textContent = 'My Duties';
                FacultyModule.loadDuties();
                break;
            case 'my-substitutions':
                document.getElementById('page-title').textContent = 'My Substitutions';
                FacultyModule.loadSubstitutions();
                break;
        }
    },

    /** Login handler - called from auth.js */
    onLogin(token, user) {
        this.token = token;
        this.user = user;
        localStorage.setItem('jwt_token', token);
        localStorage.setItem('user_data', JSON.stringify(user));
        this.showApp();
    },

    /** Logout */
    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('jwt_token');
        localStorage.removeItem('user_data');
        if (this.notifInterval) clearInterval(this.notifInterval);
        this.showLogin();
    },

    // ── API Utility ──

    /** Make authenticated API call */
    async api(url, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...(this.token ? { 'Authorization': `Bearer ${this.token}` } : {}),
            ...options.headers
        };

        // Remove Content-Type for FormData (multipart upload)
        if (options.body instanceof FormData) {
            delete headers['Content-Type'];
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            if (response.status === 401) {
                this.logout();
                this.showToast('Session expired. Please login again.', 'warning');
                throw new Error('Unauthorized');
            }

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || data.message || 'API Error');
            }
            return data;
        } catch (error) {
            if (error.message !== 'Unauthorized') {
                console.error('API Error:', error);
            }
            throw error;
        }
    },

    // ── UI Utilities ──

    /** Show a toast notification */
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                ${type === 'success' ? '<path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>' :
                  type === 'error' ? '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>' :
                  type === 'warning' ? '<path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>' :
                  '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>'}
            </svg>
            <span>${message}</span>
        `;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(50px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    },

    /** Show modal */
    showModal(title, bodyHTML) {
        document.getElementById('modal-title').textContent = title;
        document.getElementById('modal-body').innerHTML = bodyHTML;
        document.getElementById('modal-overlay').classList.remove('hidden');
    },

    /** Close modal */
    closeModal() {
        document.getElementById('modal-overlay').classList.add('hidden');
    },

    // ── Notifications ──

    /** Poll notifications */
    async pollNotifications() {
        try {
            const data = await this.api('/api/faculty/notifications');
            const badge = document.getElementById('notif-badge');
            if (data.unread_count > 0) {
                badge.textContent = data.unread_count;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        } catch(e) {
            // Silently fail on poll errors
        }
    },

    /** Toggle notification panel */
    async toggleNotifPanel() {
        const panel = document.getElementById('notif-panel');
        if (panel.classList.contains('hidden')) {
            panel.classList.remove('hidden');
            await this.loadNotifications();
        } else {
            panel.classList.add('hidden');
        }
    },

    /** Load notifications into the panel */
    async loadNotifications() {
        try {
            const data = await this.api('/api/faculty/notifications');
            const list = document.getElementById('notif-list');

            if (!data.notifications || data.notifications.length === 0) {
                list.innerHTML = '<p class="empty-state">No notifications yet</p>';
                return;
            }

            list.innerHTML = data.notifications.map(n => `
                <div class="notif-item ${n.is_read ? '' : 'unread'}" data-id="${n.id}" onclick="App.markNotifRead(${n.id}, this)">
                    <span class="notif-type-badge notif-type-${n.type}">${n.type.replace('_', ' ')}</span>
                    <div class="notif-title">${this.escapeHtml(n.title)}</div>
                    <div class="notif-message">${this.escapeHtml(n.message)}</div>
                    <div class="notif-time">${this.formatDate(n.created_at)}</div>
                </div>
            `).join('');
        } catch(e) {
            console.error('Error loading notifications:', e);
        }
    },

    /** Mark a single notification as read */
    async markNotifRead(id, el) {
        try {
            await this.api(`/api/faculty/notifications/${id}/read`, { method: 'PUT' });
            if (el) el.classList.remove('unread');
            this.pollNotifications();
        } catch(e) { console.error(e); }
    },

    /** Mark all notifications as read */
    async markAllNotifRead() {
        try {
            await this.api('/api/faculty/notifications/read-all', { method: 'PUT' });
            this.showToast('All notifications marked as read', 'success');
            await this.loadNotifications();
            this.pollNotifications();
        } catch(e) {
            this.showToast('Error marking notifications', 'error');
        }
    },

    /** Clear read notification history */
    async clearNotifHistory() {
        try {
            await this.api('/api/faculty/notifications/clear', { method: 'DELETE' });
            this.showToast('Read notifications cleared', 'success');
            await this.loadNotifications();
            this.pollNotifications();
        } catch(e) {
            this.showToast('Error clearing history', 'error');
        }
    },

    // ── Helpers ──

    escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    formatDate(dateStr) {
        if (!dateStr) return '';
        const d = new Date(dateStr);
        const now = new Date();
        const diff = now - d;
        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff/60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff/3600000)}h ago`;
        return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
    },

    formatTime(timeStr) {
        if (!timeStr) return '';
        const parts = timeStr.split(':');
        const h = parseInt(parts[0]);
        const m = parts[1];
        const ampm = h >= 12 ? 'PM' : 'AM';
        const h12 = h % 12 || 12;
        return `${h12}:${m} ${ampm}`;
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => App.init());
