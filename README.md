# FOSDEM 2026 Event Browser

A standalone, pure JavaScript application to browse FOSDEM 2026 events and mark your favorites. **No server needed** - just open the HTML file in your browser!

## Features

- ✅ Browse all FOSDEM 2026 events (1068 events, 71 tracks)
- ✅ Search events by title, speaker, room, or track
- ✅ Filter by track/theme (e.g., "AI Plumbers", "Retrocomputing", "Geospatial")
- ✅ Mark/unmark events as favorites with one click
- ✅ Filter to show only favorites
- ✅ Sort by time, title, room, day, or track (default: by track)
- ✅ Filter by day (Saturday/Sunday)
- ✅ Rich hover tooltips with:
  - Event abstracts/descriptions
  - Room information
  - Start/end times
  - Video and chat links
- ✅ Save/Load favorites to/from JSON files (💾 📂 buttons)
- ✅ Favorites saved in browser localStorage
- ✅ Scraping timestamp displayed in stats
- ✅ Works completely offline - no server needed!
- ✅ Single-file standalone - everything in one HTML file
- ✅ Compact, minimal UI focused on events
- ✅ Security hardened (XSS protection, Content Security Policy)

## Quick Start

### 1. Fetch Events Data

Download the events data from FOSDEM:

```bash
python fetch-events.py
```

This creates an `events.json` file with all the events.

**Note**: The script will also fetch abstracts/descriptions from each event's detail page (for hover tooltips). This may take 10-20 minutes for 1000+ events. You can press `Ctrl+C` to skip metadata fetching and use basic event data only.

### 2. Generate Standalone App

Embed the events into the JavaScript file:

```bash
python embed-events.py
```

This creates:
- `index.html` - **Single-file version** with everything embedded (CSS, JS, and data all in one HTML file)

### 3. Open in Browser

- Double-click `index.html` - Everything in one file!
- Works offline - no server needed!

## Updating Events

If FOSDEM updates their schedule:

1. **Fetch new data**:
   ```bash
   python fetch-events.py
   ```

2. **Regenerate standalone version**:
   ```bash
   python embed-events.py
   ```

3. **Refresh your browser** - you're done!

## How It Works

### Architecture

1. **Data Fetching** (`fetch-events.py`)
   - Python script that fetches HTML from FOSDEM website
   - Parses the events table and extracts structured data
   - Saves to `events.json` (intermediate file)

2. **Embedding** (`embed-events.py`)
   - Reads `events.json` and embeds it into `index.html`
   - Embeds CSS and JavaScript directly into the HTML
   - Creates a single-file standalone version with no external dependencies
   - Includes security protections (JSON injection prevention)

3. **Web Application** (`index.html`)
   - Pure JavaScript, no dependencies
   - All event data, CSS, and JS embedded in a single `index.html` file
   - Uses `localStorage` to persist favorites
   - File-based save/load for favorites (backup and sharing)
   - All filtering/sorting happens client-side
   - Works with `file://` protocol - no server needed!
   - Security features: XSS protection, Content Security Policy, input validation

### Why Standalone?

- ✅ **No server needed** - just open the HTML file
- ✅ **No CORS issues** - data is embedded, not fetched
- ✅ **Privacy** - All data stays on your machine
- ✅ **Offline** - Works without internet
- ✅ **Portable** - Share as a single folder
- ✅ **Simple** - No build step, no dependencies

## File Structure

```
fosdem/
├── fetch-events.py         # Fetch events from FOSDEM (Python)
├── embed-events.py          # Embed events into index.html (Python)
├── index.html               # Single-file version (everything embedded)
├── app.js                   # Application logic (source, embedded into index.html)
├── styles.css               # Styling (source, embedded into index.html)
├── events.json              # Events data (intermediate, generated)
└── README.md                # This file
```

## Requirements

- **Python 3** (for fetching and embedding events)
- **Modern web browser** (Chrome, Firefox, Edge, Safari)

## Browser Compatibility

Works in all modern browsers that support:
- ES6+ JavaScript
- localStorage
- File API (for save/load favorites)
- requestIdleCallback (with setTimeout fallback)

## Usage Tips

**Save/Load Favorites**
- Click 💾 to save your favorites to a JSON file
- Click 📂 to load favorites from a previously saved file
- Useful for backing up or sharing your favorites list

**Hover Tooltips**
- Hover over event titles to see detailed information
- Tooltips show abstracts, room, time, and links to video/chat

**Search and Filter**
- Search box supports searching across titles, speakers, rooms, and tracks
- Combine multiple filters (day, track, favorites) for precise results
- Sort order persists while filtering

## Troubleshooting

**No events showing**
- Make sure you've run both `python fetch-events.py` and `python embed-events.py`
- Check browser console for errors (F12)
- Try regenerating: `python embed-events.py`

**Events are outdated**
- Run `python fetch-events.py` to get latest data
- Then run `python embed-events.py` to regenerate
- Refresh your browser

**Favorites not saving**
- Check browser console for errors (F12)
- Ensure localStorage is enabled in your browser
- Try saving to a file (💾) as a backup

**Save/Load buttons not working**
- Ensure your browser supports the File API
- Check browser console for errors (F12)

## License

This is a personal tool for browsing FOSDEM events. FOSDEM content is licensed under Creative Commons Attribution 4.0.
