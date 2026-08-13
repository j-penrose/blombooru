class KeybindingManager {
    constructor() {
        this.bindings = {};
        this._bootstrap();
    }

    _bootstrap() {
        const el = document.getElementById('keybindings-data');
        if (el) {
            try {
                this.bindings = JSON.parse(el.textContent || '{}');
            } catch (e) {
                console.warn('keybinding-manager: failed to parse inline data', e);
                this.bindings = {};
            }
        }
    }

    async refresh() {
        try {
            const res = await fetch('/api/instance-info');
            if (!res.ok) return;
            const data = await res.json();
            if (data && data.keybindings) {
                this.bindings = data.keybindings;
            }
        } catch (e) {
            console.warn('keybinding-manager: refresh failed', e);
        }
    }

    matches(event, actionId) {
        if (!actionId) return false;
        const b = this.bindings[actionId];
        if (!b) return false;

        // Modifier guard -- this app only supports modifier-free shortcuts.
        if (event.ctrlKey || event.shiftKey || event.altKey || event.metaKey) {
            return false;
        }

        return event.code === b.code;
    }

    label(actionId) {
        const b = this.bindings[actionId];
        if (!b) return '?';
        return b.key || b.code;
    }

    async labelAsync(actionId) {
        const b = this.bindings[actionId];
        if (!b) return '?';

        if (navigator.keyboard && navigator.keyboard.getLayoutMap) {
            try {
                const layoutMap = await navigator.keyboard.getLayoutMap();
                const layoutKey = layoutMap.get(b.code);
                if (layoutKey) return layoutKey;
            } catch (_) {
                // Ignore and fall through
            }
        }

        return b.key || b.code;
    }
}

window.keybindings = new KeybindingManager();
