// Enhanced JavaScript for Inventory Management System with Search & Theme

// Global variables
let searchCache = [];
let themeChangeListeners = [];

// Utility functions
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Enhanced search functionality
class SearchManager {
    constructor() {
        this.suggestions = [
            { title: 'Upload CSV File', description: 'Upload your inventory data file', url: '/upload', icon: 'fas fa-file-csv', keywords: ['csv', 'upload', 'file', 'import', 'data'] },
            { title: 'Sample Data', description: 'Try with sample inventory data', url: '/sample-data', icon: 'fas fa-database', keywords: ['sample', 'demo', 'test', 'example'] },
            { title: 'Email Configuration', description: 'Setup automated email alerts', url: '/email-config', icon: 'fas fa-envelope', keywords: ['email', 'smtp', 'alerts', 'notifications', 'config'] },
            { title: 'Dashboard', description: 'Main inventory dashboard', url: '/', icon: 'fas fa-home', keywords: ['dashboard', 'home', 'main', 'overview'] },
            { title: 'Analysis Results', description: 'View analysis results and reports', url: '/results', icon: 'fas fa-chart-pie', keywords: ['results', 'analysis', 'reports', 'charts'] },
            { title: 'Export Data', description: 'Download analysis results as CSV', action: 'exportData', icon: 'fas fa-download', keywords: ['export', 'download', 'csv', 'save'] },
            { title: 'Help Center', description: 'Get help and support', action: 'showHelp', icon: 'fas fa-question-circle', keywords: ['help', 'support', 'guide', 'tutorial'] },
            { title: 'Theme Settings', description: 'Switch between light/dark theme', action: 'toggleTheme', icon: 'fas fa-palette', keywords: ['theme', 'dark', 'light', 'appearance'] },
            { title: 'About System', description: 'About Inventory Management Pro', action: 'showAbout', icon: 'fas fa-info-circle', keywords: ['about', 'version', 'info', 'system'] }
        ];
        this.initializeSearch();
    }

    initializeSearch() {
        // Setup main search
        this.setupSearchInput('searchInput', 'searchSuggestions');
        // Setup mobile search
        this.setupSearchInput('mobileSearchInput', 'mobileSearchSuggestions');
    }

    setupSearchInput(inputId, suggestionsId) {
        const input = document.getElementById(inputId);
        if (!input) return;

        let suggestions = document.getElementById(suggestionsId);
        if (!suggestions) {
            suggestions = this.createSuggestionsElement(input, suggestionsId);
        }

        input.addEventListener('input', (e) => {
            this.handleSearchInput(e.target.value, suggestions);
        });

        input.addEventListener('focus', (e) => {
            if (e.target.value.trim()) {
                this.handleSearchInput(e.target.value, suggestions);
            }
        });

        // Keyboard navigation
        input.addEventListener('keydown', (e) => {
            this.handleKeyNavigation(e, suggestions);
        });

        // Hide suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!input.contains(e.target) && !suggestions.contains(e.target)) {
                suggestions.style.display = 'none';
            }
        });
    }

    createSuggestionsElement(input, id) {
        const suggestions = document.createElement('div');
        suggestions.id = id;
        suggestions.className = 'search-suggestions';
        input.parentNode.style.position = 'relative';
        input.parentNode.appendChild(suggestions);
        return suggestions;
    }

    handleSearchInput(query, suggestionsElement) {
        const trimmedQuery = query.toLowerCase().trim();
        
        if (trimmedQuery.length === 0) {
            suggestionsElement.style.display = 'none';
            return;
        }

        const filtered = this.suggestions.filter(item => {
            return item.title.toLowerCase().includes(trimmedQuery) || 
                   item.description.toLowerCase().includes(trimmedQuery) ||
                   item.keywords.some(keyword => keyword.includes(trimmedQuery));
        });

        if (filtered.length > 0) {
            suggestionsElement.innerHTML = filtered.map((item, index) => `
                <div class="suggestion-item" data-index="${index}" onclick="searchManager.handleSuggestionClick('${item.url || ''}', '${item.action || ''}')">
                    <i class="${item.icon} me-2 text-primary"></i>
                    <div class="d-inline-block">
                        <strong>${this.highlightMatch(item.title, trimmedQuery)}</strong>
                        <br><small class="text-muted">${item.description}</small>
                    </div>
                </div>
            `).join('');
            suggestionsElement.style.display = 'block';
        } else {
            suggestionsElement.innerHTML = '<div class="suggestion-item text-muted">No results found</div>';
            suggestionsElement.style.display = 'block';
        }
    }

    highlightMatch(text, query) {
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }

    handleKeyNavigation(e, suggestions) {
        const items = suggestions.querySelectorAll('.suggestion-item[data-index]');
        if (items.length === 0) return;

        let currentActive = suggestions.querySelector('.suggestion-item.active');
        let activeIndex = currentActive ? parseInt(currentActive.dataset.index) : -1;

        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                activeIndex = Math.min(activeIndex + 1, items.length - 1);
                this.setActiveItem(items, activeIndex);
                break;
            case 'ArrowUp':
                e.preventDefault();
                activeIndex = Math.max(activeIndex - 1, 0);
                this.setActiveItem(items, activeIndex);
                break;
            case 'Enter':
                e.preventDefault();
                if (currentActive) {
                    currentActive.click();
                }
                break;
            case 'Escape':
                suggestions.style.display = 'none';
                break;
        }
    }

    setActiveItem(items, activeIndex) {
        items.forEach(item => item.classList.remove('active'));
        if (items[activeIndex]) {
            items[activeIndex].classList.add('active');
            items[activeIndex].scrollIntoView({ block: 'nearest' });
        }
    }

    handleSuggestionClick(url, action) {
        // Clear search
        document.querySelectorAll('.search-input').forEach(input => input.value = '');
        document.querySelectorAll('.search-suggestions').forEach(sugg => sugg.style.display = 'none');

        if (url) {
            window.location.href = url;
        } else if (action && window[action]) {
            window[action]();
        }
    }
}

// Theme Management
class ThemeManager {
    constructor() {
        this.currentTheme = this.loadTheme();
        this.applyTheme(this.currentTheme);
        this.setupThemeToggle();
    }

    loadTheme() {
        return localStorage.getItem('theme') || 'light';
    }

    saveTheme(theme) {
        localStorage.setItem('theme', theme);
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.updateThemeIcon(theme);
        this.currentTheme = theme;
        
        // Notify listeners
        themeChangeListeners.forEach(callback => callback(theme));
    }

    updateThemeIcon(theme) {
        const themeIcon = document.getElementById('themeIcon');
        if (themeIcon) {
            themeIcon.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
        }
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
        this.saveTheme(newTheme);
        
        // Show notification
        showNotification(`Switched to ${newTheme} theme`, 'success');
    }

    setupThemeToggle() {
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
    }
}

// File upload validation
function validateFileUpload(input) {
    const file = input.files[0];
    const maxSize = 16 * 1024 * 1024; // 16MB
    
    if (file) {
        if (file.size > maxSize) {
            showNotification('File size too large. Maximum size is 16MB.', 'error');
            input.value = '';
            return false;
        }
        
        if (!file.name.toLowerCase().endsWith('.csv')) {
            showNotification('Please select a CSV file.', 'error');
            input.value = '';
            return false;
        }
        
        showNotification(`File "${file.name}" selected successfully!`, 'success');
    }
    
    return true;
}

// Progress bar animation
function animateProgressBar(element, targetPercentage, duration = 1000) {
    const startPercentage = 0;
    const startTime = performance.now();
    
    function updateProgress(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const currentPercentage = startPercentage + (targetPercentage - startPercentage) * progress;
        
        element.style.width = currentPercentage + '%';
        element.setAttribute('aria-valuenow', currentPercentage);
        
        if (progress < 1) {
            requestAnimationFrame(updateProgress);
        }
    }
    
    requestAnimationFrame(updateProgress);
}

// Enhanced menu actions
function exportData() {
    const sessionId = document.body.dataset.sessionId || '';
    if (sessionId) {
        window.location.href = `/export-results/${sessionId}`;
    } else {
        showNotification('No analysis results available to export. Please run an analysis first.', 'warning');
    }
}

function showHelp() {
    const helpModal = `
        <div class="modal fade" id="helpModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="fas fa-question-circle me-2"></i>Help & Support</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6><i class="fas fa-rocket me-2 text-primary"></i>Quick Start Guide</h6>
                                <ol>
                                    <li>Upload your CSV file or use sample data</li>
                                    <li>Wait for analysis to complete (usually 2-5 seconds)</li>
                                    <li>Review recommendations and alerts</li>
                                    <li>Export results or configure email alerts</li>
                                </ol>
                                
                                <h6><i class="fas fa-file-csv me-2 text-success"></i>CSV Requirements</h6>
                                <p><strong>Required columns:</strong></p>
                                <ul>
                                    <li><code>product_id</code> - Unique identifier</li>
                                    <li><code>product_name</code> - Product name</li>
                                    <li><code>current_stock</code> - Current quantity</li>
                                    <li><code>ideal_stock_level</code> - Target quantity</li>
                                    <li><code>status</code> - Current status</li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h6><i class="fas fa-search me-2 text-info"></i>Search Features</h6>
                                <p>Use the search bar to quickly navigate:</p>
                                <ul>
                                    <li>Type "csv" for upload options</li>
                                    <li>Type "email" for notification setup</li>
                                    <li>Type "theme" to change appearance</li>
                                    <li>Type "help" for this guide</li>
                                </ul>
                                
                                <h6><i class="fas fa-palette me-2 text-warning"></i>Theme Options</h6>
                                <p>Switch between light and dark themes using the theme toggle button in the navigation bar.</p>
                                
                                <h6><i class="fas fa-envelope me-2 text-danger"></i>Email Setup</h6>
                                <p>Configure SMTP settings to receive automated alerts for critical inventory situations.</p>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', helpModal);
    const modal = new bootstrap.Modal(document.getElementById('helpModal'));
    modal.show();
    
    // Remove modal after hiding
    document.getElementById('helpModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

function showAbout() {
    const aboutModal = `
        <div class="modal fade" id="aboutModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title"><i class="fas fa-info-circle me-2"></i>About Inventory Pro</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body text-center">
                        <i class="fas fa-chart-line fa-4x text-primary mb-3"></i>
                        <h4>Inventory Management Pro</h4>
                        <p class="text-muted">Version 2.1 - Enhanced Edition</p>
                        <p>Professional inventory optimization with predictive analytics, automated email alerts, and modern UI.</p>
                        <hr>
                        <div class="row">
                            <div class="col-6">
                                <h6>✨ Features</h6>
                                <ul class="list-unstyled small">
                                    <li><i class="fas fa-check text-success me-1"></i>AI-powered analysis</li>
                                    <li><i class="fas fa-check text-success me-1"></i>Email notifications</li>
                                    <li><i class="fas fa-check text-success me-1"></i>Dark/Light themes</li>
                                    <li><i class="fas fa-check text-success me-1"></i>Smart search</li>
                                </ul>
                            </div>
                            <div class="col-6">
                                <h6>🚀 Tech Stack</h6>
                                <ul class="list-unstyled small">
                                    <li><i class="fab fa-python me-1"></i>Python Flask</li>
                                    <li><i class="fab fa-bootstrap me-1"></i>Bootstrap 5</li>
                                    <li><i class="fas fa-chart-bar me-1"></i>Matplotlib</li>
                                    <li><i class="fas fa-envelope me-1"></i>SMTP Integration</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Awesome!</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', aboutModal);
    const modal = new bootstrap.Modal(document.getElementById('aboutModal'));
    modal.show();
    
    // Remove modal after hiding
    document.getElementById('aboutModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// Global instances
let searchManager;
let themeManager;

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize managers
    themeManager = new ThemeManager();
    searchManager = new SearchManager();
    
    // Initialize tooltips and popovers
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // File input validation
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            validateFileUpload(this);
        });
    }
    
    // Set session ID if available for export functionality
    const analysisId = '{{ session.get("analysis_id", "") }}';
    if (analysisId) {
        document.body.dataset.sessionId = analysisId;
    }
});

// Global functions for template access
window.toggleTheme = () => themeManager.toggleTheme();
window.exportData = exportData;
window.showHelp = showHelp;
window.showAbout = showAbout;
window.searchManager = searchManager;
