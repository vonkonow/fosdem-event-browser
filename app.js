/**
 * FOSDEM Event Browser Application
 * Pure JavaScript - no dependencies
 */

class FOSDEMBrowser {
    constructor() {
        this.events = [];
        this.filteredEvents = [];
        this.favorites = this.loadFavorites();
        this.scrapedAt = null;
        
        this.init();
    }

            init() {
        // Load events from embedded data (no server needed!)
        // Show loading state immediately
        const container = document.getElementById('eventsList');
        if (container) {
            container.innerHTML = '<div class="loading">Loading events...</div>';
        }
        
        // Defer parsing to avoid blocking the UI
        const parseData = () => {
            try {
                // Get data from script tag (faster and cleaner than embedded string)
                const dataScript = document.getElementById('events-data');
                if (!dataScript) {
                    throw new Error('Events data not found');
                }
                const data = JSON.parse(dataScript.textContent);
                // Handle both old format (array) and new format (object with metadata)
                if (Array.isArray(data)) {
                    this.events = data;
                    this.scrapedAt = null;
                } else {
                    this.events = data.events || [];
                    this.scrapedAt = data.scrapedAt || null;
                }
                console.log(`Loaded ${this.events.length} events`);
                
                // Setup after data is loaded
                this.populateTrackFilter();
                document.getElementById('searchInput').addEventListener('input', () => this.filterEvents());
                document.getElementById('favoritesOnly').addEventListener('change', () => this.filterEvents());
                document.getElementById('sortBy').addEventListener('change', () => this.filterEvents());
                document.getElementById('dayFilter').addEventListener('change', () => this.filterEvents());
                document.getElementById('trackFilter').addEventListener('change', () => this.filterEvents());
                document.getElementById('exportFavorites').addEventListener('click', () => this.saveFavoritesToFile());
                document.getElementById('importFavorites').addEventListener('click', () => this.loadFavoritesFromFile());
                
                // Initial render
                this.filterEvents();
            } catch (error) {
                this.showError(`Error parsing events data: ${error.message}`);
            }
        };
        
        // Use requestIdleCallback for better performance, fallback to setTimeout
        if (window.requestIdleCallback) {
            requestIdleCallback(parseData, { timeout: 1000 });
        } else {
            setTimeout(parseData, 0);
        }
    }










    loadFavorites() {
        try {
            const stored = localStorage.getItem('fosdem-favorites');
            if (!stored) return [];
            const parsed = JSON.parse(stored);
            // Validate it's an array
            if (!Array.isArray(parsed)) {
                console.warn('Invalid favorites data in localStorage, resetting');
                localStorage.removeItem('fosdem-favorites');
                return [];
            }
            return parsed;
        } catch (error) {
            console.warn('Error loading favorites from localStorage:', error);
            localStorage.removeItem('fosdem-favorites');
            return [];
        }
    }

    saveFavorites() {
        localStorage.setItem('fosdem-favorites', JSON.stringify(this.favorites));
    }

    toggleFavorite(eventId) {
        const index = this.favorites.indexOf(eventId);
        if (index > -1) {
            this.favorites.splice(index, 1);
        } else {
            this.favorites.push(eventId);
        }
        this.saveFavorites();
        this.updateStats();
        this.renderEvents();
    }

    isFavorite(eventId) {
        return this.favorites.includes(eventId);
    }

    saveFavoritesToFile() {
        const favoritesJson = JSON.stringify(this.favorites, null, 2);
        const blob = new Blob([favoritesJson], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'fosdem-favorites.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        // Visual feedback
        const btn = document.getElementById('exportFavorites');
        const originalText = btn.textContent;
        btn.textContent = '✓';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 1500);
    }

    loadFavoritesFromFile() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = (event) => {
                try {
                    const imported = JSON.parse(event.target.result);
                    
                    if (!Array.isArray(imported)) {
                        throw new Error('Favorites data must be an array');
                    }
                    
                    // Validate that all items are strings (event IDs)
                    if (!imported.every(id => typeof id === 'string')) {
                        throw new Error('All favorite items must be event ID strings');
                    }
                    
                    // Confirm before overwriting
                    const currentCount = this.favorites.length;
                    const importedCount = imported.length;
                    if (currentCount > 0 && !confirm(`This will replace your ${currentCount} current favorites with ${importedCount} imported favorites. Continue?`)) {
                        return;
                    }
                    
                    this.favorites = imported;
                    this.saveFavorites();
                    this.updateStats();
                    this.filterEvents();
                    
                    // Visual feedback
                    const btn = document.getElementById('importFavorites');
                    const originalText = btn.textContent;
                    btn.textContent = '✓';
                    setTimeout(() => {
                        btn.textContent = originalText;
                    }, 1500);
                } catch (error) {
                    alert(`Error loading favorites: ${error.message}`);
                }
            };
            reader.readAsText(file);
        };
        input.click();
    }

    populateTrackFilter() {
        // Get all unique tracks
        const tracks = new Set();
        this.events.forEach(event => {
            if (event.track) {
                tracks.add(event.track);
            }
        });
        
        // Sort tracks alphabetically
        const sortedTracks = Array.from(tracks).sort();
        
        // Populate dropdown
        const trackFilter = document.getElementById('trackFilter');
        sortedTracks.forEach(track => {
            const option = document.createElement('option');
            option.value = track;
            option.textContent = track;
            trackFilter.appendChild(option);
        });
    }

    filterEvents() {
        const searchTerm = document.getElementById('searchInput').value.toLowerCase();
        const favoritesOnly = document.getElementById('favoritesOnly').checked;
        const sortBy = document.getElementById('sortBy').value;
        const dayFilter = document.getElementById('dayFilter').value;
        const trackFilter = document.getElementById('trackFilter').value;

        // Filter events
        this.filteredEvents = this.events.filter(event => {
            // Favorites filter
            if (favoritesOnly && !this.isFavorite(event.id)) {
                return false;
            }

            // Day filter
            if (dayFilter !== 'all' && event.day?.id !== dayFilter) {
                return false;
            }

            // Track filter
            if (trackFilter !== 'all' && event.track !== trackFilter) {
                return false;
            }

            // Search filter
            if (searchTerm) {
                const searchable = [
                    event.title || '',
                    ...(event.speakers || []).map(s => s?.name || '').filter(Boolean),
                    event.room?.name || '',
                    event.track || ''
                ].join(' ').toLowerCase();
                
                if (!searchable.includes(searchTerm)) {
                    return false;
                }
            }

            return true;
        });

        // Sort events
        const dayOrder = { 'saturday': 0, 'sunday': 1 };
        this.filteredEvents.sort((a, b) => {
            switch (sortBy) {
                case 'time':
                    // Sort by day first, then time
                    const aDay = dayOrder[a.day?.id] ?? 2;
                    const bDay = dayOrder[b.day?.id] ?? 2;
                    if (aDay !== bDay) return aDay - bDay;
                    return (a.startTime || '99:99').localeCompare(b.startTime || '99:99');
                
                case 'title':
                    return a.title.localeCompare(b.title);
                
                case 'room':
                    return (a.room?.name || 'ZZZ').localeCompare(b.room?.name || 'ZZZ');
                
                case 'day':
                    return (dayOrder[a.day?.id] ?? 2) - (dayOrder[b.day?.id] ?? 2);
                
                case 'track':
                    return (a.track || 'ZZZ').localeCompare(b.track || 'ZZZ');
                
                default:
                    return 0;
            }
        });

        this.updateStats();
        this.renderEvents();
    }

    updateStats() {
        document.getElementById('eventCount').textContent = `${this.filteredEvents.length} events`;
        document.getElementById('favoriteCount').textContent = `${this.favorites.length} favorites`;
        
        // Update scraping timestamp if available
        const timestampEl = document.getElementById('scrapedTimestamp');
        if (timestampEl && this.scrapedAt) {
            try {
                const date = new Date(this.scrapedAt);
                const formatted = date.toLocaleString(undefined, {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
                timestampEl.textContent = `Scraped: ${formatted}`;
            } catch (e) {
                timestampEl.textContent = `Scraped: ${this.scrapedAt}`;
            }
        } else if (timestampEl) {
            timestampEl.textContent = '';
        }
    }

    renderEvents() {
        const container = document.getElementById('eventsList');
        
        if (this.filteredEvents.length === 0) {
            container.innerHTML = '<div class="no-events">No events match your filters.</div>';
            return;
        }

        container.innerHTML = this.filteredEvents.map(event => {
            const isFav = this.isFavorite(event.id);
            
            // Prepare metadata for tooltip
            const hasTooltip = event.abstract || event.description || event.room || event.startTime || event.videoLink || event.chatLink;
            
            // Format: Title | Track | DateTime | Star
            const dayShort = event.day?.name === 'Saturday' ? 'Sat' : event.day?.name === 'Sunday' ? 'Sun' : '';
            const timeInfo = event.startTime ? `${dayShort} ${event.startTime}`.trim() : '';
            const trackInfo = event.track ? this.escapeHtml(event.track) : '';
            const title = this.escapeHtml(event.title);

            return `
                <div class="event-card ${isFav ? 'favorite' : ''}">
                    <div class="event-line">
                        <span class="event-title ${hasTooltip ? 'has-tooltip' : ''}" 
                              ${hasTooltip ? `data-event-id="${this.escapeHtml(event.id)}"` : ''}>
                            <a href="${event.link}" target="_blank" rel="noopener">${title}</a>
                        </span>
                        ${trackInfo ? `<span class="event-track">${trackInfo}</span>` : ''}
                        <span class="event-time">${timeInfo}</span>
                        <button class="favorite-btn ${isFav ? 'active' : ''}" 
                                data-event-id="${this.escapeHtml(event.id)}"
                                aria-label="${isFav ? 'Remove from' : 'Add to'} favorites">
                            ${isFav ? '★' : '☆'}
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        
        // Setup tooltip and favorite button event listeners
        container.querySelectorAll('.event-title.has-tooltip').forEach(titleEl => {
            const eventId = titleEl.getAttribute('data-event-id');
            if (!eventId) return;
            
            const event = this.events.find(ev => ev.id === eventId);
            if (!event) return;
            
            titleEl.addEventListener('mouseenter', (e) => this.showTooltip(e, event));
            titleEl.addEventListener('mouseleave', () => this.hideTooltip());
        });
        
        // Setup favorite button click handlers (using event delegation for better performance)
        container.querySelectorAll('.favorite-btn').forEach(btn => {
            const eventId = btn.getAttribute('data-event-id');
            if (eventId) {
                btn.addEventListener('click', () => this.toggleFavorite(eventId));
            }
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showTooltip(e, event) {
        // Remove existing tooltip
        this.hideTooltip();
        
        // Build tooltip content - description first, then metadata
        let content = '';
        let metadata = '';
        
        // Abstract/Description at the top
        if (event.abstract) {
            content += `<div class="tooltip-abstract">${this.escapeHtml(event.abstract)}</div>`;
        }
        if (event.description && event.description !== event.abstract) {
            content += `<div class="tooltip-abstract">${this.escapeHtml(event.description)}</div>`;
        }
        
        // Metadata at the bottom
        if (event.room) {
            metadata += `<div class="tooltip-row"><strong>📍 Room:</strong> ${this.escapeHtml(event.room.name)}</div>`;
        }
        
        if (event.startTime || event.endTime) {
            const dayName = event.day?.name || '';
            const timeStr = event.startTime && event.endTime 
                ? `${event.startTime} - ${event.endTime}`
                : event.startTime || event.endTime || '';
            if (dayName || timeStr) {
                metadata += `<div class="tooltip-row"><strong>🕐 Time:</strong> ${dayName ? dayName + ' ' : ''}${timeStr}</div>`;
            }
        }
        
        if (event.videoLink) {
            metadata += `<div class="tooltip-row"><strong>🎥 Video:</strong> <a href="${this.escapeHtml(event.videoLink)}" target="_blank" rel="noopener">Watch live</a></div>`;
        }
        
        if (event.chatLink) {
            metadata += `<div class="tooltip-row"><strong>💬 Chat:</strong> <a href="${this.escapeHtml(event.chatLink)}" target="_blank" rel="noopener">Join conversation</a></div>`;
        }
        
        // Add divider and metadata if both exist
        if (content && metadata) {
            content += `<div class="tooltip-divider"></div>`;
            content += metadata;
        } else if (metadata) {
            content = metadata;
        }
        
        if (!content) return;
        
        // Create tooltip element
        const tooltip = document.createElement('div');
        tooltip.id = 'event-tooltip';
        tooltip.className = 'tooltip';
        tooltip.innerHTML = content;
        document.body.appendChild(tooltip);
        
        // Position tooltip above the title
        const rect = e.currentTarget.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        const left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
        const top = rect.top - tooltipRect.height - 8;
        
        tooltip.style.left = `${Math.max(10, Math.min(left, window.innerWidth - tooltipRect.width - 10))}px`;
        tooltip.style.top = `${Math.max(10, top)}px`;
        
        // Show tooltip
        setTimeout(() => {
            tooltip.classList.add('show');
        }, 10);
    }

    hideTooltip() {
        const tooltip = document.getElementById('event-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    }

    showError(message) {
        const container = document.getElementById('eventsList');
        container.innerHTML = `<div class="error">${this.escapeHtml(message)}</div>`;
    }
}

// Initialize app
const app = new FOSDEMBrowser();
