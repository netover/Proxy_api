/**
 * Model Discovery JavaScript Module
 * Handles dynamic model loading, selection, and validation for the LLM Proxy Web UI
 */

class ModelDiscoveryManager {
    constructor() {
        this.cache = new Map();
        this.validatingModels = new Set();
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadInitialModels();
    }

    bindEvents() {
        // Bind refresh buttons
        document.querySelectorAll('.model-refresh-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const providerIndex = e.target.dataset.providerIndex;
                this.refreshModels(providerIndex);
            });
        });

        // Bind manual input toggles
        document.querySelectorAll('.manual-input-toggle').forEach(toggle => {
            toggle.addEventListener('change', (e) => {
                const providerIndex = e.target.dataset.providerIndex;
                this.toggleManualInput(providerIndex, e.target.checked);
            });
        });

        // Bind dropdown changes
        document.querySelectorAll('.model-dropdown').forEach(dropdown => {
            dropdown.addEventListener('change', (e) => {
                const providerIndex = e.target.dataset.providerIndex;
                this.handleModelSelection(providerIndex, e.target.value);
            });
        });

        // Bind textarea validation
        document.querySelectorAll('.model-textarea').forEach(textarea => {
            textarea.addEventListener('input', (e) => {
                const providerIndex = this.getProviderIndexFromElement(e.target);
                this.validateModels(providerIndex, e.target.value);
            });
        });
    }

    async loadInitialModels() {
        // Load models for all providers on page load
        document.querySelectorAll('.model-refresh-btn').forEach(btn => {
            const providerIndex = btn.dataset.providerIndex;
            this.refreshModels(providerIndex);
        });
    }

    async refreshModels(providerIndex) {
        const dropdown = document.getElementById(`models-dropdown-${providerIndex}`);
        const loading = document.getElementById(`loading-${providerIndex}`);
        const feedback = document.getElementById(`validation-${providerIndex}`);
        const refreshBtn = document.querySelector(`[data-provider-index="${providerIndex}"].model-refresh-btn`);

        if (!dropdown || !loading || !feedback || !refreshBtn) return;

        try {
            // Show loading state
            this.showLoading(providerIndex, true);
            refreshBtn.disabled = true;
            feedback.textContent = '';
            feedback.className = 'model-validation-feedback';

            // Fetch models
            const response = await fetch(`/api/models/discover/${providerIndex}`);
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // Update dropdown
            this.populateDropdown(dropdown, data.models);
            
            // Cache the models
            this.cache.set(providerIndex, data.models);
            
            feedback.textContent = `Found ${data.count} models`;
            feedback.className = 'model-validation-feedback success';

        } catch (error) {
            console.error('Error refreshing models:', error);
            feedback.textContent = `Error: ${error.message}`;
            feedback.className = 'model-validation-feedback error';
        } finally {
            this.showLoading(providerIndex, false);
            refreshBtn.disabled = false;
        }
    }

    populateDropdown(dropdown, models) {
        // Clear existing options except the first one
        while (dropdown.children.length > 1) {
            dropdown.removeChild(dropdown.lastChild);
        }

        // Add new model options
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = `${model.id} ${model.owned_by ? `(${model.owned_by})` : ''}`;
            option.title = model.object || '';
            dropdown.appendChild(option);
        });
    }

    handleModelSelection(providerIndex, selectedModel) {
        if (!selectedModel) return;

        const textarea = document.getElementById(`models-${providerIndex}`);
        if (!textarea) return;

        // Get current models
        const currentModels = textarea.value.split(',').map(m => m.trim()).filter(m => m);
        
        // Add selected model if not already present
        if (!currentModels.includes(selectedModel)) {
            currentModels.push(selectedModel);
            textarea.value = currentModels.join(', ');
            this.validateModels(providerIndex, textarea.value);
        }
    }

    toggleManualInput(providerIndex, isManual) {
        const dropdown = document.getElementById(`models-dropdown-${providerIndex}`);
        const refreshBtn = document.querySelector(`[data-provider-index="${providerIndex}"].model-refresh-btn`);
        
        if (dropdown) dropdown.style.display = isManual ? 'none' : 'block';
        if (refreshBtn) refreshBtn.style.display = isManual ? 'none' : 'inline-block';
    }

    async validateModels(providerIndex, modelsText) {
        const feedback = document.getElementById(`validation-${providerIndex}`);
        if (!feedback || !modelsText.trim()) return;

        const models = modelsText.split(',').map(m => m.trim()).filter(m => m);
        if (models.length === 0) return;

        feedback.textContent = 'Validating models...';
        feedback.className = 'model-validation-feedback';

        const validationPromises = models.map(async (model) => {
            if (this.validatingModels.has(`${providerIndex}-${model}`)) {
                return null;
            }

            this.validatingModels.add(`${providerIndex}-${model}`);
            
            try {
                const response = await fetch(`/api/models/validate/${providerIndex}/${encodeURIComponent(model)}`);
                const data = await response.json();
                
                return {
                    model,
                    valid: data.valid,
                    error: data.error
                };
            } catch (error) {
                return {
                    model,
                    valid: false,
                    error: error.message
                };
            } finally {
                this.validatingModels.delete(`${providerIndex}-${model}`);
            }
        });

        try {
            const results = await Promise.all(validationPromises);
            const validResults = results.filter(r => r !== null);
            
            if (validResults.length === 0) return;

            const validModels = validResults.filter(r => r.valid);
            const invalidModels = validResults.filter(r => !r.valid);

            let message = '';
            let className = 'model-validation-feedback';

            if (invalidModels.length === 0) {
                message = `All ${validModels.length} models are valid`;
                className += ' success';
            } else if (validModels.length === 0) {
                message = `All models are invalid: ${invalidModels.map(m => m.model).join(', ')}`;
                className += ' error';
            } else {
                message = `${validModels.length} valid, ${invalidModels.length} invalid`;
                if (invalidModels.length > 0) {
                    message += `: ${invalidModels.map(m => `${m.model} (${m.error})`).join(', ')}`;
                }
                className += ' warning';
            }

            feedback.textContent = message;
            feedback.className = className;

        } catch (error) {
            console.error('Error validating models:', error);
            feedback.textContent = 'Error validating models';
            feedback.className = 'model-validation-feedback error';
        }
    }

    showLoading(providerIndex, show) {
        const loading = document.getElementById(`loading-${providerIndex}`);
        if (loading) {
            loading.style.display = show ? 'block' : 'none';
        }
    }

    getProviderIndexFromElement(element) {
        // Find the provider index from the element's context
        const providerCard = element.closest('.provider-card');
        if (!providerCard) return null;

        // Find the index by looking at the textarea name
        const textarea = providerCard.querySelector('textarea[name^="models_"]');
        if (textarea) {
            const match = textarea.name.match(/models_(\d+)/);
            return match ? match[1] : null;
        }

        return null;
    }

    // Utility method to clear cache for a specific provider
    clearCache(providerIndex) {
        this.cache.delete(providerIndex);
    }

    // Utility method to clear all cache
    clearAllCache() {
        this.cache.clear();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.modelDiscovery = new ModelDiscoveryManager();
});

// Export for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ModelDiscoveryManager;
}