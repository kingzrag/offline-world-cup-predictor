#!/usr/bin/env python3
import os
import sys
import time
import json
import urllib.request
import urllib.parse
import io
from PIL import Image

BASE_DIR = "/Users/anuragsaikia/prediction/offline/public/editorial"
HEADERS = {'User-Agent': 'OFFLINE-EditorialBot/1.0 (https://offline.app; bot@offline.app) Python/3.10'}

# Missing slots and broader/alternative queries
MISSING_TARGETS = {
    ("hero-03", "cover"): [
        "association football tackle",
        "soccer match tackle",
        "football tackle action",
        "association football match"
    ],
    ("hero-03", "left"): [
        "football supporters flags",
        "soccer fans crowd",
        "football fans cheering",
        "supporters stadium flags"
    ],
    ("hero-04", "cover"): [
        "football manager",
        "soccer coach",
        "football coach",
        "coach sideline"
    ],
    ("hero-05", "cover"): [
        "young football player dribbling",
        "youth football player",
        "young soccer player",
        "dribbling football"
    ],
    ("hero-06", "left"): [
        "goalkeeper gloves",
        "goalkeeper training",
        "soccer goalkeeper gloves",
        "goalie gloves"
    ],
    ("hero-08", "cover"): [
        "La Liga match",
        "Real Madrid match",
        "FC Barcelona match",
        "Spanish football match"
    ],
    ("hero-12", "cover"): [
        "football players tunnel",
        "players tunnel stadium",
        "football tunnel",
        "stadium tunnel walkout"
    ],
    ("hero-13", "cover"): [
        "football stadium exterior",
        "soccer stadium exterior",
        "stadium architecture exterior",
        "stadium facade"
    ],
    ("hero-13", "right"): [
        "stadium night exterior",
        "football stadium night exterior",
        "soccer stadium night lights",
        "stadium night illuminated"
    ],
    ("hero-14", "cover"): [
        "football fans scarves",
        "soccer fans scarves",
        "supporters scarves",
        "football fans cheering scarves"
    ],
    ("hero-15", "cover"): [
        "street football",
        "street soccer",
        "cage football",
        "urban football pitch"
    ],
    # Let's replace hero-01/right to guarantee a real soccer stadium aerial
    ("hero-01", "right"): [
        "stadium aerial view association football",
        "soccer stadium aerial view",
        "football stadium aerial",
        "Wembley stadium aerial"
    ]
}

used_titles = set()

def verify_image(path):
    if not os.path.exists(path):
        return False
    try:
        with Image.open(path) as img:
            w, h = img.size
            fmt = img.format
            kb = os.path.getsize(path) / 1024
            if fmt in ('JPEG', 'MPO') and kb >= 300 and max(w, h) >= 1800:
                return True
    except:
        pass
    return False

def search_wikimedia(query, limit=20):
    url = f"https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query + ' filetype:jpg')}&srnamespace=6&srlimit={limit}&format=json"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return [item['title'] for item in data.get('query', {}).get('search', [])]
    except Exception as e:
        print(f"Search error for '{query}': {e}")
        return []

def get_image_info(title):
    encoded = urllib.parse.quote(title)
    url = f"https://commons.wikimedia.org/w/api.php?action=query&titles={encoded}&prop=imageinfo&iiprop=url|size&iiurlwidth=2560&format=json"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            pages = data.get('query', {}).get('pages', {})
            for pid, page in pages.items():
                if 'imageinfo' in page:
                    ii = page['imageinfo'][0]
                    thumburl = ii.get('thumburl')
                    origurl = ii.get('url')
                    orig_w = ii.get('width', 0)
                    orig_h = ii.get('height', 0)
                    return thumburl if thumburl else origurl, orig_w, orig_h
    except Exception:
        pass
    return None, 0, 0

def fetch_and_save(url, dest_path):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
            if not data.startswith(b'\xff\xd8'):
                return False
            with Image.open(io.BytesIO(data)) as img:
                w, h = img.size
                if max(w, h) < 1800 or len(data) / 1024 < 300:
                    return False
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, 'wb') as f:
                f.write(data)
            return True
    except:
        return False

def main():
    print("Fetching missing / replacement editorial images...")
    
    for (hero_id, slot_name), queries in MISSING_TARGETS.items():
        slot_file = f"{slot_name}.jpg"
        dest_path = os.path.join(BASE_DIR, hero_id, slot_file)
        rel_name = f"{hero_id}/{slot_file}"
        
        # For hero-01/right, we want to replace it to make sure it's a real soccer stadium, so we overwrite it
        if hero_id != "hero-01" or slot_name != "right":
            if verify_image(dest_path):
                print(f"Skipping {rel_name} (already valid)")
                continue
        
        print(f"\nProcessing {rel_name}...")
        success = False
        for query in queries:
            if success:
                break
            print(f"  Searching: '{query}'")
            titles = search_wikimedia(query)
            time.sleep(0.5)
            
            for title in titles:
                if title in used_titles:
                    continue
                if not title.lower().endswith(('.jpg', '.jpeg')):
                    continue
                # Skip non-soccer / american football tags
                t_lower = title.lower()
                if 'american_football' in t_lower or 'nfl' in t_lower or 'rugby' in t_lower or 'afl' in t_lower:
                    continue
                
                dl_url, orig_w, orig_h = get_image_info(title)
                time.sleep(0.3)
                
                if not dl_url or max(orig_w, orig_h) < 1800:
                    continue
                
                if fetch_and_save(dl_url, dest_path):
                    print(f"  ✓ Saved {rel_name} from: {title}")
                    used_titles.add(title)
                    success = True
                    break
        
        if not success:
            print(f"  ✗ Failed to find image for {rel_name}")
            
    # Print status report
    valid_count = 0
    for hero_num in range(1, 16):
        h_id = f"hero-{hero_num:02d}"
        for slot in ["cover.jpg", "left.jpg", "right.jpg"]:
            path = os.path.join(BASE_DIR, h_id, slot)
            if verify_image(path):
                valid_count += 1
            else:
                print(f"STILL INVALID/MISSING: {h_id}/{slot}")
    print(f"\nFinal count: {valid_count}/45 valid images")

if __name__ == "__main__":
    main()
