class BooruConfigManager {
    constructor() {
        this.container = document.getElementById('booru-config-section');
        if (this.container) {
            this.init();
        }
    }

    init() {
        this.tableBody = this.container.querySelector('#booru-config-table tbody');
        this.form = this.container.querySelector('#booru-config-form');
        this.proxyInput = this.container.querySelector('#booru-proxy-url');
        this.testProxyBtn = this.container.querySelector('#test-booru-proxy-btn');
        this.saveProxyBtn = this.container.querySelector('#save-booru-proxy-btn');

        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        if (this.testProxyBtn) {
            this.testProxyBtn.addEventListener('click', () => this.handleTestProxy());
        }

        if (this.saveProxyBtn) {
            this.saveProxyBtn.addEventListener('click', () => this.handleSaveProxy());
        }

        this.loadConfigs();
        this.loadProxySetting();
    }

    showStatus(message, type = 'info') {
        if (typeof app !== 'undefined' && app.showNotification) {
            app.showNotification(message, type);
        } else {
            console.warn('App notification helper not available:', message);
            alert(message);
        }
    }

    async loadConfigs() {
        if (!this.tableBody) return;

        try {
            const response = await fetch('/api/booru-config/');
            if (!response.ok) throw new Error('Failed to load configs');
            const configs = await response.json();
            this.renderTable(configs);
        } catch (e) {
            console.error('Error loading booru configs:', e);
            this.tableBody.innerHTML = `<tr><td colspan="4" class="text-center py-2 text-danger">${window.i18n.t('admin.settings.booru_config.no_configs')}</td></tr>`;
        }
    }

    renderTable(configs) {
        if (configs.length === 0) {
            this.tableBody.innerHTML = `<tr><td colspan="4" class="text-center py-2 text-secondary text-xs">${window.i18n.t('admin.settings.booru_config.no_configs')}</td></tr>`;
            return;
        }

        this.tableBody.innerHTML = configs.map(config => `
            <tr class="border-b last:border-b-0">
                <td class="p-2 text-xs font-mono break-all">${this.escapeHtml(config.domain)}</td>
                <td class="p-2 text-xs break-all">${this.escapeHtml(config.username || '-')}</td>
                <td class="p-2 text-xs">
                    ${config.has_api_key ? `<span class="text-success">${window.i18n.t('admin.settings.booru_config.has_key')}</span>` : `<span class="text-secondary">${window.i18n.t('common.none')}</span>`}
                </td>
                <td class="p-2 text-xs text-right">
                    <button class="text-danger hover:text-danger transition-colors cursor-pointer" onclick="window.booruConfigManager.deleteConfig('${config.domain}')">
                        ${window.Icons.trash({ size: 14 })}
                    </button>
                </td>
            </tr>
        `).join('');
    }

    async handleSubmit(e) {
        e.preventDefault();
        const domainInput = this.form.querySelector('[name="domain"]');
        const usernameInput = this.form.querySelector('[name="username"]');
        const apiKeyInput = this.form.querySelector('[name="api_key"]');

        const data = {
            domain: domainInput.value.trim(),
            username: usernameInput.value.trim() || null,
            api_key: apiKeyInput.value.trim() || null
        };

        if (!data.domain) {
            this.showStatus(window.i18n.t('admin.settings.booru_config.error_domain_required'), 'error');
            return;
        }

        try {
            const response = await fetch('/api/booru-config/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message_key || error.detail || 'Failed to save configuration');
            }

            this.showStatus(window.i18n.t('admin.settings.booru_config.save_success'), 'success');

            domainInput.value = '';
            usernameInput.value = '';
            apiKeyInput.value = '';

            this.loadConfigs();
        } catch (e) {
            console.error('Save error:', e);
            const errorMsg = app.translateError(e.message) || window.i18n.t('admin.settings.booru_config.error_save_failed');
            this.showStatus(errorMsg, 'error');
        }
    }

    deleteConfig(domain) {
        new ModalHelper({
            type: 'danger',
            title: window.i18n.t('admin.settings.booru_config.delete_confirm_title') || 'Delete Configuration',
            message: window.i18n.t('admin.settings.booru_config.delete_confirm', { domain }),
            confirmText: window.i18n.t('common.delete'),
            confirmId: 'confirm-delete-config',
            onConfirm: async () => {
                try {
                    const response = await fetch(`/api/booru-config/${encodeURIComponent(domain)}`, {
                        method: 'DELETE'
                    });

                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.message_key || error.detail || 'Failed to delete');
                    }

                    const successMsg = window.i18n.t('admin.settings.booru_config.delete_success', { domain });
                    this.showStatus(successMsg, 'success');
                    this.loadConfigs();
                } catch (e) {
                    const errorMsg = app.translateError(e.message) || window.i18n.t('admin.settings.booru_config.error_delete_failed');
                    this.showStatus(errorMsg, 'error');
                }
            }
        }).show();
    }

    async loadProxySetting() {
        if (!this.proxyInput) return;
        try {
            const response = await fetch('/api/admin/settings');
            if (response.ok) {
                const data = await response.json();
                if (data.booru_proxy_url) {
                    this.proxyInput.value = data.booru_proxy_url;
                }
            }
        } catch (e) {
            console.error('Error loading booru proxy setting:', e);
        }
    }

    async handleTestProxy() {
        const proxyUrl = this.proxyInput.value.trim();
        if (!proxyUrl) {
            this.showStatus(window.i18n.t('admin.settings.booru_config.error_proxy_empty'), 'error');
            return;
        }

        if (this.testProxyBtn) {
            this.testProxyBtn.disabled = true;
        }

        try {
            const response = await fetch('/api/booru-config/test-proxy', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ proxy_url: proxyUrl })
            });

            const result = await response.json();
            if (response.ok && result.success) {
                const msg = window.i18n.t('admin.settings.booru_config.proxy_test_success', { ip: result.origin_ip || 'unknown' });
                this.showStatus(msg, 'success');
            } else {
                const err = result.error || 'Connection failed';
                const msg = window.i18n.t('admin.settings.booru_config.proxy_test_failed', { error: err });
                this.showStatus(msg, 'error');
            }
        } catch (e) {
            console.error('Test proxy error:', e);
            const msg = window.i18n.t('admin.settings.booru_config.proxy_test_failed', { error: e.message });
            this.showStatus(msg, 'error');
        } finally {
            if (this.testProxyBtn) {
                this.testProxyBtn.disabled = false;
            }
        }
    }

    async handleSaveProxy() {
        const proxyUrl = this.proxyInput.value.trim();
        if (this.saveProxyBtn) {
            this.saveProxyBtn.disabled = true;
        }

        try {
            const response = await fetch('/api/admin/settings', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ booru_proxy_url: proxyUrl || null })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message_key || error.detail || 'Failed to save proxy setting');
            }

            this.showStatus(window.i18n.t('admin.settings.booru_config.save_success'), 'success');
        } catch (e) {
            console.error('Save proxy error:', e);
            const errorMsg = app.translateError(e.message) || window.i18n.t('admin.settings.booru_config.error_save_failed');
            this.showStatus(errorMsg, 'error');
        } finally {
            if (this.saveProxyBtn) {
                this.saveProxyBtn.disabled = false;
            }
        }
    }

    escapeHtml(text) {
        if (!text) return text;
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

if (document.getElementById('booru-config-section')) {
    window.booruConfigManager = new BooruConfigManager();
}
