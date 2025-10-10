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
            bucketName: 'skills-selector-1760061975', // placeholder replaced by deploy.sh
            region: 'ap-southeast-2',       // placeholder replaced by deploy.sh
            inferredBucket,
            inferredRegion,
            s3BaseUrl: window.location.origin + window.location.pathname.replace(/\/[^/]*$/, '/'),
            masterSkillsFile: 'skills-master.json',
            skillLevelsMappingFile: 'skill-levels-mapping.json',
            skillRatingsMappingFile: 'skill-ratings-mapping.json',
            usersFile: 'users-master.json',
            maxRetries: 3,
            retryDelay: 1000
        };

        // Application state
        this.state = {
            currentUser: null,
            masterSkills: null,
            skillLevelsMapping: null,
            skillRatingsMapping: null,
            skillLookup: null,
            selectedSkills: new Map(),
            missingSkills: [],
            hasUnsavedChanges: false,
            currentL1: null,
            currentL2: null,
            currentL3: null,
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
            await this.loadSkillLevelsMapping();
            await this.loadSkillRatingsMapping();
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
            level1Title: document.getElementById('level1Title'),
            level2Title: document.getElementById('level2Title'),
            level3Title: document.getElementById('level3Title'),
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
     * Load skill levels mapping
     */
    async loadSkillLevelsMapping() {
        try {
            this.setLoading(true);
            const response = await this.fetchWithRetry(this.config.skillLevelsMappingFile);
            
            if (!response.ok) {
                throw new Error(`Failed to load skill levels mapping: ${response.status}`);
            }
            
            const data = await response.json();
            this.state.skillLevelsMapping = data.skillNames;
            
            // Update UI titles with skill level names
            this.updateSkillLevelTitles();
            
            console.log('Skill levels mapping loaded successfully');
        } catch (error) {
            console.error('Error loading skill levels mapping:', error);
            this.showError('Failed to load skill level names. Using default names.');
            // Fallback to default mapping
            this.state.skillLevelsMapping = [
                { level: 1, name: "Level 1 Capabilities" },
                { level: 2, name: "Level 2 Capabilities" },
                { level: 3, name: "Generic Skills" },
                { level: 4, name: "Technologies" }
            ];
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Load skill ratings mapping
     */
    async loadSkillRatingsMapping() {
        try {
            this.setLoading(true);
            const response = await this.fetchWithRetry(this.config.skillRatingsMappingFile);
            
            if (!response.ok) {
                throw new Error(`Failed to load skill ratings mapping: ${response.status}`);
            }
            
            const data = await response.json();
            this.state.skillRatingsMapping = data.ratings;
            
            console.log('Skill ratings mapping loaded successfully');
        } catch (error) {
            console.error('Error loading skill ratings mapping:', error);
            this.showError('Failed to load skill ratings. Using default ratings.');
            // Fallback to default mapping
            this.state.skillRatingsMapping = [
                { value: 1, name: "Beginner", description: "Learning the fundamentals", color: "#E3F2FD" },
                { value: 2, name: "Intermediate", description: "Comfortable with core concepts", color: "#64B5F6" },
                { value: 3, name: "Advanced", description: "Deep expertise and mastery", color: "#1976D2" }
            ];
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Get skill name for a given level
     */
    getSkillLevelName(level) {
        if (!this.state.skillLevelsMapping) {
            return `Level ${level}`;
        }
        const mapping = this.state.skillLevelsMapping.find(m => m.level === level);
        return mapping ? mapping.name : `Level ${level}`;
    }

    /**
     * Get rating info by value
     */
    getRatingInfo(value) {
        if (!this.state.skillRatingsMapping) {
            return { value: 1, name: "Beginner", description: "", color: "#E3F2FD" };
        }
        const rating = this.state.skillRatingsMapping.find(r => r.value === value);
        return rating || this.state.skillRatingsMapping[0];
    }

    /**
     * Get all available ratings
     */
    getAllRatings() {
        return this.state.skillRatingsMapping || [
            { value: 1, name: "Beginner", description: "Learning the fundamentals", color: "#E3F2FD" },
            { value: 2, name: "Intermediate", description: "Comfortable with core concepts", color: "#64B5F6" },
            { value: 3, name: "Advanced", description: "Deep expertise and mastery", color: "#1976D2" }
        ];
    }

    /**
     * Update UI titles with skill level names
     */
    updateSkillLevelTitles() {
        if (this.elements.level1Title) {
            this.elements.level1Title.textContent = this.getSkillLevelName(1);
        }
        if (this.elements.level2Title) {
            this.elements.level2Title.textContent = this.getSkillLevelName(2);
        }
        if (this.elements.level3Title) {
            this.elements.level3Title.textContent = this.getSkillLevelName(3);
        }
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
            
            // Build skill lookup index for fast O(1) access
            this.buildSkillLookupIndex();
            
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
     * Build skill lookup index for fast ID resolution
     */
    buildSkillLookupIndex() {
        this.state.skillLookup = new Map();
        
        if (!Array.isArray(this.state.masterSkills)) return;
        
        // Index all skills by ID across all levels
        this.state.masterSkills.forEach(l1 => {
            this.state.skillLookup.set(l1.id, {
                skill: l1,
                level: 1,
                path: { l1 }
            });
            
            if (Array.isArray(l1.skills)) {
                l1.skills.forEach(l2 => {
                    this.state.skillLookup.set(l2.id, {
                        skill: l2,
                        level: 2,
                        path: { l1, l2 }
                    });
                    
                    if (Array.isArray(l2.skills)) {
                        l2.skills.forEach(l3 => {
                            this.state.skillLookup.set(l3.id, {
                                skill: l3,
                                level: 3,
                                path: { l1, l2, l3 }
                            });
                            
                            if (Array.isArray(l3.skills)) {
                                l3.skills.forEach(l4 => {
                                    this.state.skillLookup.set(l4.id, {
                                        skill: l4,
                                        level: 4,
                                        path: { l1, l2, l3, l4 }
                                    });
                                });
                            }
                        });
                    }
                });
            }
        });
        
        console.log(`Skill lookup index built: ${this.state.skillLookup.size} skills indexed`);
    }

    /**
     * Resolve skill by ID from lookup index
     */
    resolveSkillById(skillId) {
        return this.state.skillLookup.get(skillId);
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
            
            console.log('[LOAD] Starting email submission for:', email);
            const user = await this.loadOrCreateUser(email);
            this.state.currentUser = user;
            console.log('[LOAD] User loaded:', { email: user.email, hasSkillsFile: !!user.skillsFile, skillsFile: user.skillsFile });
            
            // Load existing skills if user has them
            if (user.skillsFile) {
                console.log('[LOAD] User has existing skills file, attempting to load:', user.skillsFile);
                await this.loadUserSkills(user.skillsFile);
            } else {
                console.log('[LOAD] No existing skills file for this user');
            }
            
            this.showSkillsSection();
            this.renderLevel1Skills();
            
        } catch (error) {
            console.error('[LOAD ERROR] Error handling email submission:', error);
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
            console.log('[USER] Loading users list...');
            const users = await this.loadUsersList();
            console.log('[USER] Users list loaded, total users:', users.length);

            // Attempt to find existing user
            let user = users.find(u => u.email === email);

            if (!user) {
                console.log('[USER] New user - creating profile for:', email);
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
                    console.warn('[USER] Could not persist new user list (continuing in memory only):', saveErr);
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
                console.log('[USER] Existing user found:', { email: user.email, skillsFile: user.skillsFile, createdAt: user.createdAt });
                this.showToast('Welcome back!', 'success');
            }
            return user;
        } catch (error) {
            console.error('[USER ERROR] Error loading/creating user (non-fatal for new session):', error);
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
            console.log('[SKILLS] Attempting to load skills from:', skillsFile);
            const response = await this.fetchWithRetry(skillsFile);
            
            if (response.ok) {
                const data = await response.json();
                console.log('[SKILLS] Skills file loaded successfully:', { 
                    hasSelectedSkills: !!data.selectedSkills, 
                    isArray: Array.isArray(data.selectedSkills || data),
                    skillCount: (data.selectedSkills || data).length,
                    lastUpdated: data.lastUpdated 
                });
                
                // Handle both old format (array) and new format (object with selectedSkills)
                const userSkills = data.selectedSkills || data;
                this.loadSelectedSkillsFromData(userSkills);
                
                // Reset unsaved changes flag after loading
                this.state.hasUnsavedChanges = false;
                this.updateSaveButtonState();
                
                console.log('[SKILLS] Skills loaded into state, selectedSkills.size:', this.state.selectedSkills.size);
                
                // Show missing skills banner if any skills couldn't be resolved
                this.showMissingSkillsBanner();
                
                // Display last updated time if available
                if (data.lastUpdated) {
                    const lastUpdated = new Date(data.lastUpdated).toLocaleString();
                    this.showToast(`Skills loaded (last updated: ${lastUpdated})`, 'success');
                } else {
                    this.showToast('Your existing skills have been loaded', 'success');
                }
            } else {
                console.warn('[SKILLS] Failed to load skills file, status:', response.status, response.statusText);
            }
        } catch (error) {
            console.error('[SKILLS ERROR] Error loading user skills:', error);
            this.showToast('Could not load existing skills', 'warning');
        }
    }

    /**
     * Load selected skills from saved data
     */
    loadSelectedSkillsFromData(userSkills) {
        console.log('[PARSE] Starting to parse skills data:', { 
            isArray: Array.isArray(userSkills), 
            length: userSkills?.length,
            firstItem: userSkills?.[0] 
        });
        
        this.state.selectedSkills.clear();
        this.state.missingSkills = [];
        
        if (!Array.isArray(userSkills) || userSkills.length === 0) {
            console.log('[PARSE] No skills to load (empty or invalid array)');
            this.updateSelectedSkillsDisplay();
            return;
        }
        
        // Check if this is the new flat format or old hierarchical format
        const isNewFormat = userSkills[0].hasOwnProperty('l1Id');
        console.log('[PARSE] Format detected:', isNewFormat ? 'NEW (flat with IDs)' : 'OLD (hierarchical)');
        
        if (isNewFormat) {
            console.log('[PARSE] Processing new format skills...');
            // New flat format with only IDs
            userSkills.forEach((selection, index) => {
                const { l1Id, l2Id, l3Id, l4Ids } = selection;
                console.log(`[PARSE] Processing skill ${index + 1}/${userSkills.length}:`, { l1Id, l2Id, l3Id, l4Count: l4Ids?.length, rating: selection.rating });
                
                // Resolve skills from master using lookup index
                const l1Data = this.resolveSkillById(l1Id);
                const l2Data = this.resolveSkillById(l2Id);
                const l3Data = this.resolveSkillById(l3Id);
                
                // Check for missing skills
                if (!l1Data) {
                    this.state.missingSkills.push({ id: l1Id, level: 1 });
                    console.warn('[PARSE] L1 skill not found:', l1Id);
                    return;
                }
                if (!l2Data) {
                    this.state.missingSkills.push({ id: l2Id, level: 2 });
                    console.warn('[PARSE] L2 skill not found:', l2Id);
                    return;
                }
                if (!l3Data) {
                    this.state.missingSkills.push({ id: l3Id, level: 3 });
                    console.warn('[PARSE] L3 skill not found:', l3Id);
                    return;
                }
                
                console.log(`[PARSE] Resolved skill: ${l1Data.skill.title} > ${l2Data.skill.title} > ${l3Data.skill.title}`);
                
                // Resolve L4 skills
                const l4Skills = [];
                if (Array.isArray(l4Ids)) {
                    l4Ids.forEach(l4Id => {
                        const l4Data = this.resolveSkillById(l4Id);
                        if (l4Data) {
                            l4Skills.push({
                                id: l4Id,
                                title: l4Data.skill.title,
                                description: l4Data.skill.description
                            });
                        } else {
                            this.state.missingSkills.push({ id: l4Id, level: 4 });
                            console.warn('[PARSE] L4 skill not found:', l4Id);
                        }
                    });
                }
                
                // Build selection key and store
                const key = this.buildSelectionKey(l1Id, l2Id, l3Id);
                console.log(`[PARSE] Storing skill with key: ${key}, rating: ${selection.rating || 1}`);
                
                this.state.selectedSkills.set(key, {
                    key,
                    l1: { 
                        id: l1Id, 
                        title: l1Data.skill.title, 
                        description: l1Data.skill.description 
                    },
                    l2: { 
                        id: l2Id, 
                        title: l2Data.skill.title, 
                        description: l2Data.skill.description 
                    },
                    l3: { 
                        id: l3Id, 
                        title: l3Data.skill.title, 
                        description: l3Data.skill.description 
                    },
                    l4Skills: l4Skills,
                    rating: selection.rating || 1,  // Load rating or default to Beginner
                    _ratingAcknowledged: true  // Don't pulse for loaded skills
                });
            });
            console.log('[PARSE] Finished processing new format. Total skills loaded:', this.state.selectedSkills.size);
        } else {
            // Old hierarchical format with titles/descriptions - convert and warn
            console.warn('[PARSE] Loading old skill format - this will be converted to new format on next save');
            userSkills.forEach(l1 => {
                if (!Array.isArray(l1.skills)) return;
                l1.skills.forEach(l2 => {
                    if (!Array.isArray(l2.skills)) return;
                    l2.skills.forEach(l3 => {
                        if (l3.level === 3) {
                            const key = this.buildSelectionKey(l1.id, l2.id, l3.id);
                            
                            // Extract L4 skills if they exist
                            const l4Skills = Array.isArray(l3.skills) 
                                ? l3.skills.filter(l4 => l4.level === 4).map(l4 => ({
                                    id: l4.id,
                                    title: l4.title,
                                    description: l4.description || ''
                                  }))
                                : [];
                            
                            this.state.selectedSkills.set(key, {
                                key,
                                l1: { id: l1.id, title: l1.title, description: l1.description },
                                l2: { id: l2.id, title: l2.title, description: l2.description },
                                l3: { id: l3.id, title: l3.title, description: l3.description },
                                l4Skills: l4Skills,
                                rating: 1,  // Default rating for old format
                                _ratingAcknowledged: true  // Don't pulse for loaded skills
                            });
                        }
                    });
                });
            });
        }
        
        // Show missing skills banner if any
        if (this.state.missingSkills.length > 0) {
            console.log('[PARSE] Missing skills detected:', this.state.missingSkills.length);
            this.showMissingSkillsBanner();
        }
        
        console.log('[PARSE] Calling updateSelectedSkillsDisplay()...');
        this.updateSelectedSkillsDisplay();
        console.log('[PARSE] Complete! Final selectedSkills.size:', this.state.selectedSkills.size);
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
     * Render Level 3 skills (with Level 4 technology selectors)
     */
    renderLevel3Skills(l3Skills) {
        const html = l3Skills
            .map(skill => {
                const key = this.buildSelectionKey(this.state.currentL1, this.state.currentL2, skill.id);
                const isSelected = this.state.selectedSkills.has(key);
                const hasL4Skills = Array.isArray(skill.skills) && skill.skills.length > 0;
                
                return this.createL3SkillCard(key, skill, isSelected, hasL4Skills);
            }).join('');
        this.elements.level3Skills.innerHTML = html;
        
        // Attach event listeners for L3 cards and L4 dropdowns
        this.attachLevel3EventListeners();
    }

    /**
     * Create Level 3 skill card with Level 4 technology button
     */
    createL3SkillCard(key, skill, isSelected, hasL4Skills) {
        const selectedClass = isSelected ? 'selected' : '';
        const selectedIndicator = isSelected ? '<span class="selected-indicator">Selected</span>' : '';
        
        // Get current rating for this skill (if selected)
        const skillData = this.state.selectedSkills.get(key);
        const currentRating = skillData?.rating || (isSelected ? 1 : null);
        
        // Build rating dropdown HTML
        let ratingDropdown = '';
        if (isSelected) {
            // Selected skill: show dropdown with current rating
            const ratingInfo = this.getRatingInfo(currentRating);
            const allRatings = this.getAllRatings();
            const ratingOptions = allRatings.map(r => 
                `<option value="${r.value}" ${r.value === currentRating ? 'selected' : ''}>${r.name}</option>`
            ).join('');
            
            // Add pulse class if newly selected with default rating and not acknowledged
            const pulseClass = (currentRating === 1 && !skillData?._ratingAcknowledged) ? 'rating-pulse' : '';
            
            // Text color for dropdown (white for Advanced)
            const textColor = currentRating === 3 ? '#fff' : '#333';
            
            ratingDropdown = `
                <div class="l3-rating-section">
                    <label class="rating-label">Rating:</label>
                    <select class="l3-rating-dropdown ${pulseClass}" data-skill-key="${key}" style="background-color: ${ratingInfo.color}; color: ${textColor}">
                        ${ratingOptions}
                    </select>
                </div>
            `;
        } else {
            // Unselected skill: show placeholder dropdown (disabled)
            ratingDropdown = `
                <div class="l3-rating-section">
                    <label class="rating-label">Rating:</label>
                    <select class="l3-rating-dropdown" data-skill-key="${key}" disabled style="background-color: #f5f5f5; color: #999;">
                        <option value="">Select from dropdown...</option>
                    </select>
                </div>
            `;
        }
        
        // Show technologies if selected and has L4 skills
        let technologiesDisplay = '';
        if (isSelected && skillData?.l4Skills && skillData.l4Skills.length > 0) {
            const techTags = skillData.l4Skills.map(l4 => 
                `<span class="tech-tag">${l4.title}</span>`
            ).join('');
            technologiesDisplay = `
                <div class="skill-technologies-explorer">
                    ${techTags}
                </div>
            `;
        }
        
        let l4Button = '';
        if (hasL4Skills) {
            const l4Name = this.getSkillLevelName(4);
            const selectedL4 = this.state.selectedSkills.get(key)?.l4Skills || [];
            const selectedCount = selectedL4.length;
            
            l4Button = `
                <div class="l4-technologies-section">
                    <button class="l4-select-btn" data-l3-key="${key}" data-l3-title="${skill.title}" type="button">
                        <span class="l4-btn-icon">⚙</span>
                        ${selectedCount > 0 ? `${selectedCount} ${l4Name} Selected` : `Select ${l4Name}`}
                    </button>
                </div>
            `;
        }
        
        return `
            <div class="skill-card selectable ${selectedClass}" data-skill-id="${key}">
                ${selectedIndicator}
                <div class="skill-card-title">${skill.title}</div>
                <div class="skill-card-description">${skill.description}</div>
                ${technologiesDisplay}
                ${l4Button}
                ${ratingDropdown}
            </div>`;
    }

    /**
     * Attach event listeners for Level 3 cards and Level 4 buttons
     */
    attachLevel3EventListeners() {
        // Toggle L3 selection when clicking the card (but not the button/dropdown area)
        this.elements.level3Skills.onclick = (e) => {
            // Ignore clicks on technology button or rating dropdown
            if (e.target.closest('.l4-technologies-section') || e.target.closest('.l3-rating-section')) {
                return;
            }
            const card = e.target.closest('.skill-card');
            if (card) {
                this.toggleL3Skill(card.dataset.skillId);
            }
        };
        
        // Handle L4 technology selection button clicks
        const l4Buttons = this.elements.level3Skills.querySelectorAll('.l4-select-btn');
        l4Buttons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const l3Key = button.dataset.l3Key;
                const l3Title = button.dataset.l3Title;
                this.showL4TechnologyModal(l3Key, l3Title);
            });
        });
        
        // Handle rating dropdown changes
        const ratingDropdowns = this.elements.level3Skills.querySelectorAll('.l3-rating-dropdown');
        ratingDropdowns.forEach(dropdown => {
            dropdown.addEventListener('change', (e) => {
                e.stopPropagation();
                const skillKey = dropdown.dataset.skillKey;
                const newRating = parseInt(dropdown.value);
                const skillData = this.state.selectedSkills.get(skillKey);
                
                if (skillData) {
                    skillData.rating = newRating;
                    skillData._ratingAcknowledged = true; // Stop pulsing
                    this.state.hasUnsavedChanges = true;
                    
                    // Update dropdown color and text color
                    const ratingInfo = this.getRatingInfo(newRating);
                    dropdown.style.backgroundColor = ratingInfo.color;
                    dropdown.style.color = newRating === 3 ? '#fff' : '#333'; // White text for Advanced
                    
                    // Remove pulse animation from dropdown only
                    dropdown.classList.remove('rating-pulse');
                    
                    // Sync: Update selected skills display to reflect rating change
                    this.updateSelectedSkillsDisplay();
                    
                    // Visual indicator on save button
                    this.updateSaveButtonState();
                    
                    this.showToast(`Rating updated to ${ratingInfo.name}`, 'success');
                }
            });
        });
    }

    /**
     * Show Level 4 technology selection modal
     */
    showL4TechnologyModal(l3Key, l3Title) {
        const { l1Id, l2Id, l3Id } = this.parseSelectionKey(l3Key);
        const l1Skill = this.state.masterSkills.find(s => s.id === l1Id);
        const l2Skill = l1Skill ? l1Skill.skills.find(s => s.id === l2Id) : null;
        const l3Skill = l2Skill ? l2Skill.skills.find(s => s.id === l3Id) : null;
        
        if (!l3Skill || !Array.isArray(l3Skill.skills) || l3Skill.skills.length === 0) {
            return;
        }
        
        const l4Name = this.getSkillLevelName(4);
        const selectedL4 = this.state.selectedSkills.get(l3Key)?.l4Skills || [];
        const selectedL4Ids = selectedL4.map(s => s.id);
        
        // Create modal HTML
        const modalHtml = `
            <div class="l4-modal-overlay" id="l4ModalOverlay">
                <div class="l4-modal">
                    <div class="l4-modal-header">
                        <h3>${l4Name} for "${l3Title}"</h3>
                        <button class="l4-modal-close" id="l4ModalClose" aria-label="Close">&times;</button>
                    </div>
                    <div class="l4-modal-body">
                        <div class="l4-modal-grid">
                            ${l3Skill.skills.map(l4 => `
                                <div class="l4-tech-card ${selectedL4Ids.includes(l4.id) ? 'selected' : ''}" 
                                     data-l4-id="${l4.id}" 
                                     data-l4-title="${l4.title}"
                                     data-l4-description="${l4.description || ''}">
                                    <span class="l4-tech-selected-indicator">✓</span>
                                    <div class="l4-tech-title">${l4.title}</div>
                                    <div class="l4-tech-description">${l4.description || ''}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    <div class="l4-modal-footer">
                        <button class="btn btn-secondary" id="l4ModalCancel">Cancel</button>
                        <button class="btn btn-primary" id="l4ModalDone">Done</button>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Get modal elements
        const overlay = document.getElementById('l4ModalOverlay');
        const closeBtn = document.getElementById('l4ModalClose');
        const cancelBtn = document.getElementById('l4ModalCancel');
        const doneBtn = document.getElementById('l4ModalDone');
        const techCards = overlay.querySelectorAll('.l4-tech-card');
        
        // Handle technology card selection
        techCards.forEach(card => {
            card.addEventListener('click', () => {
                card.classList.toggle('selected');
            });
        });
        
        // Close modal handlers
        const closeModal = () => {
            overlay.remove();
        };
        
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);
        
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                closeModal();
            }
        });
        
        // Done button - save selections
        doneBtn.addEventListener('click', () => {
            const selectedCards = overlay.querySelectorAll('.l4-tech-card.selected');
            const selectedTechnologies = Array.from(selectedCards).map(card => ({
                id: card.dataset.l4Id,
                title: card.dataset.l4Title,
                description: card.dataset.l4Description
            }));
            
            this.handleL4Selection(l3Key, selectedTechnologies);
            closeModal();
        });
        
        // Prevent body scroll when modal is open
        document.body.style.overflow = 'hidden';
        
        // Restore body scroll when modal closes
        const originalRemove = overlay.remove.bind(overlay);
        overlay.remove = function() {
            document.body.style.overflow = '';
            originalRemove();
        };
    }

    /**
     * Handle Level 4 technology selection from modal
     */
    handleL4Selection(l3Key, selectedTechnologies) {
        const { l1Id, l2Id, l3Id } = this.parseSelectionKey(l3Key);
        const l1Skill = this.state.masterSkills.find(s => s.id === l1Id);
        const l2Skill = l1Skill ? l1Skill.skills.find(s => s.id === l2Id) : null;
        const l3Skill = l2Skill ? l2Skill.skills.find(s => s.id === l3Id) : null;
        
        if (!l1Skill || !l2Skill || !l3Skill) return;
        
        // If technologies are selected, auto-select the L3 skill
        if (selectedTechnologies.length > 0) {
            this.state.selectedSkills.set(l3Key, {
                key: l3Key,
                l1: { id: l1Id, title: l1Skill.title, description: l1Skill.description },
                l2: { id: l2Id, title: l2Skill.title, description: l2Skill.description },
                l3: { id: l3Id, title: l3Skill.title, description: l3Skill.description },
                l4Skills: selectedTechnologies,
                rating: 1  // Default to Beginner
            });
            this.showToast(`${selectedTechnologies.length} ${this.getSkillLevelName(4).toLowerCase()} selected`, 'success');
        } else {
            // If no technologies selected, deselect the L3 skill
            if (this.state.selectedSkills.has(l3Key)) {
                this.state.selectedSkills.delete(l3Key);
                this.showToast('Skill deselected', 'success');
            }
        }
        
        // Update UI
        this.updateSelectedSkillsDisplay();
        if (l2Skill) this.renderLevel3Skills(l2Skill.skills);
    }

    /**
     * Show missing skills banner if there are skills that couldn't be resolved
     */
    showMissingSkillsBanner() {
        const banner = document.getElementById('missingSkillsBanner');
        const countEl = document.getElementById('missingSkillsCount');
        const listEl = document.getElementById('missingSkillsList');
        const lastUpdatedEl = document.getElementById('lastUpdated');
        const dismissBtn = document.getElementById('dismissBannerBtn');
        
        if (!banner || this.state.missingSkills.length === 0) {
            if (banner) banner.style.display = 'none';
            return;
        }
        
        // Show banner
        banner.style.display = 'block';
        
        // Set count
        countEl.textContent = this.state.missingSkills.length;
        
        // Set timestamp
        const now = new Date();
        lastUpdatedEl.textContent = now.toLocaleString();
        
        // List missing skill IDs with level information
        listEl.innerHTML = this.state.missingSkills
            .map(item => `<div><strong>L${item.level}:</strong> ${item.id}</div>`)
            .join('');
        
        // Dismiss button handler
        if (dismissBtn && !dismissBtn.dataset.listenerAttached) {
            dismissBtn.dataset.listenerAttached = 'true';
            dismissBtn.addEventListener('click', () => {
                banner.style.display = 'none';
            });
        }
    }

    /**
     * Toggle L3 skill selection (direct card click without using technology modal)
     */
    toggleL3Skill(selectionKey) {
        const { l1Id, l2Id, l3Id } = this.parseSelectionKey(selectionKey);
        const l1Skill = this.state.masterSkills.find(s => s.id === l1Id);
        const l2Skill = l1Skill ? l1Skill.skills.find(s => s.id === l2Id) : null;
        const l3Skill = l2Skill ? l2Skill.skills.find(s => s.id === l3Id) : null;
        if (!l1Skill || !l2Skill || !l3Skill) return;
        
        // Check if this skill has L4 technologies
        const hasL4Skills = Array.isArray(l3Skill.skills) && l3Skill.skills.length > 0;
        
        if (this.state.selectedSkills.has(selectionKey)) {
            // Deselect the skill
            this.state.selectedSkills.delete(selectionKey);
            this.showToast('Skill removed', 'success');
        } else {
            // If skill has L4 technologies, open the modal instead
            if (hasL4Skills) {
                this.showL4TechnologyModal(selectionKey, l3Skill.title);
                return;
            }
            
            // Select skill without L4 technologies
            this.state.selectedSkills.set(selectionKey, {
                key: selectionKey,
                l1: { id: l1Id, title: l1Skill.title, description: l1Skill.description },
                l2: { id: l2Id, title: l2Skill.title, description: l2Skill.description },
                l3: { id: l3Id, title: l3Skill.title, description: l3Skill.description },
                l4Skills: [],
                rating: 1  // Default to Beginner
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
        console.log('[DISPLAY] updateSelectedSkillsDisplay called, selectedSkills.size:', this.state.selectedSkills.size);
        const container = this.elements.selectedSkillsDisplay;
        
        if (this.state.selectedSkills.size === 0) {
            console.log('[DISPLAY] No skills selected, showing empty message');
            container.innerHTML = '<p class="empty-message">Please select your skills</p>';
            this.elements.saveSkillsBtn.style.display = 'none';
            const viewBtn = document.getElementById('viewSelectedBtn');
            if (viewBtn) viewBtn.style.display = 'none';
            return;
        }

        console.log('[DISPLAY] Grouping skills for display...');

        // Group by L1 -> L2 -> list of L3 (with L4)
        const grouped = {};
        for (const { l1, l2, l3, l4Skills, key, rating, _ratingAcknowledged } of this.state.selectedSkills.values()) {
            if (!grouped[l1.id]) grouped[l1.id] = { meta: l1, children: {} };
            if (!grouped[l1.id].children[l2.id]) grouped[l1.id].children[l2.id] = { meta: l2, items: [] };
            grouped[l1.id].children[l2.id].items.push({ l3, l4Skills: l4Skills || [], key, rating, _ratingAcknowledged });
        }
        const htmlParts = [];
        Object.values(grouped).forEach(l1Group => {
            htmlParts.push(`<div class="selected-group"><div class="selected-group-title">${l1Group.meta.title}</div>`);
            Object.values(l1Group.children).forEach(l2Group => {
                htmlParts.push(`<div class="selected-subgroup-title">${l2Group.meta.title}</div>`);
                l2Group.items.forEach(({ l3, l4Skills, key, rating, _ratingAcknowledged }) => {
                    htmlParts.push(this.createSelectedSkillItem(key, { l1: l1Group.meta, l2: l2Group.meta, l3, l4Skills, rating, _ratingAcknowledged }));
                });
            });
            htmlParts.push('</div>');
        });
        container.innerHTML = htmlParts.join('');
        console.log('[DISPLAY] HTML generated, skill items:', htmlParts.length);
        
        this.elements.saveSkillsBtn.style.display = 'block';
        const viewBtn = document.getElementById('viewSelectedBtn');
        if (viewBtn) viewBtn.style.display = 'inline-block';

        console.log('[DISPLAY] Display updated successfully');
        
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
        
        // Handle rating changes
        container.onchange = (e) => {
            if (e.target.classList.contains('skill-rating-dropdown')) {
                const skillKey = e.target.dataset.skillId;
                const newRating = parseInt(e.target.value);
                const skillData = this.state.selectedSkills.get(skillKey);
                if (skillData) {
                    skillData.rating = newRating;
                    skillData._ratingAcknowledged = true;
                    this.state.hasUnsavedChanges = true;
                    
                    // Update dropdown color and text color
                    const ratingInfo = this.getRatingInfo(newRating);
                    e.target.style.backgroundColor = ratingInfo.color;
                    e.target.style.color = newRating === 3 ? '#fff' : '#333'; // White text for Advanced
                    
                    // Sync: Re-render explorer section if visible to update rating dropdown there
                    if (this.state.currentL2) {
                        const l1Skill = this.state.masterSkills.find(s => s.id === this.state.currentL1);
                        const l2Skill = l1Skill ? l1Skill.skills.find(s => s.id === this.state.currentL2) : null;
                        if (l2Skill) this.renderLevel3Skills(l2Skill.skills);
                    }
                    
                    // Visual indicator on save button
                    this.updateSaveButtonState();
                    this.showToast(`Rating updated to ${ratingInfo.name}`, 'success');
                }
            }
        };
    }

    /**
     * Update save button visual state based on unsaved changes
     */
    updateSaveButtonState() {
        if (this.state.hasUnsavedChanges) {
            this.elements.saveSkillsBtn.classList.add('has-changes');
            this.elements.saveSkillsBtn.textContent = 'Save Changes *';
        } else {
            this.elements.saveSkillsBtn.classList.remove('has-changes');
            this.elements.saveSkillsBtn.textContent = 'Save Skills';
        }
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
        const l4TechnologiesHtml = skillData.l4Skills && skillData.l4Skills.length > 0
            ? `<div class="skill-technologies">${skillData.l4Skills.map(l4 => `<span class="tech-tag">${l4.title}</span>`).join('')}</div>`
            : '';
        
        const currentRating = skillData.rating || 1;
        const ratingInfo = this.getRatingInfo(currentRating);
        const allRatings = this.getAllRatings();
        const ratingOptions = allRatings.map(r => 
            `<option value="${r.value}" ${r.value === currentRating ? 'selected' : ''}>${r.name}</option>`
        ).join('');
        
        // Text color for dropdown (white for Advanced)
        const textColor = currentRating === 3 ? '#fff' : '#333';
        
        return `
            <div class="selected-skill-item">
                <div class="skill-item-header">
                    <div class="skill-leaf-title">${skillData.l3.title}</div>
                    <div class="skill-rating-container">
                        <select class="skill-rating-dropdown" data-skill-id="${id}" style="background-color: ${ratingInfo.color}; color: ${textColor}">
                            ${ratingOptions}
                        </select>
                    </div>
                    <button class="remove-skill-btn" data-skill-id="${id}" aria-label="Remove skill ${skillData.l3.title}">×</button>
                </div>
                ${l4TechnologiesHtml}
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
            
            console.log('[SAVE-SKILLS] Starting save process for user:', this.state.currentUser.email);
            console.log('[SAVE-SKILLS] Selected skills count:', this.state.selectedSkills.size);
            
            // Create hierarchical structure for selected skills
            const userSkillsData = this.createUserSkillsStructure();
            console.log('[SAVE-SKILLS] Skills data structure created, items:', userSkillsData.length);
            
            // Generate filename with email only (format: <email>.json inside users/ folder)
            // Sanitize email for filename (replace special characters)
            const emailPart = this.state.currentUser.email.replace(/[^a-zA-Z0-9@.-]/g, '_');
            const filenameOnly = `${emailPart}.json`;
            const objectKey = `users/${filenameOnly}`;
            console.log('[SAVE-SKILLS] Target file path:', objectKey);
            
            // Add timestamp inside the JSON data
            const dataWithTimestamp = {
                userEmail: this.state.currentUser.email,
                selectedSkills: userSkillsData,
                lastUpdated: new Date().toISOString()
            };
            
            // Save skills file (will overwrite existing file)
            console.log('[SAVE-SKILLS] Step 1: Saving skills file...');
            await this.saveFile(objectKey, dataWithTimestamp);
            console.log('[SAVE-SKILLS] Skills file saved successfully');
            
            // Update user record with skills file reference
            console.log('[SAVE-SKILLS] Step 2: Updating users-master.json...');
            await this.updateUserSkillsFile(objectKey);
            console.log('[SAVE-SKILLS] users-master.json updated successfully');
            
            // Reset unsaved changes flag
            this.state.hasUnsavedChanges = false;
            this.updateSaveButtonState();
            
            console.log('[SAVE-SKILLS] Save process completed successfully!');
            this.showToast('Skills saved successfully!', 'success');
            // Download button removed
            
        } catch (error) {
            console.error('[SAVE-SKILLS ERROR] Error saving skills:', error);
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
     * Create flat structure for user skills (ID-only format)
     */
    createUserSkillsStructure() {
        const flatStructure = [];
        
        for (const [, skillData] of this.state.selectedSkills) {
            const selection = {
                l1Id: skillData.l1.id,
                l2Id: skillData.l2.id,
                l3Id: skillData.l3.id,
                l4Ids: (skillData.l4Skills || []).map(l4 => l4.id),
                rating: skillData.rating || 1  // Include rating in saved data
            };
            flatStructure.push(selection);
        }
        
        return flatStructure;
    }

    /**
     * Update user record with skills file reference
     */
    async updateUserSkillsFile(filename) {
        try {
            console.log('[UPDATE] Starting updateUserSkillsFile with filename:', filename);
            console.log('[UPDATE] Current user email:', this.state.currentUser.email);
            
            // Load current users list
            const response = await this.fetchWithRetry(this.config.usersFile);
            let users = [];
            if (response && response.ok) {
                try { 
                    users = await response.json(); 
                    console.log('[UPDATE] Loaded users-master.json, total users:', users.length);
                } catch (_) { 
                    console.warn('[UPDATE] Failed to parse users-master.json');
                    users = []; 
                }
            } else {
                console.warn('[UPDATE] Failed to fetch users-master.json, status:', response?.status);
            }

            // Ensure current user exists in list
            let user = users.find(u => u.email === this.state.currentUser.email);
            if (!user) {
                console.log('[UPDATE] User not found in list, creating new entry');
                user = { email: this.state.currentUser.email, createdAt: new Date().toISOString(), skillsFile: null };
                users.push(user);
            } else {
                console.log('[UPDATE] User found in list, current skillsFile:', user.skillsFile);
            }

            user.skillsFile = filename;
            user.lastUpdated = new Date().toISOString();
            console.log('[UPDATE] Updated user object:', { email: user.email, skillsFile: user.skillsFile, lastUpdated: user.lastUpdated });

            console.log('[UPDATE] Attempting to save users-master.json...');
            await this.saveFile(this.config.usersFile, users);
            console.log('[UPDATE] users-master.json saved successfully');
            
            this.state.currentUser.skillsFile = filename;
            console.log('[UPDATE] State updated, currentUser.skillsFile:', this.state.currentUser.skillsFile);
        } catch (error) {
            console.error('[UPDATE ERROR] Error updating user skills file reference:', error);
            throw error;
        }
    }

    /**
     * Save file to S3 using PUT request
     */
    async saveFile(filename, data) {
        console.log('[SAVE] Starting saveFile for:', filename);
        console.log('[SAVE] Data type:', Array.isArray(data) ? 'Array' : typeof data, 'Length/Keys:', Array.isArray(data) ? data.length : Object.keys(data).length);
        
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

        console.log('[SAVE] Target URL:', url);
        console.log('[SAVE] Bucket:', bucketName, 'Region:', region);
        
        const response = await fetch(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data, null, 2)
        });
        
        console.log('[SAVE] Response status:', response.status, response.statusText);
        
        if (!response.ok) {
            // Provide clearer diagnostics for common static hosting issues
            console.error('[SAVE ERROR] Save failure details', {
                status: response.status,
                statusText: response.statusText,
                attemptedUrl: url,
                websiteBaseForReads: this.config.s3BaseUrl
            });
            throw new Error(`Failed to save file ${filename}: ${response.status} ${response.statusText}`);
        }
        
        console.log('[SAVE] File saved successfully:', filename);
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