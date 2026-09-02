class BulkManageTagsModal {
    constructor(options = {}) {
        this.options = {
            id: 'bulk-manage-tags-modal',
            onAction: options.onAction || (() => { }), // (action) => {}
            ...options
        };
        this.element = null;
    }

    show() {
        if (!this.element) {
            this.create();
        }
        this.element.style.display = 'flex';

        // Prevent body scroll
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
            <div class="surface p-2 sm:p-6 border shadow-2xl w-full max-w-sm mx-4 relative">
                <div class="flex items-center mb-4 flex-shrink-0">
                    <h2 class="text-base sm:text-lg font-bold truncate">${window.i18n.t('common.manage_tags')}</h2>
                </div>
                
                <div class="flex flex-col gap-3">
                    <button class="action-btn text-left p-4 bg hover:border-primary hover:text-primary transition-colors border flex items-center gap-3 cursor-pointer" data-action="manual">
                        ${window.Icons.edit({ size: 20 })}
                        <div class="flex-1">
                            <div class="font-bold text-sm">${window.i18n.t('common.manual_tag_editor')}</div>
                            <div class="text-xs opacity-70">${window.i18n.t('bulk_modal.menu.manual_desc')}</div>
                        </div>
                        ${window.Icons.chevronRight({ size: 16, class: 'opacity-50' })}
                    </button>

                    <button class="action-btn text-left p-4 bg hover:border-primary hover:text-primary transition-colors border flex items-center gap-3 cursor-pointer" data-action="ai_tags">
                        ${window.Icons.messageSquare({ size: 20 })}
                        <div class="flex-1">
                            <div class="font-bold text-sm">${window.i18n.t('bulk_modal.menu.ai_tags')}</div>
                            <div class="text-xs opacity-70">${window.i18n.t('bulk_modal.menu.ai_desc')}</div>
                        </div>
                        ${window.Icons.chevronRight({ size: 16, class: 'opacity-50' })}
                    </button>

                    <button class="action-btn text-left p-4 bg hover:border-primary hover:text-primary transition-colors border flex items-center gap-3 cursor-pointer" data-action="wd_tagger">
                        ${window.Icons.camera({ size: 20 })}
                        <div class="flex-1">
                            <div class="font-bold text-sm">${window.i18n.t('bulk_modal.menu.wd_tagger')}</div>
                            <div class="text-xs opacity-70">${window.i18n.t('bulk_modal.menu.wd_desc')}</div>
                        </div>
                        ${window.Icons.chevronRight({ size: 16, class: 'opacity-50' })}
                    </button>
                </div>
                <div class="flex gap-2 mt-4">
                    <button class="close-btn flex-1 px-4 py-2 border bg hover:border-primary hover:text-primary text text-xs transition-colors cursor-pointer">${window.i18n.t('common.close')}</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        this.element = modal;
        this.setupResultListeners();
    }

    setupResultListeners() {
        if (!this.element) return;

        this.element.addEventListener('click', (e) => {
            // Close button
            if (e.target.closest('.close-btn') || e.target === this.element) {
                this.hide();
                return;
            }

            // Action buttons
            const btn = e.target.closest('.action-btn');
            if (btn) {
                const action = btn.dataset.action;
                this.hide();
                if (this.options.onAction) {
                    this.options.onAction(action);
                }
            }
        });

        // Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.element.style.display === 'flex') {
                this.hide();
            }
        });
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = BulkManageTagsModal;
}
