/**
 * ============================================================================
 * Faculty Module — Timetable, Duties, Substitutions views
 * ============================================================================
 */

const FacultyModule = {
    // ──────────────────────────────────
    // TIMETABLE VIEW
    // ──────────────────────────────────
    async loadTimetable() {
        const content = document.getElementById('page-content');
        content.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading timetable...</p></div>';

        try {
            const data = await App.api('/api/faculty/timetable');
            const timetable = data.timetable;

            if (!timetable.length) {
                content.innerHTML = '<div class="empty-state">No timetable entries found</div>';
                return;
            }

            // Organize by day and period
            const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            const periods = [
                { period: 1, time: '09:00 - 09:50' },
                { period: 2, time: '09:50 - 10:40' },
                { period: 3, time: '10:50 - 11:40' },
                { period: 4, time: '11:40 - 12:30' },
                { period: 0, time: '12:30 - 13:20', isLunch: true },
                { period: 5, time: '13:20 - 14:10' },
                { period: 6, time: '14:10 - 15:00' },
                { period: 7, time: '15:10 - 16:00' },
            ];

            const grid = {};
            timetable.forEach(entry => {
                const key = `${entry.day_of_week}-${entry.period}`;
                grid[key] = entry;
            });

            content.innerHTML = `
                <div class="fade-in">
                    <div class="data-section">
                        <div class="data-section-header">
                            <h3>Weekly Timetable — ${App.user.full_name}</h3>
                            <span class="tag tag-primary">${App.user.department}</span>
                        </div>
                        <div style="overflow-x:auto;padding:1rem">
                            <div class="timetable-grid" style="grid-template-columns: 100px repeat(${days.length}, 1fr)">
                                <div class="timetable-header">Time</div>
                                ${days.map(d => `<div class="timetable-header">${d.substring(0, 3)}</div>`).join('')}
                                
                                ${periods.map(p => {
                if (p.isLunch) {
                    return `
                                            <div class="timetable-time" style="background:rgba(245,158,11,0.08);color:var(--warning)">LUNCH</div>
                                            ${days.map(() => `<div class="timetable-cell" style="background:rgba(245,158,11,0.04)"><span style="font-size:0.7rem;color:var(--text-muted)">🍽️</span></div>`).join('')}
                                        `;
                }
                return `
                                        <div class="timetable-time">${p.time}</div>
                                        ${days.map(d => {
                    const entry = grid[`${d}-${p.period}`];
                    if (entry) {
                        return `
                                                    <div class="timetable-cell">
                                                        <div class="timetable-class">
                                                            <div class="tt-subject">${App.escapeHtml(entry.subject)}</div>
                                                            <div class="tt-room">${App.escapeHtml(entry.classroom)}</div>
                                                        </div>
                                                    </div>
                                                `;
                    }
                    return `<div class="timetable-cell"><span style="font-size:0.7rem;color:var(--text-muted)">Free</span></div>`;
                }).join('')}
                                    `;
            }).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } catch (e) {
            content.innerHTML = `<div class="empty-state">Error loading timetable: ${e.message}</div>`;
        }
    },

    // ──────────────────────────────────
    // DUTIES VIEW
    // ──────────────────────────────────
    async loadDuties() {
        const content = document.getElementById('page-content');
        content.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading duties...</p></div>';

        try {
            const data = await App.api('/api/faculty/duties');
            const duties = data.duties;

            content.innerHTML = `
                <div class="fade-in">
                    <div class="stats-grid" style="grid-template-columns: repeat(auto-fit, minmax(150px, 1fr))">
                        <div class="stat-card cyan">
                            <div class="stat-value">${duties.filter(d => d.status === 'upcoming').length}</div>
                            <div class="stat-label">Upcoming</div>
                        </div>
                        <div class="stat-card amber">
                            <div class="stat-value">${duties.filter(d => d.status === 'ongoing').length}</div>
                            <div class="stat-label">Ongoing</div>
                        </div>
                        <div class="stat-card green">
                            <div class="stat-value">${duties.filter(d => d.status === 'completed').length}</div>
                            <div class="stat-label">Completed</div>
                        </div>
                        <div class="stat-card rose">
                            <div class="stat-value">${duties.filter(d => d.status === 'cancelled').length}</div>
                            <div class="stat-label">Cancelled</div>
                        </div>
                    </div>

                    <div class="data-section">
                        <div class="data-section-header">
                            <h3>My Duties (${duties.length})</h3>
                        </div>
                        <div class="data-table-wrapper">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Event</th>
                                        <th>Date</th>
                                        <th>Time</th>
                                        <th>Venue</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${duties.length ? duties.map(d => `
                                        <tr>
                                            <td style="color:var(--text-primary);font-weight:500">${App.escapeHtml(d.event_name)}</td>
                                            <td>${d.date}</td>
                                            <td>${App.formatTime(d.start_time)} - ${App.formatTime(d.end_time)}</td>
                                            <td>${App.escapeHtml(d.venue)}</td>
                                            <td><span class="badge badge-${d.status}">${d.status}</span></td>
                                        </tr>
                                    `).join('') : '<tr><td colspan="5" class="empty-state">No duties assigned</td></tr>'}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        } catch (e) {
            content.innerHTML = `<div class="empty-state">Error: ${e.message}</div>`;
        }
    },

    // ──────────────────────────────────
    // SUBSTITUTIONS VIEW
    // ──────────────────────────────────
    async loadSubstitutions() {
        const content = document.getElementById('page-content');
        content.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Loading substitutions...</p></div>';

        try {
            const data = await App.api('/api/faculty/substitutions');
            const subs = data.substitutions;

            const asSubstitute = subs.filter(s => s.substitute_faculty_id === App.user.id);
            const asOriginal = subs.filter(s => s.original_faculty_id === App.user.id);

            content.innerHTML = `
                <div class="fade-in">
                    ${asSubstitute.length ? `
                    <div class="data-section">
                        <div class="data-section-header">
                            <h3>Classes I'm Substituting (${asSubstitute.length})</h3>
                        </div>
                        <div class="data-table-wrapper">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Original Faculty</th>
                                        <th>Subject</th>
                                        <th>Classroom</th>
                                        <th>Time</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${asSubstitute.map(s => `
                                        <tr>
                                            <td>${s.date}</td>
                                            <td>${App.escapeHtml(s.original_faculty_name)}<br><small style="color:var(--text-muted)">${s.original_department || ''}</small></td>
                                            <td style="color:var(--text-primary);font-weight:500">${App.escapeHtml(s.subject)}</td>
                                            <td>${App.escapeHtml(s.classroom)}</td>
                                            <td>${App.formatTime(s.start_time)} - ${App.formatTime(s.end_time)}</td>
                                            <td><span class="badge badge-${s.status}">${s.status}</span></td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    ` : ''}

                    ${asOriginal.length ? `
                    <div class="data-section">
                        <div class="data-section-header">
                            <h3>My Classes Being Covered (${asOriginal.length})</h3>
                        </div>
                        <div class="data-table-wrapper">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Substitute Faculty</th>
                                        <th>Subject</th>
                                        <th>Classroom</th>
                                        <th>Time</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${asOriginal.map(s => `
                                        <tr>
                                            <td>${s.date}</td>
                                            <td style="color:var(--accent-secondary)">${App.escapeHtml(s.substitute_faculty_name)}<br><small style="color:var(--text-muted)">${s.substitute_department || ''}</small></td>
                                            <td>${App.escapeHtml(s.subject)}</td>
                                            <td>${App.escapeHtml(s.classroom)}</td>
                                            <td>${App.formatTime(s.start_time)} - ${App.formatTime(s.end_time)}</td>
                                            <td><span class="badge badge-${s.status}">${s.status}</span></td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    ` : ''}

                    ${!asSubstitute.length && !asOriginal.length ? '<div class="empty-state">No substitution records</div>' : ''}
                </div>
            `;
        } catch (e) {
            content.innerHTML = `<div class="empty-state">Error: ${e.message}</div>`;
        }
    }
};
