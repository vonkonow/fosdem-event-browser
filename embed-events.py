#!/usr/bin/env python3
"""
Embed events.json into app.js to create a standalone version
that works without a server (file:// protocol)
"""

import json
import os

print("Creating standalone version...")

# Read events.json
if not os.path.exists('events.json'):
    print("Error: events.json not found. Run: python fetch-events.py")
    exit(1)

with open('events.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Handle both old format (array) and new format (object with metadata)
if isinstance(data, list):
    # Old format - just an array
    events = data
    scraped_at = None
else:
    # New format - object with scrapedAt and events
    events = data.get('events', [])
    scraped_at = data.get('scrapedAt')

print(f"Loaded {len(events)} events")
if scraped_at:
    print(f"Data scraped at: {scraped_at}")

# Read app.js
with open('app.js', 'r', encoding='utf-8') as f:
    app_js = f.read()

# Find and replace the init method - handle both embedded and non-embedded versions
# Pattern to match init() method that loads events
import re

# Create embedded version - use JSON.parse for faster loading
# Store JSON in a script tag in HTML for cleaner separation
# Include metadata (scrapedAt) if available
data_to_embed = {
    'events': events
}
if scraped_at:
    data_to_embed['scrapedAt'] = scraped_at
events_json = json.dumps(data_to_embed, ensure_ascii=False)
# Escape </script> to prevent breaking out of script tag (JSON injection protection)
events_json = events_json.replace('</script>', '<\\/script>')

new_init = """    init() {
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
"""

# Replace the init method - find the entire method body
# Look for "init() {" and find the matching closing brace
init_start = app_js.find('init() {')
if init_start == -1:
    # Try with whitespace
    init_start = app_js.find('init()')
    if init_start != -1:
        # Find the opening brace
        brace_start = app_js.find('{', init_start)
        if brace_start != -1:
            init_start = brace_start

if init_start != -1:
    # Find the matching closing brace
    brace_count = 0
    i = init_start
    while i < len(app_js):
        if app_js[i] == '{':
            brace_count += 1
        elif app_js[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                # Found the matching closing brace
                init_end = i + 1
                # Replace the entire method
                app_js_embedded = app_js[:init_start] + new_init + app_js[init_end:]
                break
        i += 1
    else:
        print("Warning: Could not find matching closing brace for init() method")
        app_js_embedded = app_js
else:
    print("Warning: Could not find init() method")
    app_js_embedded = app_js

# Save as app.js (overwrite existing)
with open('app.js', 'w', encoding='utf-8') as f:
    f.write(app_js_embedded)

print(f"Created app.js ({len(app_js_embedded)} bytes)")

# Create single-file standalone version
print("\nCreating single-file standalone version...")

# Read CSS
with open('styles.css', 'r', encoding='utf-8') as f:
    css_content = f.read()

# Read the HTML body (without external links)
html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' https://fosdem.org data:; connect-src 'none'; font-src 'self' data:; object-src 'none'; base-uri 'self'; form-action 'none';">
    <title>FOSDEM 2026 Event Browser</title>
    <link rel="icon" type="image/png" href="https://fosdem.org/2026/favicon-32x32.png" sizes="32x32">
    <link rel="icon" type="image/png" href="https://fosdem.org/2026/favicon-16x16.png" sizes="16x16">
    <link rel="apple-touch-icon" href="https://fosdem.org/2026/apple-touch-icon.png">
    <style>
{css}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>FOSDEM 2026</h1>
        </header>

        <div class="controls">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search events, speakers, rooms...">
                <button id="exportFavorites" type="button" title="Save Favorites">💾</button>
                <button id="importFavorites" type="button" title="Load Favorites">📂</button>
            </div>
            
            <div class="filter-controls">
                <label class="checkbox-label">
                    <input type="checkbox" id="favoritesOnly">
                    Show favorites only
                </label>
                
                <select id="sortBy">
                    <option value="track" selected>Sort by Track</option>
                    <option value="time">Sort by Time</option>
                    <option value="title">Sort by Title</option>
                    <option value="room">Sort by Room</option>
                </select>
                
                <select id="dayFilter">
                    <option value="all">All Days</option>
                    <option value="saturday">Saturday</option>
                    <option value="sunday">Sunday</option>
                </select>
                
                <select id="trackFilter">
                    <option value="all">All Tracks</option>
                    <!-- Populated by JavaScript -->
                </select>
            </div>
        </div>

        <div class="stats">
            <span id="eventCount">0 events</span>
            <span id="favoriteCount">0 favorites</span>
            <span id="scrapedTimestamp" class="scraped-timestamp"></span>
        </div>

        <div id="eventsList" class="events-list">
            <div class="loading">Loading events...</div>
        </div>
    </div>

    <script type="application/json" id="events-data">{events_json}</script>
    <script>
{js}
    </script>
</body>
</html>"""

# Create standalone HTML
standalone_html = html_template.format(
    css=css_content,
    events_json=events_json,
    js=app_js_embedded
)

# Save standalone version
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(standalone_html)

print(f"Created index.html ({len(standalone_html)} bytes)")
print("\nSingle-file version ready! Open index.html in your browser.")
print("Everything is embedded - no external files needed!")
