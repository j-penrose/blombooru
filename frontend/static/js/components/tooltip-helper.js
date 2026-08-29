class TooltipHelper {
    constructor(options = {}) {
        this.options = {
            id: options.id || 'media-tooltip',
            delay: options.delay || 300,
            maxWidth: options.maxWidth || 300,
            ...options
        };

        this.tooltipElement = null;
        this.activeElement = null;
        this.hoverTimeouts = new Map();
        this.scrollHandler = null;

        this.init();
    }

    init() {
        this.createTooltip();
        this.setupScrollHandler();
    }

    createTooltip() {
        // Check if tooltip already exists
        let tooltip = document.getElementById(this.options.id);
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = this.options.id;
            document.body.appendChild(tooltip);
        }
        tooltip.className = 'absolute pointer-events-none z-[10000] px-3 py-2 text-xs leading-normal border border-border shadow-lg break-words hidden';
        tooltip.style.backgroundColor = 'var(--tag-text)';
        tooltip.style.color = 'var(--tag-general)';
        tooltip.style.maxWidth = `${this.options.maxWidth}px`;
        this.tooltipElement = tooltip;
        return this.tooltipElement;
    }

    _escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    show(element, content) {
        if (!content) return;

        if (typeof content === 'string') {
            this.tooltipElement.textContent = content;
        } else if (Array.isArray(content)) {
            if (content.length === 0) return;

            const categoryOrder = ['artist', 'character', 'copyright', 'general', 'meta'];

            const sortedTags = [...content].sort((a, b) => {
                const nameA = typeof a === 'string' ? a : (a.name || String(a));
                const nameB = typeof b === 'string' ? b : (b.name || String(b));
                const catA = typeof a === 'object' && a.category ? a.category.toLowerCase() : 'general';
                const catB = typeof b === 'object' && b.category ? b.category.toLowerCase() : 'general';

                const catIndexA = categoryOrder.indexOf(catA);
                const catIndexB = categoryOrder.indexOf(catB);
                const orderA = catIndexA === -1 ? 99 : catIndexA;
                const orderB = catIndexB === -1 ? 99 : catIndexB;

                if (orderA !== orderB) {
                    return orderA - orderB;
                }
                return nameA.localeCompare(nameB);
            });

            const html = sortedTags.map(item => {
                const name = typeof item === 'string' ? item : (item.name || String(item));
                const category = typeof item === 'object' && item.category ? item.category.toLowerCase() : 'general';
                const validCategory = categoryOrder.includes(category) ? category : 'general';
                return `<span class="font-medium" style="color: var(--tag-${validCategory});">${this._escapeHtml(name)}</span>`;
            }).join(' ');

            this.tooltipElement.innerHTML = html;
        } else if (typeof content === 'object') {
            if (content.html) {
                this.tooltipElement.innerHTML = content.html;
            } else if (content.text) {
                this.tooltipElement.textContent = content.text;
            } else {
                return;
            }
        } else {
            return;
        }

        this.tooltipElement.classList.remove('hidden');
        this.position(element);
        this.activeElement = element;
    }

    position(element) {
        const rect = element.getBoundingClientRect();
        const tooltipRect = this.tooltipElement.getBoundingClientRect();

        // Calculate position (above the element by default)
        let top = rect.top - tooltipRect.height - 10;
        let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);

        // If tooltip would go off top of screen, show below instead
        if (top < 10) {
            top = rect.bottom + 10;
        }

        // Keep tooltip within viewport horizontally
        if (left < 10) {
            left = 10;
        } else if (left + tooltipRect.width > window.innerWidth - 10) {
            left = window.innerWidth - tooltipRect.width - 10;
        }

        // Add scroll offset
        top += window.scrollY;
        left += window.scrollX;

        this.tooltipElement.style.top = `${top}px`;
        this.tooltipElement.style.left = `${left}px`;
    }

    hide() {
        if (this.tooltipElement) {
            this.tooltipElement.classList.add('hidden');
        }
        this.activeElement = null;
    }

    // Add hover events to an element
    addToElement(element, contentProvider, options = {}) {
        const delay = options.delay || this.options.delay;

        element.addEventListener('mouseenter', () => {
            // Clear any existing timeout for this element
            if (this.hoverTimeouts.has(element)) {
                clearTimeout(this.hoverTimeouts.get(element));
            }

            // Set new timeout
            const timeoutId = setTimeout(() => {
                const content = typeof contentProvider === 'function'
                    ? contentProvider(element)
                    : contentProvider;

                if (content) {
                    this.show(element, content);
                }

                this.hoverTimeouts.delete(element);
            }, delay);

            this.hoverTimeouts.set(element, timeoutId);
        });

        element.addEventListener('mouseleave', () => {
            // Clear timeout if still pending
            if (this.hoverTimeouts.has(element)) {
                clearTimeout(this.hoverTimeouts.get(element));
                this.hoverTimeouts.delete(element);
            }
            this.hide();
        });
    }

    // Setup scroll handler to reposition tooltip if visible
    setupScrollHandler() {
        this.scrollHandler = () => {
            if (this.activeElement && !this.tooltipElement.classList.contains('hidden')) {
                this.position(this.activeElement);
            }
        };

        window.addEventListener('scroll', this.scrollHandler, { passive: true });
    }

    // Cleanup method
    destroy() {
        // Clear all timeouts
        for (const timeoutId of this.hoverTimeouts.values()) {
            clearTimeout(timeoutId);
        }
        this.hoverTimeouts.clear();

        // Remove scroll handler
        if (this.scrollHandler) {
            window.removeEventListener('scroll', this.scrollHandler);
        }

        // Remove tooltip element
        if (this.tooltipElement && this.tooltipElement.parentNode) {
            this.tooltipElement.parentNode.removeChild(this.tooltipElement);
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TooltipHelper;
}
