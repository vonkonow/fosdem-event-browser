#!/usr/bin/env python3
"""
FOSDEM Events Data Fetcher (Python version)
 
This script fetches events from FOSDEM 2026 and saves them as JSON.
Run: python fetch-events.py

No dependencies required - uses only standard library.
"""

import urllib.request
import urllib.parse
import json
import re
import time

URL = 'https://fosdem.org/2026/schedule/events/'

print('Fetching FOSDEM 2026 events...')

try:
    with urllib.request.urlopen(URL) as response:
        html = response.read().decode('utf-8')
    print(f'Fetched {len(html)} characters of HTML')
    # Debug: check if we got the expected content
    if '/schedule/event/' in html:
        print('Found event links in HTML')
    else:
        print('WARNING: No event links found in HTML. Page structure may be different.')
        # Save a sample for debugging
        with open('debug_html_sample.html', 'w', encoding='utf-8') as f:
            f.write(html[:5000])  # First 5000 chars
        print('Saved first 5000 chars to debug_html_sample.html for inspection')
except Exception as e:
    print(f'Error fetching data: {e}')
    exit(1)

def parse_events_from_html(html_content):
    """Parse events from FOSDEM HTML table - more flexible approach"""
    events = []
    
    # More flexible regex patterns to handle various HTML formats
    # First find event URLs, then extract title from surrounding context
    event_url_pattern = re.compile(r'/2026/schedule/event/([^/"\'>\s]+)')
    speaker_pattern = re.compile(
        r'<a[^>]*href=["\']/2026/schedule/speaker/([^"\']+)["\'][^>]*>([^<]+)</a>',
        re.IGNORECASE
    )
    room_pattern = re.compile(
        r'<a[^>]*href=["\']/2026/schedule/room/([^"\']+)["\'][^>]*>([^<]+)</a>',
        re.IGNORECASE
    )
    day_pattern = re.compile(
        r'<a[^>]*href=["\']/2026/schedule/day/([^"\']+)["\'][^>]*>([^<]+)</a>',
        re.IGNORECASE
    )
    time_pattern = re.compile(r'(\d{1,2}:\d{2})')
    
    # Find all track/theme headers (e.g., <h4>AI Plumbers (23)</h4>)
    track_header_pattern = re.compile(r'<h4>([^<]+) \((\d+)\)</h4>')
    track_headers = []
    for match in track_header_pattern.finditer(html_content):
        track_name = match.group(1).strip()
        track_count = int(match.group(2))
        track_headers.append({
            'name': track_name,
            'count': track_count,
            'position': match.start()
        })
    
    print(f'Found {len(track_headers)} track/theme groupings')
    
    # Find all event URLs
    event_urls = event_url_pattern.findall(html_content)
    print(f'Found {len(event_urls)} event URLs in HTML...')
    
    # Remove duplicates while preserving order
    seen_urls = set()
    unique_urls = []
    for url in event_urls:
        if url not in seen_urls:
            seen_urls.add(url)
            unique_urls.append(url)
    
    print(f'Processing {len(unique_urls)} unique events...')
    
    for event_id in unique_urls:
        try:
            event_link = event_id.rstrip('/')
            # Find the title - the structure is: <a href="...">TITLE<br/><i></i></a>
            # Extract everything between > and < (before any <br/> or </a>)
            title_pattern = re.compile(
                rf'<a[^>]*href=["\']/2026/schedule/event/{re.escape(event_id)}/?["\'][^>]*>([^<]+)',
                re.IGNORECASE
            )
            title_match = title_pattern.search(html_content)
            if not title_match:
                continue
            
            title = title_match.group(1).strip()
            
            # Find the table row containing this event (look for surrounding <tr> tags)
            match_pos = title_match.start()
            
            # Find the most recent track header before this event
            track = None
            for track_header in reversed(track_headers):
                if track_header['position'] < match_pos:
                    track = track_header['name']
                    break
            
            # Find the start of the row
            row_start = html_content.rfind('<tr', 0, match_pos)
            if row_start == -1:
                continue
            
            # Find the end of the row
            row_end = html_content.find('</tr>', match_pos)
            if row_end == -1:
                continue
            
            # Extract the row HTML
            row_html = html_content[row_start:row_end + 5]
            
            # Extract speakers from this row
            speakers = []
            for speaker_match in speaker_pattern.finditer(row_html):
                speakers.append({
                    'id': urllib.parse.unquote(speaker_match.group(1)),
                    'name': speaker_match.group(2).strip()
                })
            
            # Extract room
            room = None
            room_match = room_pattern.search(row_html)
            if room_match:
                room = {
                    'id': urllib.parse.unquote(room_match.group(1)),
                    'name': room_match.group(2).strip()
                }
            
            # Extract day
            day = None
            day_match = day_pattern.search(row_html)
            if day_match:
                day = {
                    'id': urllib.parse.unquote(day_match.group(1)),
                    'name': day_match.group(2).strip()
                }
            
            # Extract times from the row
            time_matches = list(time_pattern.finditer(row_html))
            start_time = ''
            end_time = ''
            
            if len(time_matches) >= 2:
                start_time = time_matches[0].group(1)
                end_time = time_matches[1].group(1)
            elif len(time_matches) == 1:
                start_time = time_matches[0].group(1)
            
            events.append({
                'id': event_id,
                'title': title,
                'link': f'https://fosdem.org/2026/schedule/event/{event_link}/',
                'speakers': speakers,
                'room': room,
                'day': day,
                'startTime': start_time,
                'endTime': end_time,
                'track': track
            })
        except Exception as e:
            # Skip events that fail to parse (only show first few errors)
            if len([ev for ev in events if ev]) < 5:
                print(f'Warning: Failed to parse event {event_id}: {e}')
            continue
    
    # Remove duplicates
    seen_ids = set()
    unique_events = []
    for event in events:
        if event['id'] not in seen_ids:
            seen_ids.add(event['id'])
            unique_events.append(event)
    
    print(f'Parsed {len(unique_events)} unique events')
    return unique_events

def fetch_event_metadata(event_link, delay=0.1):
    """Fetch abstract and description from an event's detail page"""
    try:
        time.sleep(delay)  # Rate limiting - be nice to the server
        with urllib.request.urlopen(event_link) as response:
            html = response.read().decode('utf-8')
        
        # Extract abstract
        abstract = None
        abstract_match = re.search(
            r'<div class="event-abstract">.*?<p>(.*?)</p>',
            html,
            re.DOTALL | re.IGNORECASE
        )
        if abstract_match:
            abstract = re.sub(r'<[^>]+>', '', abstract_match.group(1)).strip()
            # Clean up whitespace
            abstract = ' '.join(abstract.split())
            if abstract:
                abstract = abstract[:500]  # Limit length
        
        # Extract description (if present)
        description = None
        description_match = re.search(
            r'<div class="event-description">(.*?)</div>',
            html,
            re.DOTALL | re.IGNORECASE
        )
        if description_match:
            desc_html = description_match.group(1).strip()
            if desc_html:
                # Remove HTML tags and clean up
                description = re.sub(r'<[^>]+>', '', desc_html).strip()
                description = ' '.join(description.split())
                if description:
                    description = description[:500]  # Limit length
        
        # Extract video link
        video_link = None
        video_match = re.search(
            r'<a[^>]*href=["\'](https://live\.fosdem\.org[^"\']+)["\'][^>]*>',
            html,
            re.IGNORECASE
        )
        if video_match:
            video_link = video_match.group(1)
        
        # Extract chat link
        chat_link = None
        chat_match = re.search(
            r'<a[^>]*href=["\'](https://chat\.fosdem\.org[^"\']+)["\'][^>]*>',
            html,
            re.IGNORECASE
        )
        if chat_match:
            chat_link = chat_match.group(1)
        
        # Extract navicon (favicon)
        navicon = None
        # Try to find favicon-32x32.png first, then favicon-16x16.png, then apple-touch-icon
        favicon_32 = re.search(
            r'<link[^>]*rel=["\']icon["\'][^>]*href=["\']([^"\']*favicon-32x32\.png[^"\']*)["\']',
            html,
            re.IGNORECASE
        )
        if favicon_32:
            navicon = favicon_32.group(1)
        else:
            favicon_16 = re.search(
                r'<link[^>]*rel=["\']icon["\'][^>]*href=["\']([^"\']*favicon-16x16\.png[^"\']*)["\']',
                html,
                re.IGNORECASE
            )
            if favicon_16:
                navicon = favicon_16.group(1)
            else:
                apple_icon = re.search(
                    r'<link[^>]*rel=["\']apple-touch-icon["\'][^>]*href=["\']([^"\']+)["\']',
                    html,
                    re.IGNORECASE
                )
                if apple_icon:
                    navicon = apple_icon.group(1)
        
        # Convert relative URL to absolute if needed
        if navicon and navicon.startswith('/'):
            navicon = 'https://fosdem.org' + navicon
        
        return {
            'abstract': abstract,
            'description': description,
            'videoLink': video_link,
            'chatLink': chat_link,
            'navicon': navicon
        }
    except Exception as e:
        print(f'  Warning: Could not fetch metadata for {event_link}: {e}')
        return {
            'abstract': None,
            'description': None,
            'videoLink': None,
            'chatLink': None,
            'navicon': None
        }

try:
    events = parse_events_from_html(html)
    
    # Optionally fetch metadata for each event (can be slow for 1000+ events)
    print(f'\nFetching metadata (abstracts/descriptions) for {len(events)} events...')
    print('This may take a while. Press Ctrl+C to skip and use basic data only.')
    
    try:
        for i, event in enumerate(events, 1):
            if i % 10 == 0:
                print(f'  Progress: {i}/{len(events)} events...')
            
            metadata = fetch_event_metadata(event['link'])
            event['abstract'] = metadata['abstract']
            event['description'] = metadata['description']
            event['videoLink'] = metadata['videoLink']
            event['chatLink'] = metadata['chatLink']
            event['navicon'] = metadata['navicon']
    except KeyboardInterrupt:
        print('\n  Interrupted by user. Continuing with available data...')
    except Exception as e:
        print(f'\n  Error fetching metadata: {e}')
        print('  Continuing with basic event data...')
    
    # Save to JSON file with metadata
    from datetime import datetime
    data = {
        'scrapedAt': datetime.now().isoformat(),
        'events': events
    }
    with open('events.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    events_with_abstract = sum(1 for e in events if e.get('abstract'))
    print(f'\nSuccessfully saved {len(events)} events to events.json')
    print(f'  {events_with_abstract} events have abstracts/descriptions')
    print('You can now run: python embed-events.py')
    
except Exception as e:
    print(f'Error parsing data: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
