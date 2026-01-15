/**
 * Advanced Phone Filters
 * Provides comprehensive filtering and search capabilities
 */

class PhoneFilters {
    constructor() {
        this.filters = {
            search: '',
            brands: [],
            priceRange: { min: 0, max: Infinity },
            storage: [],
            stores: [],
            confidence: 'all',
            sortBy: 'price_asc'
        };
        
        this.allPhones = [];
        this.filteredPhones = [];
    }
    
    init(phones) {
        this.allPhones = phones;
        this.applyFilters();
    }
    
    setSearchTerm(term) {
        this.filters.search = term.toLowerCase();
        this.applyFilters();
    }
    
    setPriceRange(min, max) {
        this.filters.priceRange = { min, max };
        this.applyFilters();
    }
    
    toggleBrand(brand) {
        const index = this.filters.brands.indexOf(brand);
        if (index > -1) {
            this.filters.brands.splice(index, 1);
        } else {
            this.filters.brands.push(brand);
        }
        this.applyFilters();
    }
    
    setConfidence(level) {
        this.filters.confidence = level;
        this.applyFilters();
    }
    
    setSortBy(sortBy) {
        this.filters.sortBy = sortBy;
        this.applyFilters();
    }
    
    applyFilters() {
        let filtered = [...this.allPhones];
        
        // Search filter
        if (this.filters.search) {
            filtered = filtered.filter(phone => {
                const searchText = `${phone.brand} ${phone.model}`.toLowerCase();
                return searchText.includes(this.filters.search);
            });
        }
        
        // Brand filter
        if (this.filters.brands.length > 0) {
            filtered = filtered.filter(phone => 
                this.filters.brands.includes(phone.brand)
            );
        }
        
        // Price range filter
        filtered = filtered.filter(phone => {
            const price = phone.best_price || 0;
            return price >= this.filters.priceRange.min && 
                   price <= this.filters.priceRange.max;
        });
        
        // Confidence filter
        if (this.filters.confidence === 'high') {
            filtered = filtered.filter(phone => 
                (phone.confidence || 0) >= 0.75
            );
        }
        
        // Sort
        filtered = this.sortPhones(filtered);
        
        this.filteredPhones = filtered;
        this.renderResults();
    }
    
    sortPhones(phones) {
        const sorted = [...phones];
        
        switch (this.filters.sortBy) {
            case 'price_asc':
                sorted.sort((a, b) => (a.best_price || Infinity) - (b.best_price || Infinity));
                break;
            case 'price_desc':
                sorted.sort((a, b) => (b.best_price || 0) - (a.best_price || 0));
                break;
            case 'confidence_desc':
                sorted.sort((a, b) => (b.confidence || 0) - (a.confidence || 0));
                break;
            case 'brand_asc':
                sorted.sort((a, b) => (a.brand || '').localeCompare(b.brand || ''));
                break;
        }
        
        return sorted;
    }
    
    renderResults() {
        // Update result count
        const countElement = document.getElementById('result-count');
        if (countElement) {
            countElement.textContent = `${this.filteredPhones.length} phones found`;
        }
        
        // Trigger re-render (integrate with existing render logic)
        if (window.renderPhones) {
            window.renderPhones(this.filteredPhones);
        }
    }
    
    reset() {
        this.filters = {
            search: '',
            brands: [],
            priceRange: { min: 0, max: Infinity },
            storage: [],
            stores: [],
            confidence: 'all',
            sortBy: 'price_asc'
        };
        this.applyFilters();
    }
}

// Export for use in main app
if (typeof window !== 'undefined') {
    window.PhoneFilters = PhoneFilters;
}
