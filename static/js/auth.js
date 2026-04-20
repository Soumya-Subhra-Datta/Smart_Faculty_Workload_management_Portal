/**
 * ============================================================================
 * Auth Module — Login form handler
 * ============================================================================
 */

const AuthModule = {
    init() {
        const form = document.getElementById('login-form');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        // Also handle button click
        document.getElementById('login-btn').addEventListener('click', () => this.handleLogin());
    },

    async handleLogin() {
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value.trim();
        const errorEl = document.getElementById('login-error');
        const btn = document.getElementById('login-btn');

        if (!username || !password) {
            errorEl.textContent = 'Please enter both username and password.';
            errorEl.classList.remove('hidden');
            return;
        }

        // Show loading state
        btn.disabled = true;
        btn.innerHTML = '<span>Signing in...</span><div class="spinner" style="width:18px;height:18px;border-width:2px"></div>';
        errorEl.classList.add('hidden');

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Login failed');
            }

            // Success — pass to App
            App.onLogin(data.token, data.user);

        } catch (error) {
            errorEl.textContent = error.message;
            errorEl.classList.remove('hidden');
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<span>Sign In</span><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
        }
    }
};

// Initialize auth module
document.addEventListener('DOMContentLoaded', () => AuthModule.init());
