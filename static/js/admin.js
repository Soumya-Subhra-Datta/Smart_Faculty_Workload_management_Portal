/**
 * ============================================================================
 * Admin Module — Dashboard, Faculty Management, Duty Management, Substitutions
 * ============================================================================
 */

const AdminModule = {
    facultyList: [],
    dutiesList: [],

    // ──────────────────────────────────
    // DASHBOARD
    // ──────────────────────────────────
    async loadDashboard() {
        const content = document.getElementById('page-content');
        content.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading dashboard...</p></div>';

        try {
            const data = await App.api('/api/admin/dashboard');
            const s = data.stats;
            const workload = data.workload || [];

            const maxSubs = Math.max(...workload.map(w => w.total_substitutions || 0), 1);

            content.innerHTML = `
                <div class="fade-in">
                    <div class="stats-grid">
                        <div class="stat-card purple">
                            <div class="stat-value">${s.total_faculty}</div>
                            <div class="stat-label">Total Faculty</div>
                        </div>
                        <div class="stat-card cyan">
                            <div class="stat-value">${s.active_duties}</div>
                            <div class="stat-label">Active Duties</div>
                        </div>
                        <div class="stat-card green">
                            <div class="stat-value">${s.completed_duties}</div>
                            <div class="stat-label">Completed Duties</div>
                        </div>
                        <div class="stat-card amber">
                            <div class="stat-value">${s.total_substitutions}</div>
                            <div class="stat-label">Active Substitutions</div>
                        </div>
                        <div class="stat-card rose">
                            <div class="stat-value">${s.cancelled_duties}</div>
                            <div class="stat-label">Cancelled Duties</div>
                        </div>
                        <div class="stat-card blue">
                            <div class="stat-value">${s.departments}</div>
                            <div class="stat-label">Departments</div>
                        </div>
                    </div>

                    <div class="data-section">
                        <div class="data-section-header">
                            <h3>Faculty Workload Analytics</h3>
                        </div>
                        <div class="workload-bar-list">
                            ${workload.filter(w => w.total_substitutions > 0).slice(0, 15).map(w => `
                                <div class="workload-bar-item">
                                    <span class="workload-bar-name" title="${App.escapeHtml(w.full_name)}">${App.escapeHtml(w.full_name)}</span>
                                    <div class="workload-bar-track">
                                        <div class="workload-bar-fill" style="width: ${(w.total_substitutions / maxSubs * 100)}%"></div>
                                    </div>
                                    <span class="workload-bar-count">${w.total_substitutions}</span>
                                </div>
                            `).join('') || '<p class="empty-state">No substitution data yet</p>'}
                        </div>
                    </div>
                </div>
            `;
        } catch (e) {
            content.innerHTML = `<div class="empty-state">Error loading dashboard: ${e.message}</div>`;
        }
    },

    // ──────────────────────────────────
    // FACULTY MANAGEMENT
    // ──────────────────────────────────
    async loadFacultyManagement() {
        const content = document.getElementById('page-content');
        content.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading faculty...</p></div>';

        try {
            const data = await App.api('/api/admin/faculty');
            this.facultyList = data.faculty;

            content.innerHTML = `
                <div class="fade-in">
                    <div class="filter-bar">
                        <input type="text" class="search-input" id="faculty-search" placeholder="Search faculty...">
                        <select id="faculty-dept-filter">
                            <option value="">All Departments</option>
                            ${[...new Set(this.facultyList.map(f => f.department))].sort().map(d =>
                `<option value="${d}">${d}</option>`
            ).join('')}
                        </select>
                        <button class="btn btn-primary" onclick="AdminModule.showAddFacultyModal()">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                            Add Faculty
                        </button>
                    </div>

                    <div class="data-section">
                        <div class="data-table-wrapper">
                            <table class="data-table" id="faculty-table">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Username</th>
                                        <th>Department</th>
                                        <th>Email</th>
                                        <th>Subjects</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="faculty-tbody">
                                    ${this.renderFacultyRows(this.facultyList)}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;

            // Search & filter listeners
            document.getElementById('faculty-search').addEventListener('input', () => this.filterFaculty());
            document.getElementById('faculty-dept-filter').addEventListener('change', () => this.filterFaculty());

        } catch (e) {
            content.innerHTML = `<div class="empty-state">Error loading faculty: ${e.message}</div>`;
        }
    },

    renderFacultyRows(list) {
        if (!list.length) return '<tr><td colspan="6" class="empty-state">No faculty found</td></tr>';
        return list.map(f => `
            <tr>
                <td style="color:var(--text-primary);font-weight:500">${App.escapeHtml(f.full_name)}</td>
                <td><code style="color:var(--accent-secondary);font-size:0.8rem">${f.username}</code></td>
                <td><span class="tag tag-primary">${f.department}</span></td>
                <td>${App.escapeHtml(f.email)}</td>
                <td>
                    <div class="subjects-list">
                        ${(f.subjects || []).map(s => `<span class="tag">${s}</span>`).join('')}
                    </div>
                </td>
                <td>
                    <div class="table-actions">
                        <button class="btn-icon action-edit" title="Edit" onclick="AdminModule.showEditFacultyModal(${f.id})">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                        </button>
                        <button class="btn-icon action-delete" title="Delete" onclick="AdminModule.deleteFaculty(${f.id}, '${App.escapeHtml(f.full_name)}')">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    },

    filterFaculty() {
        const search = document.getElementById('faculty-search').value.toLowerCase();
        const dept = document.getElementById('faculty-dept-filter').value;
        const filtered = this.facultyList.filter(f => {
            const matchSearch = !search || f.full_name.toLowerCase().includes(search) || f.username.toLowerCase().includes(search) || f.email.toLowerCase().includes(search);
            const matchDept = !dept || f.department === dept;
            return matchSearch && matchDept;
        });
        document.getElementById('faculty-tbody').innerHTML = this.renderFacultyRows(filtered);
    },

    showAddFacultyModal() {
        App.showModal('Add New Faculty', `
            <form id="add-faculty-form" onsubmit="return false;">
                <div class="form-row">
                    <div class="form-group">
                        <label>Full Name *</label>
                        <input type="text" id="fac-full-name" required>
                    </div>
                    <div class="form-group">
                        <label>Username *</label>
                        <input type="text" id="fac-username" required>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Email *</label>
                        <input type="email" id="fac-email" required>
                    </div>
                    <div class="form-group">
                        <label>Department *</label>
                        <select id="fac-department" required>
                            <option value="">Select</option>
                            <option value="CSE">CSE</option>
                            <option value="ECE">ECE</option>
                            <option value="EEE">EEE</option>
                            <option value="MECH">MECH</option>
                            <option value="CIVIL">CIVIL</option>
                            <option value="IT">IT</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label>Password (default: faculty123)</label>
                    <input type="password" id="fac-password" placeholder="faculty123">
                </div>
                <div class="form-group">
                    <label>Subjects (comma-separated)</label>
                    <input type="text" id="fac-subjects" placeholder="Machine Learning, Data Structures, ...">
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="App.closeModal()">Cancel</button>
                    <button class="btn btn-primary" onclick="AdminModule.addFaculty()">Add Faculty</button>
                </div>
            </form>
        `);
    },

    async addFaculty() {
        const data = {
            full_name: document.getElementById('fac-full-name').value.trim(),
            username: document.getElementById('fac-username').value.trim(),
            email: document.getElementById('fac-email').value.trim(),
            department: document.getElementById('fac-department').value,
            password: document.getElementById('fac-password').value || 'faculty123',
            subjects: document.getElementById('fac-subjects').value.split(',').map(s => s.trim()).filter(Boolean)
        };

        if (!data.full_name || !data.username || !data.email || !data.department) {
            App.showToast('Please fill in all required fields', 'warning');
            return;
        }

        try {
            await App.api('/api/admin/faculty', { method: 'POST', body: JSON.stringify(data) });
            App.showToast('Faculty added successfully', 'success');
            App.closeModal();
            this.loadFacultyManagement();
        } catch (e) {
            App.showToast(e.message, 'error');
        }
    },

    showEditFacultyModal(id) {
        const fac = this.facultyList.find(f => f.id === id);
        if (!fac) return;

        App.showModal('Edit Faculty', `
            <form id="edit-faculty-form" onsubmit="return false;">
                <div class="form-row">
                    <div class="form-group">
                        <label>Full Name</label>
                        <input type="text" id="edit-fac-name" value="${App.escapeHtml(fac.full_name)}">
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" id="edit-fac-email" value="${App.escapeHtml(fac.email)}">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Department</label>
                        <select id="edit-fac-dept">
                            ${['CSE', 'ECE', 'EEE', 'MECH', 'CIVIL', 'IT'].map(d =>
            `<option value="${d}" ${fac.department === d ? 'selected' : ''}>${d}</option>`
        ).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>New Password (leave blank to keep)</label>
                        <input type="password" id="edit-fac-pass" placeholder="Unchanged">
                    </div>
                </div>
                <div class="form-group">
                    <label>Subjects (comma-separated)</label>
                    <input type="text" id="edit-fac-subjects" value="${(fac.subjects || []).join(', ')}">
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="App.closeModal()">Cancel</button>
                    <button class="btn btn-primary" onclick="AdminModule.updateFaculty(${id})">Save Changes</button>
                </div>
            </form>
        `);
    },

    async updateFaculty(id) {
        const data = {
            full_name: document.getElementById('edit-fac-name').value.trim(),
            email: document.getElementById('edit-fac-email').value.trim(),
            department: document.getElementById('edit-fac-dept').value,
            subjects: document.getElementById('edit-fac-subjects').value.split(',').map(s => s.trim()).filter(Boolean)
        };
        const password = document.getElementById('edit-fac-pass').value;
        if (password) data.password = password;

        try {
            await App.api(`/api/admin/faculty/${id}`, { method: 'PUT', body: JSON.stringify(data) });
            App.showToast('Faculty updated successfully', 'success');
            App.closeModal();
            this.loadFacultyManagement();
        } catch (e) {
            App.showToast(e.message, 'error');
        }
    },

    async deleteFaculty(id, name) {
        if (!confirm(`Are you sure you want to delete ${name}? This will also remove their timetable, duties, and substitutions.`)) return;
        try {
            await App.api(`/api/admin/faculty/${id}`, { method: 'DELETE' });
            App.showToast('Faculty deleted', 'success');
            this.loadFacultyManagement();
        } catch (e) {
            App.showToast(e.message, 'error');
        }
    },

    // ──────────────────────────────────
    // DUTY MANAGEMENT
    // ──────────────────────────────────
    async loadDutyManagement() {
        const content = document.getElementById('page-content');
        content.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading duties...</p></div>';

        try {
            const [dutyData, facData] = await Promise.all([
                App.api('/api/admin/duties'),
                App.api('/api/admin/faculty')
            ]);
            this.dutiesList = dutyData.duties;
            this.facultyList = facData.faculty;

            content.innerHTML = `
                <div class="fade-in">
                    <div class="filter-bar">
                        <input type="text" class="search-input" id="duty-search" placeholder="Search duties...">
                        <select id="duty-status-filter">
                            <option value="">All Statuses</option>
                            <option value="upcoming">Upcoming</option>
                            <option value="ongoing">Ongoing</option>
                            <option value="completed">Completed</option>
                            <option value="cancelled">Cancelled</option>
                        </select>
                        <button class="btn btn-primary" onclick="AdminModule.showCreateDutyModal()">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                            Create Duty
                        </button>
                        <button class="btn btn-secondary" onclick="AdminModule.showCSVUploadModal()">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                            Upload CSV
                        </button>
                        <button class="btn btn-danger" onclick="AdminModule.clearDutyHistory()">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                            Clear History
                        </button>
                    </div>

                    <div class="data-section">
                        <div class="data-table-wrapper">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Event</th>
                                        <th>Assigned To</th>
                                        <th>Date</th>
                                        <th>Time</th>
                                        <th>Venue</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="duties-tbody">
                                    ${this.renderDutyRows(this.dutiesList)}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;

            document.getElementById('duty-search').addEventListener('input', () => this.filterDuties());
            document.getElementById('duty-status-filter').addEventListener('change', () => this.filterDuties());

        } catch (e) {
            content.innerHTML = `<div class="empty-state">Error loading duties: ${e.message}</div>`;
        }
    },

    renderDutyRows(list) {
        if (!list.length) return '<tr><td colspan="7" class="empty-state">No duties found</td></tr>';
        return list.map(d => `
            <tr>
                <td style="color:var(--text-primary);font-weight:500">${App.escapeHtml(d.event_name)}</td>
                <td>${App.escapeHtml(d.faculty_name || 'N/A')}<br><small style="color:var(--text-muted)">${d.faculty_department || ''}</small></td>
                <td>${d.date}</td>
                <td>${App.formatTime(d.start_time)} - ${App.formatTime(d.end_time)}</td>
                <td>${App.escapeHtml(d.venue)}</td>
                <td><span class="badge badge-${d.status}">${d.status}</span></td>
                <td>
                    <div class="table-actions">
                        ${d.status === 'upcoming' || d.status === 'ongoing' ? `
                            <button class="btn-icon action-cancel" title="Cancel Duty" onclick="AdminModule.cancelDuty(${d.id}, '${App.escapeHtml(d.event_name)}')">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `).join('');
    },

    filterDuties() {
        const search = document.getElementById('duty-search').value.toLowerCase();
        const status = document.getElementById('duty-status-filter').value;
        const filtered = this.dutiesList.filter(d => {
            const matchSearch = !search || d.event_name.toLowerCase().includes(search) || (d.faculty_name || '').toLowerCase().includes(search);
            const matchStatus = !status || d.status === status;
            return matchSearch && matchStatus;
        });
        document.getElementById('duties-tbody').innerHTML = this.renderDutyRows(filtered);
    },

    showCreateDutyModal() {
        const today = new Date().toISOString().split('T')[0];
        App.showModal('Create New Duty', `
            <form id="create-duty-form" onsubmit="return false;">
                <div class="form-group">
                    <label>Event Name *</label>
                    <input type="text" id="duty-name" placeholder="e.g., NAAC Inspection" required>
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea id="duty-desc" rows="2" placeholder="Brief description..."></textarea>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Date *</label>
                        <input type="date" id="duty-date" value="${today}" required>
                    </div>
                    <div class="form-group">
                        <label>Venue *</label>
                        <input type="text" id="duty-venue" placeholder="e.g., Main Auditorium" required>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>Start Time *</label>
                        <input type="time" id="duty-start" value="09:00" required>
                    </div>
                    <div class="form-group">
                        <label>End Time *</label>
                        <input type="time" id="duty-end" value="12:00" required>
                    </div>
                </div>
                <div class="form-group">
                    <label>Assign Faculty *</label>
                    <select id="duty-faculty" required>
                        <option value="">Select Faculty</option>
                        ${this.facultyList.map(f =>
            `<option value="${f.id}">${f.full_name} (${f.department})</option>`
        ).join('')}
                    </select>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="App.closeModal()">Cancel</button>
                    <button class="btn btn-primary" onclick="AdminModule.createDuty()">Create & Auto-Substitute</button>
                </div>
            </form>
        `);
    },

    async createDuty() {
        const data = {
            event_name: document.getElementById('duty-name').value.trim(),
            description: document.getElementById('duty-desc').value.trim(),
            date: document.getElementById('duty-date').value,
            start_time: document.getElementById('duty-start').value,
            end_time: document.getElementById('duty-end').value,
            venue: document.getElementById('duty-venue').value.trim(),
            assigned_faculty_id: parseInt(document.getElementById('duty-faculty').value)
        };

        if (!data.event_name || !data.date || !data.start_time || !data.end_time || !data.venue || !data.assigned_faculty_id) {
            App.showToast('Please fill in all required fields', 'warning');
            return;
        }

        try {
            const result = await App.api('/api/admin/duties', { method: 'POST', body: JSON.stringify(data) });
            App.showToast(`Duty created! ${result.substitutions_created} substitution(s) auto-assigned.`, 'success');
            App.closeModal();
            this.loadDutyManagement();
        } catch (e) {
            App.showToast(e.message, 'error');
        }
    },

    async cancelDuty(id, name) {
        if (!confirm(`Cancel duty "${name}"? Associated substitutions will also be cancelled.`)) return;
        try {
            const result = await App.api(`/api/admin/duties/${id}/cancel`, { method: 'PUT' });
            App.showToast(`Duty cancelled. ${result.substitutions_cancelled} substitution(s) also cancelled.`, 'success');
            this.loadDutyManagement();
        } catch (e) {
            App.showToast(e.message, 'error');
        }
    },

    async clearDutyHistory() {
        if (!confirm('Are you sure you want to clear all completed and cancelled duties? This action cannot be undone.')) return;
        try {
            const result = await App.api('/api/admin/duties/clear', { method: 'DELETE' });
            App.showToast(result.message, 'success');
            this.loadDutyManagement();
        } catch (e) {
            App.showToast(e.message, 'error');
        }
    },

    showCSVUploadModal() {
        App.showModal('Upload Duties via CSV', `
            <div class="csv-upload-zone" id="csv-drop-zone" onclick="document.getElementById('csv-file-input').click()">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                <p>Click or drag & drop a CSV file</p>
                <p class="csv-hint">Columns: event_name, description, date, start_time, end_time, venue, faculty_username</p>
            </div>
            <input type="file" id="csv-file-input" accept=".csv">
            <div id="csv-status"></div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="App.closeModal()">Close</button>
                <button class="btn btn-primary" id="csv-upload-btn" onclick="AdminModule.uploadCSV()" disabled>Upload & Process</button>
            </div>
        `);

        const fileInput = document.getElementById('csv-file-input');
        const dropZone = document.getElementById('csv-drop-zone');

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                document.getElementById('csv-status').innerHTML = `<p style="color:var(--success);margin-top:0.5rem">Selected: ${e.target.files[0].name}</p>`;
                document.getElementById('csv-upload-btn').disabled = false;
            }
        });

        dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                document.getElementById('csv-status').innerHTML = `<p style="color:var(--success);margin-top:0.5rem">Selected: ${e.dataTransfer.files[0].name}</p>`;
                document.getElementById('csv-upload-btn').disabled = false;
            }
        });
    },

    async uploadCSV() {
        const fileInput = document.getElementById('csv-file-input');
        if (!fileInput.files.length) return;

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        const statusEl = document.getElementById('csv-status');
        statusEl.innerHTML = '<div class="loading-spinner" style="padding:1rem"><div class="spinner"></div><p>Processing CSV...</p></div>';

        try {
            const result = await App.api('/api/admin/duties/upload-csv', {
                method: 'POST',
                body: formData,
                headers: {} // Let browser set Content-Type for FormData
            });

            statusEl.innerHTML = `
                <div style="margin-top:1rem;padding:1rem;background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.2);border-radius:8px">
                    <p style="color:var(--success);font-weight:600">${result.message}</p>
                    ${result.results.map(r => `
                        <p style="font-size:0.85rem;margin-top:0.3rem;color:var(--text-secondary)">
                            ${r.error ? `❌ ${r.event_name}: ${r.error}` : `✓ ${r.event_name} — ${r.faculty} (${r.substitutions} sub(s))`}
                        </p>
                    `).join('')}
                </div>
            `;
            App.showToast('CSV processed successfully', 'success');
        } catch (e) {
            statusEl.innerHTML = `<div class="error-msg">${e.message}</div>`;
        }
    },

    // ──────────────────────────────────
    // SUBSTITUTIONS
    // ──────────────────────────────────
    async loadSubstitutions() {
        const content = document.getElementById('page-content');
        content.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading substitutions...</p></div>';

        try {
            const data = await App.api('/api/admin/substitutions');
            const subs = data.substitutions;

            content.innerHTML = `
                <div class="fade-in">
                    <div class="filter-bar">
                        <input type="text" class="search-input" id="sub-search" placeholder="Search substitutions...">
                        <select id="sub-status-filter">
                            <option value="">All Statuses</option>
                            <option value="assigned">Assigned</option>
                            <option value="completed">Completed</option>
                            <option value="cancelled">Cancelled</option>
                        </select>
                    </div>

                    <div class="data-section">
                        <div class="data-section-header">
                            <h3>All Substitutions (${subs.length})</h3>
                        </div>
                        <div class="data-table-wrapper">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Original Faculty</th>
                                        <th>Substitute</th>
                                        <th>Subject</th>
                                        <th>Classroom</th>
                                        <th>Time</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody id="subs-tbody">
                                    ${this.renderSubRows(subs)}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;

            document.getElementById('sub-search').addEventListener('input', () => {
                const search = document.getElementById('sub-search').value.toLowerCase();
                const status = document.getElementById('sub-status-filter').value;
                const filtered = subs.filter(s => {
                    const ms = !search || s.original_faculty_name.toLowerCase().includes(search) || s.substitute_faculty_name.toLowerCase().includes(search) || s.subject.toLowerCase().includes(search);
                    const mst = !status || s.status === status;
                    return ms && mst;
                });
                document.getElementById('subs-tbody').innerHTML = this.renderSubRows(filtered);
            });
            document.getElementById('sub-status-filter').addEventListener('change', () => {
                document.getElementById('sub-search').dispatchEvent(new Event('input'));
            });

        } catch (e) {
            content.innerHTML = `<div class="empty-state">Error: ${e.message}</div>`;
        }
    },

    renderSubRows(list) {
        if (!list.length) return '<tr><td colspan="7" class="empty-state">No substitutions found</td></tr>';
        return list.map(s => `
            <tr>
                <td>${s.date}</td>
                <td>${App.escapeHtml(s.original_faculty_name)}<br><small style="color:var(--text-muted)">${s.original_department || ''}</small></td>
                <td style="color:var(--accent-secondary)">${App.escapeHtml(s.substitute_faculty_name)}<br><small style="color:var(--text-muted)">${s.substitute_department || ''}</small></td>
                <td>${App.escapeHtml(s.subject)}</td>
                <td>${App.escapeHtml(s.classroom)}</td>
                <td>${App.formatTime(s.start_time)} - ${App.formatTime(s.end_time)}</td>
                <td><span class="badge badge-${s.status}">${s.status}</span></td>
            </tr>
        `).join('');
    }
};
