class FormatRegistryHelper {
    constructor() {
        this.formats = {};
        this.aliasMap = {};
        
        const dataTag = document.getElementById('format-registry-data');
        if (dataTag) {
            try {
                this.formats = JSON.parse(dataTag.textContent);
                for (const fmt of Object.values(this.formats)) {
                    if (Array.isArray(fmt.aliases)) {
                        for (const alias of fmt.aliases) {
                            this.aliasMap[alias.toLowerCase()] = fmt;
                        }
                    }
                }
            } catch (e) {
                console.error("Failed to parse inline format registry data:", e);
            }
        }
    }

    _extractExtension(filenameOrUrl) {
        if (!filenameOrUrl) return "";
        let clean = String(filenameOrUrl).split('#')[0].split('?')[0].toLowerCase();
        if (clean.endsWith('.tar.gz')) return '.tar.gz';
        if (clean.includes('.')) {
            return '.' + clean.split('.').pop();
        }
        if (!clean.startsWith('.')) {
            return '.' + clean;
        }
        return clean;
    }

    getFormat(filenameOrExt) {
        if (!filenameOrExt) return null;
        const ext = this._extractExtension(filenameOrExt);
        return this.formats[ext] || this.aliasMap[ext] || null;
    }

    isCategory(filename, category) {
        const fmt = this.getFormat(filename);
        return fmt && fmt.category === category;
    }

    isVideo(filename) {
        return this.isCategory(filename, 'video');
    }

    isImage(filename) {
        return this.isCategory(filename, 'image');
    }
    
    isArchive(filename) {
        return this.isCategory(filename, 'archive');
    }

    isValidMedia(fileOrName) {
        if (!fileOrName) return false;
        if (typeof fileOrName === 'object' && fileOrName.name) {
            if (fileOrName.type && this.isValidMimeType(fileOrName.type, ['image', 'video'])) {
                return true;
            }
            return this.isImage(fileOrName.name) || this.isVideo(fileOrName.name);
        }
        return this.isImage(fileOrName) || this.isVideo(fileOrName);
    }

    isValidMimeType(mimeType, categories = []) {
        if (!mimeType) return false;
        const mime = mimeType.split(';')[0].trim().toLowerCase();
        for (const fmt of Object.values(this.formats)) {
            if (fmt.mime_type === mime) {
                if (categories.length === 0 || categories.includes(fmt.category)) {
                    return true;
                }
            }
        }
        if (categories.includes('image') && mime.startsWith('image/')) return true;
        if (categories.includes('video') && mime.startsWith('video/')) return true;
        return false;
    }

    isValidFile(file) {
        if (!file) return false;
        if (file.type && this.isValidMimeType(file.type, ['image', 'video'])) {
            return true;
        }
        const ext = this._extractExtension(file.name);
        const fmt = this.formats[ext];
        return fmt && (fmt.category === 'image' || fmt.category === 'video');
    }

    getAcceptString(categories = ['image', 'video']) {
        let acceptList = [];
        for (const cat of categories) {
            if (cat === 'image') acceptList.push('image/*');
            if (cat === 'video') acceptList.push('video/*');
        }

        for (const [ext, fmt] of Object.entries(this.formats)) {
            if (categories.includes(fmt.category)) {
                acceptList.push(ext);
                if (fmt.category !== 'image' && fmt.category !== 'video') {
                    acceptList.push(fmt.mime_type);
                }
            }
        }
        
        return [...new Set(acceptList)].join(',');
    }
    
    getValidTypes(categories = ['image', 'video']) {
        let validTypes = [];
        for (const fmt of Object.values(this.formats)) {
            if (categories.length === 0 || categories.includes(fmt.category)) {
                validTypes.push(fmt.mime_type);
            }
        }
        return [...new Set(validTypes)];
    }
}

window.FormatRegistry = new FormatRegistryHelper();
