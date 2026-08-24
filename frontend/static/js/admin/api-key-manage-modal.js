class ApiKeyManageModal {
    constructor(options = {}) {
        this.options = {
            id: 'api-key-manage-modal',
            onUpdate: options.onUpdate || (() => { }),
            onRevoke: options.onRevoke || (() => { }),
            ...options
        };
        this.keyData = null;
        this.element = null;
        this.isUpdating = false;
    }

    show(keyData) {
        this.keyData = keyData;
        if (!this.element) {
            this.create();
        } else {
            this.updateContent();
        }
        this.element.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    hide() {
        if (this.element) {
            this.element.style.display = 'none';
        }
        document.body.style.overflow = '';
    }

    create() {
        const modal = document.createElement('div');
        modal.id = this.options.id;
        modal.className = 'fixed inset-0 flex items-center justify-center z-50';
        modal.style.background = 'rgba(0, 0, 0, 0.5)';
        modal.style.display = 'none';

        modal.innerHTML = `
            <div class="surface p-4 sm:p-6 border shadow-2xl w-full max-w-lg mx-4 relative max-h-[90vh] overflow-y-auto">
                <div class="flex items-center justify-between mb-3 pb-2 border-b flex-shrink-0">
                    <h2 class="text-base sm:text-lg font-bold truncate">${window.i18n.t('modal.manage_api_key.title')}</h2>
                    <span id="akm-key-prefix" class="font-mono text-xs bg surface px-2 py-0.5 border"></span>
                </div>

                <div class="mb-3">
                    <div class="flex gap-2">
                        <input type="text" id="akm-name-input"
                            class="flex-1 bg px-3 py-1.5 border text-xs hover:border-primary transition-colors focus:outline-none focus:border-primary"
                            placeholder="${window.i18n.t('modal.api_key_name.placeholder')}"
                            maxlength="64"
                            autocomplete="off">
                        <button type="button" id="akm-rename-btn" class="btn-primary cursor-pointer">
                            ${window.i18n.t('common.save')}
                        </button>
                    </div>
                </div>

                <div class="flex flex-col gap-3 mb-3" id="akm-levels-container">
                    <!-- Read-Only -->
                    <button class="akm-level-btn text-left p-4 bg hover:border-primary transition-all border flex items-center gap-3 relative cursor-pointer" data-level="read">
                        <div class="text-success shrink-0">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                                <circle cx="12" cy="12" r="3"></circle>
                            </svg>
                        </div>
                        <div class="flex-1">
                            <div class="font-bold text-sm">${window.i18n.t('modal.manage_api_key.level_read_title')}</div>
                            <div class="text-xs opacity-70">${window.i18n.t('modal.manage_api_key.level_read_desc')}</div>
                        </div>
                    </button>

                    <!-- Upload & Edit -->
                    <button class="akm-level-btn text-left p-4 bg hover:border-primary transition-all border flex items-center gap-3 relative cursor-pointer" data-level="write">
                        <div class="mt-0.5 text-warning shrink-0">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                                <polyline points="17 8 12 3 7 8"></polyline>
                                <line x1="12" y1="3" x2="12" y2="15"></line>
                            </svg>
                        </div>
                        <div class="flex-1">
                            <div class="font-bold text-sm">${window.i18n.t('modal.manage_api_key.level_write_title')}</div>
                            <div class="text-xs opacity-70">${window.i18n.t('modal.manage_api_key.level_write_desc')}</div>
                        </div>
                    </button>

                    <!-- Full Admin -->
                    <button class="akm-level-btn text-left p-4 bg hover:border-primary transition-all border flex items-center gap-3 relative cursor-pointer" data-level="admin">
                        <div class="mt-0.5 text-danger shrink-0">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                            </svg>
                        </div>
                        <div class="flex-1">
                            <div class="font-bold text-sm">${window.i18n.t('modal.manage_api_key.level_admin_title')}</div>
                            <div class="text-xs opacity-70">${window.i18n.t('modal.manage_api_key.level_admin_desc')}</div>
                        </div>
                    </button>
                </div>

                <div class="flex justify-between items-center pt-3 border-t">
                    <button class="akm-revoke-btn btn-danger cursor-pointer">
                        ${window.i18n.t('modal.manage_api_key.revoke_btn')}
                    </button>
                    <button class="akm-close-btn btn cursor-pointer">
                        ${window.i18n.t('common.close')}
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.element = modal;
        this.setupListeners();
        this.updateContent();
    }

    updateContent() {
        if (!this.element || !this.keyData) return;

        const prefixEl = this.element.querySelector('#akm-key-prefix');
        if (prefixEl) prefixEl.textContent = `${this.keyData.key_prefix}...`;

        const nameInput = this.element.querySelector('#akm-name-input');
        if (nameInput && document.activeElement !== nameInput) {
            nameInput.value = this.keyData.name || '';
        }

        const currentLevel = this.keyData.permission || 'read';

        this.element.querySelectorAll('.akm-level-btn').forEach(btn => {
            const level = btn.dataset.level;
            const isCurrent = (level === currentLevel);

            if (isCurrent) {
                btn.classList.add('border-primary', 'surface');
            } else {
                btn.classList.remove('border-primary', 'surface');
            }
        });
    }

    setupListeners() {
        if (!this.element) return;

        // Close on backdrop or close button
        this.element.addEventListener('click', (e) => {
            if (e.target.closest('.akm-close-btn') || e.target === this.element) {
                this.hide();
            }
        });

        // Rename input and button
        const nameInput = this.element.querySelector('#akm-name-input');
        nameInput?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.saveName();
            }
        });
        this.element.querySelector('#akm-rename-btn')?.addEventListener('click', () => {
            this.saveName();
        });

        // Level selection
        this.element.querySelectorAll('.akm-level-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const targetLevel = btn.dataset.level;
                if (!targetLevel || targetLevel === this.keyData?.permission || this.isUpdating) return;
                await this.setLevel(targetLevel);
            });
        });

        // Revoke button
        this.element.querySelector('.akm-revoke-btn')?.addEventListener('click', () => {
            if (!this.keyData) return;
            const keyId = this.keyData.id;
            this.hide();
            this.options.onRevoke(keyId);
        });

        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.element && this.element.style.display !== 'none') {
                this.hide();
            }
        });
    }

    async saveName() {
        if (!this.keyData || this.isUpdating) return;
        const nameInput = this.element.querySelector('#akm-name-input');
        const newName = nameInput ? nameInput.value.trim() : '';
        if (newName === (this.keyData.name || '')) return;

        this.isUpdating = true;
        try {
            const response = await app.apiCall(`/api/admin/api-keys/${this.keyData.id}`, {
                method: 'PATCH',
                body: JSON.stringify({ name: newName })
            });

            this.keyData.name = response.name;
            this.updateContent();
            app.showNotification(window.i18n.t('notifications.admin.api_key_updated'), 'success');
            this.options.onUpdate(this.keyData);
        } catch (error) {
            app.showNotification(error.message, 'error', window.i18n.t('notifications.admin.error_updating_api_key'));
        } finally {
            this.isUpdating = false;
        }
    }

    async setLevel(level) {
        if (!this.keyData || this.isUpdating) return;
        this.isUpdating = true;

        try {
            const response = await app.apiCall(`/api/admin/api-keys/${this.keyData.id}`, {
                method: 'PATCH',
                body: JSON.stringify({ permission: level })
            });

            this.keyData.permission = response.permission || level;
            this.updateContent();
            app.showNotification(window.i18n.t('notifications.admin.api_key_updated'), 'success');
            this.options.onUpdate(this.keyData);
        } catch (error) {
            app.showNotification(error.message, 'error', window.i18n.t('notifications.admin.error_updating_api_key'));
        } finally {
            this.isUpdating = false;
        }
    }
}

if (typeof window !== 'undefined') {
    window.ApiKeyManageModal = ApiKeyManageModal;
}
