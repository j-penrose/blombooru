class PendingEntitiesPanel {
    constructor(containerElement, session, options = {}) {
        this.container = containerElement;
        this.session = session;
        this.options = options;
        this.pendingData = { pending_tags: [], pending_albums: [] };
        this.isLoading = false;

        this.init();
    }

    init() {
        this.container.innerHTML = `
            <div class="pending-entities-panel surface border p-4 mb-4 text-xs" style="display: none;">
                <div class="flex items-center justify-between border-b pb-2 mb-3">
                    <div class="flex items-center gap-3 w-full">
                        <span class="text-xs font-bold whitespace-nowrap overflow-hidden text-ellipsis">${window.i18n.t('upload.pending.title')}</span>
                    </div>
                </div>
                <p class="text-secondary text-[11px] mb-3">
                    ${window.i18n.t('upload.pending.description')}
                </p>

                <!-- Tags Section -->
                <div id="pending-tags-container" class="mb-3">
                    <h4 class="text-[11px] font-bold text-secondary uppercase tracking-wider mb-2">
                        ${window.i18n.t('upload.pending.new_tags')} (<span id="pending-tags-count">0</span>)
                    </h4>
                    <div id="pending-tags-list" class="flex flex-wrap gap-2"></div>
                </div>

                <!-- Albums Section -->
                <div id="pending-albums-container">
                    <h4 class="text-[11px] font-bold text-secondary uppercase tracking-wider mb-2">
                        ${window.i18n.t('upload.pending.new_albums')} (<span id="pending-albums-count">0</span>)
                    </h4>
                    <div id="pending-albums-list" class="flex flex-wrap gap-2"></div>
                </div>
            </div>
        `;

        this.setupSessionListeners();
    }

    setupSessionListeners() {
        this.session.on('itemAdded', () => this.debouncedRefresh());
        this.session.on('itemUpdated', () => this.debouncedRefresh());
        this.session.on('itemRemoved', () => this.debouncedRefresh());
        this.session.on('sessionCleared', () => {
            this.pendingData = { pending_tags: [], pending_albums: [] };
            this.render();
        });
    }

    debouncedRefresh() {
        clearTimeout(this.refreshTimeout);
        this.refreshTimeout = setTimeout(() => this.refresh(), 300);
    }

    async refresh() {
        if (!this.session.sessionId) {
            this.pendingData = { pending_tags: [], pending_albums: [] };
            this.render();
            return;
        }
        this.isLoading = true;

        try {
            this.pendingData = await this.session.fetchPendingEntities();
            this.render();
        } catch (e) {
            console.error('Error refreshing pending entities:', e);
        } finally {
            this.isLoading = false;
        }
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    render() {
        const panel = this.container.querySelector('.pending-entities-panel');
        const tags = this.pendingData.pending_tags || [];
        const albums = this.pendingData.pending_albums || [];
        const total = tags.length + albums.length;

        // Hide completely if empty
        if (!panel) return;
        if (total === 0) {
            panel.style.display = 'none';
            return;
        }
        panel.style.display = 'block';

        const tagsCount = this.container.querySelector('#pending-tags-count');
        const albumsCount = this.container.querySelector('#pending-albums-count');
        const tagsList = this.container.querySelector('#pending-tags-list');
        const albumsList = this.container.querySelector('#pending-albums-list');
        const tagsContainer = this.container.querySelector('#pending-tags-container');
        const albumsContainer = this.container.querySelector('#pending-albums-container');

        if (tagsCount) tagsCount.textContent = tags.length.toString();
        if (albumsCount) albumsCount.textContent = albums.length.toString();

        // Render Pending Tags as style-conforming pills with category selector
        if (tagsContainer) {
            tagsContainer.style.display = tags.length > 0 ? 'block' : 'none';
        }
        if (tagsList && tags.length > 0) {
            tagsList.className = 'flex flex-wrap gap-2';
            tagsList.innerHTML = tags.map(tag => {
                const cat = tag.category || 'general';
                const grayscaleClass = (!tag.user_assigned) ? 'grayscale' : '';
                return `
                    <div class="pending-tag-item inline-flex items-center gap-1 bg border p-1" data-name="${this.escapeHtml(tag.name)}">
                        <div class="custom-select pending-cat-select inline-block align-middle" data-value="${cat}" data-tag="${this.escapeHtml(tag.name)}">
                            <div class="custom-select-trigger tag-text tag ${cat} ${grayscaleClass} cursor-pointer select-none" style="display: inline-flex; align-items: center; gap: 4px; white-space: nowrap;">
                                <span class="text-xs">${this.escapeHtml(tag.name)}</span>
                                <span class="custom-select-value" style="display: none;"></span>
                                ${window.Icons.chevronDown({ size: 10, class: 'custom-select-arrow flex-shrink-0 transition-transform duration-200', style: 'display: block;' })}
                            </div>
                            <div class="custom-select-dropdown bg border border-primary max-h-40 overflow-y-auto shadow-lg z-50 min-w-25">
                                <div class="custom-select-option px-3 py-1.5 cursor-pointer hover:surface text-xs ${cat === 'general' ? 'selected' : ''}" data-value="general">${window.i18n.t('common.tag_category_general')}</div>
                                <div class="custom-select-option px-3 py-1.5 cursor-pointer hover:surface text-xs ${cat === 'artist' ? 'selected' : ''}" data-value="artist">${window.i18n.t('common.tag_category_artist')}</div>
                                <div class="custom-select-option px-3 py-1.5 cursor-pointer hover:surface text-xs ${cat === 'character' ? 'selected' : ''}" data-value="character">${window.i18n.t('common.tag_category_character')}</div>
                                <div class="custom-select-option px-3 py-1.5 cursor-pointer hover:surface text-xs ${cat === 'copyright' ? 'selected' : ''}" data-value="copyright">${window.i18n.t('common.tag_category_copyright')}</div>
                                <div class="custom-select-option px-3 py-1.5 cursor-pointer hover:surface text-xs ${cat === 'meta' ? 'selected' : ''}" data-value="meta">${window.i18n.t('common.tag_category_meta')}</div>
                            </div>
                        </div>
                        <span class="pending-tag-count-badge text-[10px] text-secondary hover:text-primary cursor-pointer transition-colors"
                            title="${window.i18n.t('upload.pending.used_in_media', { count: tag.used_by.length })}">
                            ${window.i18n.t('upload.pending.media_count', { count: tag.used_by.length })}
                        </span>
                        <button type="button" class="pending-remove-btn text-secondary hover:text-danger transition-colors cursor-pointer p-0.5 flex items-center justify-center">
                            ${window.Icons.trash({ size: 12, class: 'transition-colors' })}
                        </button>
                    </div>
                `;
            }).join('');

            this.setupTagRowEvents();
        }

        // Render Pending Albums
        if (albumsContainer) {
            albumsContainer.style.display = albums.length > 0 ? 'block' : 'none';
        }
        if (albumsList && albums.length > 0) {
            albumsList.className = 'flex flex-wrap gap-2';
            albumsList.innerHTML = albums.map(alb => `
                <div class="inline-flex items-center gap-1 bg border p-1">
                    <span class="font-mono text-xs flex items-center gap-1.5" title="${this.escapeHtml(alb.path)}">
                        ${window.Icons.folder({ size: 12, class: 'text-secondary' })}
                        <span>${this.escapeHtml(alb.path)}</span>
                    </span>
                    <span class="text-[10px] text-secondary" title="${window.i18n.t('upload.pending.used_in_media', { count: alb.used_by.length })}">
                        ${window.i18n.t('upload.pending.media_count', { count: alb.used_by.length })}
                    </span>
                </div>
            `).join('');
        }
    }

    setupTagRowEvents() {
        const chips = this.container.querySelectorAll('.pending-tag-item');
        chips.forEach(chip => {
            const tagName = chip.dataset.name;
            const tagObj = (this.pendingData.pending_tags || []).find(t => t.name.toLowerCase() === tagName.toLowerCase());

            // Category select
            const catSelectEl = chip.querySelector('.pending-cat-select');
            if (catSelectEl && typeof CustomSelect !== 'undefined') {
                new CustomSelect(catSelectEl);
                catSelectEl.addEventListener('change', async (e) => {
                    const newCat = e.detail.value;
                    await this.session.updatePendingTag(tagName, { category: newCat });
                });
            }

            // Click badge to highlight referencing cards
            const countBadge = chip.querySelector('.pending-tag-count-badge');
            if (countBadge && tagObj) {
                countBadge.addEventListener('click', () => {
                    if (this.options.onHighlightItems) {
                        this.options.onHighlightItems(tagObj.used_by);
                    }
                });
            }

            // Remove tag from all items
            const removeBtn = chip.querySelector('.pending-remove-btn');
            if (removeBtn) {
                removeBtn.addEventListener('click', async () => {
                    await this.session.updatePendingTag(tagName, { remove: true });
                });
            }
        });
    }
}

window.PendingEntitiesPanel = PendingEntitiesPanel;
