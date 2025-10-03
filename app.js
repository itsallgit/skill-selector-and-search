/**
 * Skills Selector Application
 * A single-page application for selecting and managing professional skills
 * Designed to run on AWS S3 with public file access
 */

class SkillsApp {
    constructor() {
        // Configuration (bucket/region overridden by deploy.sh, but also auto-detected for safety)
        const host = window.location.hostname; // e.g. bucket.s3-website-region.amazonaws.com OR bucket.s3.region.amazonaws.com
        let inferredBucket = 'deloitte-skills-selector';
        let inferredRegion = 'us-east-1';
        const websiteMatch = host.match(/^(.*?)\.s3-website[-.]([a-z0-9-]+)\.amazonaws\.com$/);
        const restMatch = host.match(/^(.*?)\.s3\.([a-z0-9-]+)\.amazonaws\.com$/);
        if (websiteMatch) {
            inferredBucket = websiteMatch[1];
            inferredRegion = websiteMatch[2];
        } else if (restMatch) {
            inferredBucket = restMatch[1];
            inferredRegion = restMatch[2];
        }
        this.config = {
            bucketName: 'skills-selector', // placeholder replaced by deploy.sh
            region: 'ap-southeast-2',       // placeholder replaced by deploy.sh
            inferredBucket,
            inferredRegion,
            s3BaseUrl: window.location.origin + window.location.pathname.replace(/\/[^/]*$/, '/'),
            masterSkillsFile: 'skills-master.json',
            usersFile: 'users-master.json',
            maxRetries: 3,
            retryDelay: 1000
        };

        // Application state
        this.state = {
            currentUser: null,
            masterSkills: null,
            selectedSkills: new Map(),
            currentL1: null,
            currentL2: null,
            isLoading: false
        };

        // DOM elements
        this.elements = {};
        
        this.init();
    }

    /**
     * Initialize the application
     */
    async init() {
        try {
            this.initializeElements();
            this.attachEventListeners();
            await this.loadMasterSkills();
            console.log('Skills Selector Application initialized successfully');
        } catch (error) {
            console.error('Failed to initialize application:', error);
            this.showError('Failed to initialize application. Please refresh the page.');
        }
    }

    /**
     * Initialize DOM element references
     */
    initializeElements() {
        this.elements = {
            // Email section
            emailInput: document.getElementById('emailInput'),
            submitEmailBtn: document.getElementById('submitEmailBtn'),
            emailError: document.getElementById('emailError'),
            emailSection: document.getElementById('emailSection'),
            
            // Skills section
            skillsSection: document.getElementById('skillsSection'),
            userEmail: document.getElementById('userEmail'),
            selectedSkillsDisplay: document.getElementById('selectedSkillsDisplay'),
            saveSkillsBtn: document.getElementById('saveSkillsBtn'),
            
            // Skills explorer
            level1Skills: document.getElementById('level1Skills'),
            level2Skills: document.getElementById('level2Skills'),
            level3Skills: document.getElementById('level3Skills'),
            level2Container: document.getElementById('level2Container'),
            level3Container: document.getElementById('level3Container'),
            
            // Loading and messages
            loadingIndicator: document.getElementById('loadingIndicator'),
            toastContainer: document.getElementById('toastContainer')
        };
    }

    /**
     * Attach event listeners to DOM elements
     */
    attachEventListeners() {
        // Email submission
        this.elements.submitEmailBtn.addEventListener('click', () => this.handleEmailSubmit());
        this.elements.emailInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleEmailSubmit();
        });

        // Save skills
        this.elements.saveSkillsBtn.addEventListener('click', () => this.saveUserSkills());
        const viewSelectedBtn = document.getElementById('viewSelectedBtn');
        if (viewSelectedBtn) {
            viewSelectedBtn.addEventListener('click', () => {
                // Scroll to selected skills section
                this.elements.selectedSkillsDisplay.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        }
        // Download button removed per requirements.
    }

    /**
     * Load master skills data
     */
    async loadMasterSkills() {
        try {
            this.setLoading(true);
            const response = await this.fetchWithRetry(this.config.masterSkillsFile);
            
            if (!response.ok) {
                throw new Error(`Failed to load skills data: ${response.status}`);
            }
            
            this.state.masterSkills = await response.json();
            // Normalize to array format with id/level/skills arrays
            if (!Array.isArray(this.state.masterSkills)) {
                this.state.masterSkills = Object.entries(this.state.masterSkills).map(([l1Id, l1]) => ({
                    id: l1Id,
                    level: 1,
                    title: l1.title,
                    description: l1.description,
                    skills: l1.skills ? Object.entries(l1.skills).map(([l2Id, l2]) => ({
                        id: l2Id,
                        level: 2,
                        title: l2.title,
                        description: l2.description,
                        skills: l2.skills ? Object.entries(l2.skills).map(([l3Id, l3]) => ({
                            id: l3Id,
                            level: 3,
                            title: l3.title,
                            description: l3.description,
                            skills: []
                        })) : []
                    })) : []
                }));
            }
            console.log('Master skills loaded (normalized):', this.state.masterSkills);
        } catch (error) {
            console.error('Error loading master skills:', error);
            // Initialize with empty structure if file doesn't exist
            this.state.masterSkills = [];
            this.showToast('Skills data not found. Starting with empty skills list.', 'warning');
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Handle email submission
     */
    async handleEmailSubmit() {
        const email = this.elements.emailInput.value.trim();
        
        if (!this.validateEmail(email)) {
            this.showEmailError('Please enter a valid email address');
            return;
        }

        try {
            this.setLoading(true);
            this.clearEmailError();
            
            const user = await this.loadOrCreateUser(email);
            this.state.currentUser = user;
            
            // Load existing skills if user has them
            if (user.skillsFile) {
                await this.loadUserSkills(user.skillsFile);
            }
            
            this.showSkillsSection();
            this.renderLevel1Skills();
            
        } catch (error) {
            console.error('Error handling email submission:', error);
            this.showEmailError('Failed to load user profile. Please try again.');
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Validate email format
     */
    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Load or create user profile
     */
    async loadOrCreateUser(email) {
        try {
            const users = await this.loadUsersList();

            // Attempt to find existing user
            let user = users.find(u => u.email === email);

            if (!user) {
                user = {
                    email,
                    skillsFile: null,
                    createdAt: new Date().toISOString()
                };
                users.push(user);
                // Try to persist – but don't fail overall if we cannot (e.g. running from local file:// or read-only hosting)
                try {
                    await this.saveFile(this.config.usersFile, users);
                    this.showToast('New profile created successfully!', 'success');
                } catch (saveErr) {
                    console.warn('Could not persist new user list (continuing in memory only):', saveErr);
                    this.showToast('Profile created in session (storage unavailable).', 'warning');
                    // Fallback: store minimal info in localStorage so refresh can rehydrate (best-effort only)
                    try {
                        const lsKey = 'skillsApp_tempUsers';
                        const existing = JSON.parse(localStorage.getItem(lsKey) || '[]');
                        existing.push(user);
                        localStorage.setItem(lsKey, JSON.stringify(existing));
                    } catch (_) { /* ignore localStorage issues */ }
                }
            } else {
                this.showToast('Welcome back!', 'success');
            }
            return user;
        } catch (error) {
            console.error('Error loading/creating user (non-fatal for new session):', error);
            // As a last resort, allow a transient in-memory user so UI continues
            const fallbackUser = { email, skillsFile: null, createdAt: new Date().toISOString(), transient: true };
            this.showToast('Running in temporary mode (data not persisted).', 'warning');
            return fallbackUser;
        }
    }

    /**
     * Load users list (gracefully handle 404 or invalid JSON)
     */
    async loadUsersList() {
        try {
            const response = await this.fetchWithRetry(this.config.usersFile);
            if (response.ok) {
                try {
                    const users = await response.json();
                    if (Array.isArray(users)) return users;
                    return [];
                } catch (parseErr) {
                    console.warn('Could not parse users-master.json, starting fresh.', parseErr);
                    return [];
                }
            } else if (response.status === 404) {
                // File not yet created – treat as empty list
                return [];
            } else {
                console.warn('Unexpected status loading users file:', response.status);
                return [];
            }
        } catch (err) {
            console.warn('Failed to fetch users file (network/permission). Using empty list.', err);
            // Try localStorage fallback
            try {
                const ls = JSON.parse(localStorage.getItem('skillsApp_tempUsers') || '[]');
                if (Array.isArray(ls)) return ls;
            } catch (_) { /* ignore */ }
            return [];
        }
    }

    /**
     * Load user's existing skills
     */
    async loadUserSkills(skillsFile) {
        try {
            const response = await this.fetchWithRetry(skillsFile);
            
            if (response.ok) {
                const userSkills = await response.json();
                this.loadSelectedSkillsFromData(userSkills);
                this.showToast('Your existing skills have been loaded', 'success');
            }
        } catch (error) {
            console.error('Error loading user skills:', error);
            this.showToast('Could not load existing skills', 'warning');
        }
    }

    /**
     * Load selected skills from saved data
     */
    loadSelectedSkillsFromData(userSkills) {
        this.state.selectedSkills.clear();
        if (Array.isArray(userSkills)) {
            userSkills.forEach(l1 => {
                if (!Array.isArray(l1.skills)) return;
                l1.skills.forEach(l2 => {
                    if (!Array.isArray(l2.skills)) return;
                    l2.skills.forEach(l3 => {
                        if (l3.level === 3) {
                            const key = this.buildSelectionKey(l1.id, l2.id, l3.id);
                            this.state.selectedSkills.set(key, {
                                key,
                                l1: { id: l1.id, title: l1.title, description: l1.description },
                                l2: { id: l2.id, title: l2.title, description: l2.description },
                                l3: { id: l3.id, title: l3.title, description: l3.description }
                            });
                        }
                    });
                });
            });
        }
        this.updateSelectedSkillsDisplay();
    }

    /**
     * Show skills section and hide email section
     */
    showSkillsSection() {
        this.elements.emailSection.style.display = 'none';
        this.elements.skillsSection.style.display = 'block';
        this.elements.userEmail.textContent = this.state.currentUser.email;
    }

    /**
     * Render Level 1 skills
     */
    renderLevel1Skills() {
        if (!Array.isArray(this.state.masterSkills) || this.state.masterSkills.length === 0) {
            this.elements.level1Skills.innerHTML = '<p class="empty-message">No skills available. Please contact your administrator.</p>';
            return;
        }
        const html = this.state.masterSkills
            .map(skill => {
                const count = this.countSelectedUnder(skill.id, null, null);
                return this.createSkillCard(skill.id, { ...skill, selectedCount: count }, 'expandable', this.state.currentL1 === skill.id);
            })
            .join('');
        this.elements.level1Skills.innerHTML = html;
        this.elements.level1Skills.onclick = (e) => {
            const card = e.target.closest('.skill-card');
            if (card) this.selectL1Skill(card.dataset.skillId);
        };
    }

    /**
     * Select L1 skill and show L2 skills
     */
    selectL1Skill(l1Id) {
        this.state.currentL1 = l1Id;
        this.state.currentL2 = null;
        const l1Skill = this.state.masterSkills.find(s => s.id === l1Id);
        if (!l1Skill || !Array.isArray(l1Skill.skills) || l1Skill.skills.length === 0) {
            this.showToast('No sub-categories available for this skill area', 'warning');
            return;
        }
        this.renderLevel2Skills(l1Skill.skills);
        this.elements.level2Container.style.display = 'block';
        this.elements.level3Container.style.display = 'none';
        this.elements.level2Container.scrollIntoView({ behavior: 'smooth' });
        this.renderLevel1Skills(); // refresh selection state
    }

    /**
     * Render Level 2 skills
     */
    renderLevel2Skills(l2Skills) {
        const html = l2Skills
            .map(skill => {
                const count = this.countSelectedUnder(this.state.currentL1, skill.id, null);
                return this.createSkillCard(skill.id, { ...skill, selectedCount: count }, 'expandable', this.state.currentL2 === skill.id);
            })
            .join('');
        this.elements.level2Skills.innerHTML = html;
        this.elements.level2Skills.onclick = (e) => {
            const card = e.target.closest('.skill-card');
            if (card) this.selectL2Skill(card.dataset.skillId);
        };
    }

    /**
     * Select L2 skill and show L3 skills
     */
    selectL2Skill(l2Id) {
        this.state.currentL2 = l2Id;
        const l1Skill = this.state.masterSkills.find(s => s.id === this.state.currentL1);
        const l2Skill = l1Skill ? l1Skill.skills.find(s => s.id === l2Id) : null;
        if (!l2Skill || !Array.isArray(l2Skill.skills) || l2Skill.skills.length === 0) {
            this.showToast('No specific skills available for this category', 'warning');
            return;
        }
        this.renderLevel3Skills(l2Skill.skills);
        this.elements.level3Container.style.display = 'block';
        this.elements.level3Container.scrollIntoView({ behavior: 'smooth' });
        // Refresh level2 selection state
        if (l1Skill) this.renderLevel2Skills(l1Skill.skills);
    }

    /**
     * Render Level 3 skills (selectable)
     */
    renderLevel3Skills(l3Skills) {
        const html = l3Skills
            .map(skill => {
                const key = this.buildSelectionKey(this.state.currentL1, this.state.currentL2, skill.id);
                return this.createSkillCard(key, { title: skill.title, description: skill.description }, 'selectable', this.state.selectedSkills.has(key));
            }).join('');
        this.elements.level3Skills.innerHTML = html;
        this.elements.level3Skills.onclick = (e) => {
            const card = e.target.closest('.skill-card');
            if (card) this.toggleL3Skill(card.dataset.skillId);
        };
    }

    /**
     * Toggle L3 skill selection
     */
    toggleL3Skill(selectionKey) {
        const { l1Id, l2Id, l3Id } = this.parseSelectionKey(selectionKey);
        const l1Skill = this.state.masterSkills.find(s => s.id === l1Id);
        const l2Skill = l1Skill ? l1Skill.skills.find(s => s.id === l2Id) : null;
        const l3Skill = l2Skill ? l2Skill.skills.find(s => s.id === l3Id) : null;
        if (!l1Skill || !l2Skill || !l3Skill) return;
        if (this.state.selectedSkills.has(selectionKey)) {
            this.state.selectedSkills.delete(selectionKey);
            this.showToast('Skill removed', 'success');
        } else {
            this.state.selectedSkills.set(selectionKey, {
                key: selectionKey,
                l1: { id: l1Id, title: l1Skill.title, description: l1Skill.description },
                l2: { id: l2Id, title: l2Skill.title, description: l2Skill.description },
                l3: { id: l3Id, title: l3Skill.title, description: l3Skill.description }
            });
            this.showToast('Skill added', 'success');
        }
        this.updateSelectedSkillsDisplay();
        if (l2Skill) this.renderLevel3Skills(l2Skill.skills);
    }

    /**
     * Create skill card HTML
     */
    createSkillCard(id, skill, type, isSelected = false) {
        const selectedClass = isSelected ? 'selected' : '';
        const typeClass = type === 'selectable' ? 'selectable' : 'expandable';
        const subCount = (type !== 'selectable' && skill.selectedCount) ? `<div class="sub-count">${skill.selectedCount} selected</div>` : '';
        const selectedIndicator = type === 'selectable' ? '<span class="selected-indicator">Selected</span>' : '';
        return `
            <div class="skill-card ${typeClass} ${selectedClass}" data-skill-id="${id}">
                ${selectedIndicator}
                <div class="skill-card-title">${skill.title}</div>
                <div class="skill-card-description">${skill.description}</div>
                ${subCount}
            </div>`;
    }

    /**
     * Update selected skills display
     */
    updateSelectedSkillsDisplay() {
        const container = this.elements.selectedSkillsDisplay;
        
        if (this.state.selectedSkills.size === 0) {
            container.innerHTML = '<p class="empty-message">Please select your skills</p>';
            this.elements.saveSkillsBtn.style.display = 'none';
            const viewBtn = document.getElementById('viewSelectedBtn');
            if (viewBtn) viewBtn.style.display = 'none';
            return;
        }

        // Group by L1 -> L2 -> list of L3
        const grouped = {};
        for (const { l1, l2, l3, key } of this.state.selectedSkills.values()) {
            if (!grouped[l1.id]) grouped[l1.id] = { meta: l1, children: {} };
            if (!grouped[l1.id].children[l2.id]) grouped[l1.id].children[l2.id] = { meta: l2, items: [] };
            grouped[l1.id].children[l2.id].items.push({ l3, key });
        }
        const htmlParts = [];
        Object.values(grouped).forEach(l1Group => {
            htmlParts.push(`<div class="selected-group"><div class="selected-group-title">${l1Group.meta.title}</div>`);
            Object.values(l1Group.children).forEach(l2Group => {
                htmlParts.push(`<div class="selected-subgroup-title">${l2Group.meta.title}</div>`);
                l2Group.items.forEach(({ l3, key }) => {
                    htmlParts.push(this.createSelectedSkillItem(key, { l1: l1Group.meta, l2: l2Group.meta, l3 }));
                });
            });
            htmlParts.push('</div>');
        });
        container.innerHTML = htmlParts.join('');
        this.elements.saveSkillsBtn.style.display = 'block';
        const viewBtn = document.getElementById('viewSelectedBtn');
        if (viewBtn) viewBtn.style.display = 'inline-block';

        // Ensure download button visibility if any selections
    // Download button removed

        // Remove old listener by resetting onclick
        container.onclick = (e) => {
            if (e.target.classList.contains('remove-skill-btn')) {
                const skillKey = e.target.dataset.skillId;
                this.state.selectedSkills.delete(skillKey);
                this.updateSelectedSkillsDisplay();
                if (this.state.currentL2) {
                    const l1Skill = this.state.masterSkills.find(s => s.id === this.state.currentL1);
                    const l2Skill = l1Skill ? l1Skill.skills.find(s => s.id === this.state.currentL2) : null;
                    if (l2Skill) this.renderLevel3Skills(l2Skill.skills);
                }
                this.showToast('Skill removed', 'success');
            }
        };
    }

    /** Count selected L3 under given hierarchy */
    countSelectedUnder(l1Id, l2Id, l3Id) {
        let count = 0;
        for (const val of this.state.selectedSkills.values()) {
            if (l1Id && val.l1.id !== l1Id) continue;
            if (l2Id && val.l2.id !== l2Id) continue;
            if (l3Id && val.l3.id !== l3Id) continue;
            count++;
        }
        return count;
    }

    /**
     * Create selected skill item HTML
     */
    createSelectedSkillItem(id, skillData) {
        return `
            <div class="selected-skill-item">
                <div class="skill-leaf-title">${skillData.l3.title}</div>
                <button class="remove-skill-btn" data-skill-id="${id}" aria-label="Remove skill ${skillData.l3.title}">×</button>
            </div>`;
    }

    /**
     * Save user skills to S3
     */
    async saveUserSkills() {
        if (this.state.selectedSkills.size === 0) {
            this.showToast('Please select at least one skill before saving', 'warning');
            return;
        }

        try {
            this.setLoading(true);
            
            // Create hierarchical structure for selected skills
            const userSkillsData = this.createUserSkillsStructure();
            
            // Generate filename with timestamp (format: <email>-<timestamp>.json inside users/ folder)
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const emailPart = this.state.currentUser.email; // keep real email per requirement
            const filenameOnly = `${emailPart}-${timestamp}.json`;
            const objectKey = `users/${filenameOnly}`;
            
            // Save skills file
            await this.saveFile(objectKey, userSkillsData);
            
            // Update user record with skills file reference
            await this.updateUserSkillsFile(objectKey);
            
            this.showToast('Skills saved successfully!', 'success');
            // Download button removed
            
        } catch (error) {
            console.error('Error saving skills:', error);
            this.showToast('Failed to save skills. Please try again.', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Download current selected skills JSON
     */
    // downloadUserSkills removed (feature deprecated)

    /**
     * Create hierarchical structure for user skills
     */
    createUserSkillsStructure() {
        const byL1 = new Map();
        for (const [, skillData] of this.state.selectedSkills) {
            if (!byL1.has(skillData.l1.id)) {
                byL1.set(skillData.l1.id, {
                    id: skillData.l1.id,
                    level: 1,
                    title: skillData.l1.title,
                    description: skillData.l1.description,
                    skills: []
                });
            }
            const l1Obj = byL1.get(skillData.l1.id);
            let l2Obj = l1Obj.skills.find(s => s.id === skillData.l2.id);
            if (!l2Obj) {
                l2Obj = {
                    id: skillData.l2.id,
                    level: 2,
                    title: skillData.l2.title,
                    description: skillData.l2.description,
                    skills: []
                };
                l1Obj.skills.push(l2Obj);
            }
            if (!l2Obj.skills.find(s => s.id === skillData.l3.id)) {
                l2Obj.skills.push({
                    id: skillData.l3.id,
                    level: 3,
                    title: skillData.l3.title,
                    description: skillData.l3.description,
                    skills: []
                });
            }
        }
        return Array.from(byL1.values());
    }

    /**
     * Update user record with skills file reference
     */
    async updateUserSkillsFile(filename) {
        try {
            // Load current users list
            const response = await this.fetchWithRetry(this.config.usersFile);
            let users = [];
            if (response && response.ok) {
                try { users = await response.json(); } catch (_) { users = []; }
            }

            // Ensure current user exists in list
            let user = users.find(u => u.email === this.state.currentUser.email);
            if (!user) {
                user = { email: this.state.currentUser.email, createdAt: new Date().toISOString(), skillsFile: null };
                users.push(user);
            }

            user.skillsFile = filename;
            user.lastUpdated = new Date().toISOString();

            await this.saveFile(this.config.usersFile, users);
            this.state.currentUser.skillsFile = filename;
        } catch (error) {
            console.error('Error updating user skills file reference:', error);
            throw error;
        }
    }

    /**
     * Save file to S3 using PUT request
     */
    async saveFile(filename, data) {
        // For WRITE operations we must use the REST endpoint (website endpoints do NOT support PUT)
        // Special-case us-east-1 endpoint style
    // Prefer explicit placeholders substituted by deploy script; if unchanged use inferred values
    let { bucketName, region, inferredBucket, inferredRegion } = this.config;
    if (!bucketName || bucketName === 'skills-selector') bucketName = inferredBucket;
    if (!region || region === 'ap-southeast-2') region = inferredRegion;
        const restBase = region === 'us-east-1'
            ? `https://${bucketName}.s3.amazonaws.com/`
            : `https://${bucketName}.s3.${region}.amazonaws.com/`;
        const url = restBase + filename;

        const response = await fetch(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data, null, 2)
        });
        
        if (!response.ok) {
            // Provide clearer diagnostics for common static hosting issues
            console.error('Save failure details', {
                status: response.status,
                statusText: response.statusText,
                attemptedUrl: url,
                websiteBaseForReads: this.config.s3BaseUrl
            });
            throw new Error(`Failed to save file ${filename}: ${response.status} ${response.statusText}`);
        }
        
        return response;
    }

    /**
     * Fetch with retry logic
     */
    async fetchWithRetry(url, options = {}, retries = this.config.maxRetries) {
        const fullUrl = url.startsWith('http') ? url : this.config.s3BaseUrl + url;
        
        for (let i = 0; i < retries; i++) {
            try {
                const response = await fetch(fullUrl, options);
                return response;
            } catch (error) {
                if (i === retries - 1) throw error;
                await this.delay(this.config.retryDelay * Math.pow(2, i));
            }
        }
    }

    /**
     * Utility functions
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    truncateText(text, maxLength) {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    setLoading(isLoading) {
        this.state.isLoading = isLoading;
        this.elements.loadingIndicator.style.display = isLoading ? 'flex' : 'none';
    }

    showEmailError(message) {
        this.elements.emailError.textContent = message;
        this.elements.emailError.classList.add('show');
    }

    clearEmailError() {
        this.elements.emailError.classList.remove('show');
        this.elements.emailError.textContent = '';
    }

    showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        this.elements.toastContainer.appendChild(toast);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    buildSelectionKey(l1Id, l2Id, l3Id) {
        return `${l1Id}::${l2Id}::${l3Id}`;
    }

    parseSelectionKey(key) {
        const [l1Id, l2Id, l3Id] = key.split('::');
        return { l1Id, l2Id, l3Id };
    }
}

// Initialize the application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.skillsApp = new SkillsApp();
});