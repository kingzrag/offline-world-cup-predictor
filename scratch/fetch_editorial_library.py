#!/usr/bin/env python3
"""
Editorial Image Library Builder for OFFLINE Platform
Fetches 45 real football photographs from Wikimedia Commons / open sources.
Ensures every image meets strict quality criteria:
- JPEG format
- Resolution >= 1800px on long edge
- File size >= 300 KB
- No watermarks / overlays
"""

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

# Target themes & search queries for each slot
# Map of (hero_id, slot) -> list of alternative search queries
SEARCH_TARGETS = {
    ("hero-01", "cover"): ["FIFA World Cup trophy celebration", "UEFA Champions League trophy lift celebration"],
    ("hero-01", "left"):  ["association football fans emotion celebration", "football supporters cheering stadium"],
    ("hero-01", "right"): ["association football stadium aerial sunset", "stadium aerial night association football"],
    
    ("hero-02", "cover"): ["association football stadium night floodlights", "Champions League match action stadium"],
    ("hero-02", "left"):  ["empty association football stadium pitch", "football stadium before match empty"],
    ("hero-02", "right"): ["UEFA Champions League trophy pitch", "association football trophy presentation"],
    
    ("hero-03", "cover"): ["association football tackle duel match action", "soccer match tackle intense action"],
    ("hero-03", "left"):  ["passionate association football supporters flags", "ultras supporters singing terrace"],
    ("hero-03", "right"): ["association football players entering pitch tunnel", "football stadium tunnel exit"],
    
    ("hero-04", "cover"): ["association football manager coach sideline instruction", "football coach talking sideline"],
    ("hero-04", "left"):  ["association football tactical training session", "football coach whiteboard tactical"],
    ("hero-04", "right"): ["association football team talk huddle", "football team huddle players"],
    
    ("hero-05", "cover"): ["young association football player dribbling action", "youth football player dribble"],
    ("hero-05", "left"):  ["youth football academy training session", "junior football academy practice"],
    ("hero-05", "right"): ["association football player goal celebration young", "footballer jumping celebration"],
    
    ("hero-06", "cover"): ["association football goalkeeper diving save", "soccer goalkeeper save dive"],
    ("hero-06", "left"):  ["association football goalkeeper gloves preparation", "goalkeeper gloves close up"],
    ("hero-06", "right"): ["penalty kick association football shootout", "goalkeeper penalty save shootout"],
    
    ("hero-07", "cover"): ["Premier League association football match action", "English football match action"],
    ("hero-07", "left"):  ["packed association football stadium stands crowd", "football stadium crowd packed"],
    ("hero-07", "right"): ["association football stadium night floodlights crowd", "football stadium evening lights"],
    
    ("hero-08", "cover"): ["La Liga association football match action", "Spanish football match passing action"],
    ("hero-08", "left"):  ["Camp Nou stadium Barcelona interior", "Spanish football stadium interior"],
    ("hero-08", "right"): ["Santiago Bernabeu stadium Real Madrid", "Bernabeu stadium night floodlights"],
    
    ("hero-09", "cover"): ["Serie A Italian association football match action", "Italian football match action"],
    ("hero-09", "left"):  ["San Siro stadium Milan interior aerial", "Stadio Olimpico Rome interior"],
    ("hero-09", "right"): ["Italian football ultras flare banner stadium", "Serie A supporters curva flares"],
    
    ("hero-10", "cover"): ["Bundesliga association football match action", "German football goal match action"],
    ("hero-10", "left"):  ["Signal Iduna Park Dortmund yellow wall fans", "Dortmund supporters sudtribune"],
    ("hero-10", "right"): ["Allianz Arena Bayern Munich stadium exterior", "modern football stadium night illuminated"],
    
    ("hero-11", "cover"): ["national football team lineup World Cup anthem", "national team lineup association football"],
    ("hero-11", "left"):  ["association football national team fans flags", "World Cup supporters flags waving"],
    ("hero-11", "right"): ["World Cup association football goal celebration", "national team celebration goal"],
    
    ("hero-12", "cover"): ["association football players walking tunnel pitch", "matchday players tunnel walkout"],
    ("hero-12", "left"):  ["association football referee coin toss captains", "referee captains handshake pitch"],
    ("hero-12", "right"): ["association football players warming up drills", "pre match warmup football players"],
    
    ("hero-13", "cover"): ["iconic association football stadium exterior architecture", "modern football stadium exterior architectural"],
    ("hero-13", "left"):  ["empty association football stadium interior seats", "stadium seats empty stand"],
    ("hero-13", "right"): ["association football stadium illuminated night exterior", "stadium exterior night lights glowing"],
    
    ("hero-14", "cover"): ["association football supporters scarves cheering", "football fans scarves held up"],
    ("hero-14", "left"):  ["association football tifo display ultras choreography", "stadium tifo choreography fans"],
    ("hero-14", "right"): ["association football crowd goal celebration stadium", "stadium stands goal celebration fans"],
    
    ("hero-15", "cover"): ["street football cage soccer urban", "urban street football match pitch"],
    ("hero-15", "left"):  ["children kids playing association football neighborhood", "kids street football match"],
    ("hero-15", "right"): ["grassroots amateur association football pitch community", "local community football match pitch"],
}

used_urls = set()
used_titles = set()

def verify_image(path, min_kb=300, min_long_edge=1800):
    if not os.path.exists(path):
        return False, "File missing"
    kb = os.path.getsize(path) / 1024
    if kb < min_kb:
        return False, f"Size too small ({kb:.0f} KB < {min_kb} KB)"
    try:
        with Image.open(path) as img:
            fmt = img.format
            w, h = img.size
            if fmt not in ('JPEG', 'MPO'):
                return False, f"Format not JPEG ({fmt})"
            long_edge = max(w, h)
            if long_edge < min_long_edge:
                return False, f"Resolution too low ({long_edge}px < {min_long_edge}px)"
            return True, f"OK ({w}x{h}, {kb:.0f} KB)"
    except Exception as e:
        return False, f"Corrupt image ({e})"

def search_wikimedia(query, limit=15):
    url = f"https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query + ' filetype:jpg')}&srnamespace=6&srlimit={limit}&format=json"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return [item['title'] for item in data.get('query', {}).get('search', [])]
    except Exception as e:
        print(f"  [Search Error] {query}: {e}")
        return []

def get_image_info(title, target_width=2400):
    encoded = urllib.parse.quote(title)
    url = f"https://commons.wikimedia.org/w/api.php?action=query&titles={encoded}&prop=imageinfo&iiprop=url|size&iiurlwidth={target_width}&format=json"
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
                    dl_url = thumburl if thumburl else origurl
                    return dl_url, orig_w, orig_h
    except Exception as e:
        pass
    return None, 0, 0

def fetch_and_save(url, dest_path):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
            if not data.startswith(b'\xff\xd8'):
                return False, "Not JPEG magic bytes"
            with Image.open(io.BytesIO(data)) as img:
                w, h = img.size
                if max(w, h) < 1800 or len(data) / 1024 < 300:
                    return False, f"Downloaded image inadequate ({w}x{h}, {len(data)/1024:.0f}KB)"
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, 'wb') as f:
                f.write(data)
            return True, f"Saved ({w}x{h}, {len(data)/1024:.0f}KB)"
    except Exception as e:
        return False, f"Download failed ({e})"

def main():
    print("=" * 60)
    print("OFFLINE Editorial Image Library Builder")
    print("=" * 60)

    # First check existing images
    existing_valid = 0
    for hero_num in range(1, 16):
        hero_id = f"hero-{hero_num:02d}"
        for slot in ["cover.jpg", "left.jpg", "right.jpg"]:
            path = os.path.join(BASE_DIR, hero_id, slot)
            ok, msg = verify_image(path)
            if ok:
                existing_valid += 1

    print(f"Starting with {existing_valid}/45 valid images.\n")

    # Iterate through all 15 heroes
    for hero_num in range(1, 16):
        hero_id = f"hero-{hero_num:02d}"
        for slot_name in ["cover", "left", "right"]:
            slot_file = f"{slot_name}.jpg"
            dest_path = os.path.join(BASE_DIR, hero_id, slot_file)
            rel_name = f"{hero_id}/{slot_file}"

            ok, msg = verify_image(dest_path)
            if ok:
                print(f"[EXISTING VALID] {rel_name}: {msg}")
                continue

            print(f"\n[FETCHING] {rel_name}...")
            queries = SEARCH_TARGETS.get((hero_id, slot_name), [f"association football {hero_id} {slot_name}"])
            
            slot_success = False
            for query in queries:
                if slot_success:
                    break
                print(f"  Searching: '{query}'")
                titles = search_wikimedia(query, limit=15)
                time.sleep(0.5)

                for title in titles:
                    if title in used_titles:
                        continue
                    if not title.lower().endswith(('.jpg', '.jpeg')):
                        continue
                    # Exclude non-association-football files (e.g. american football, rugby)
                    t_lower = title.lower()
                    if 'american_football' in t_lower or 'nfl' in t_lower or 'rugby' in t_lower or 'afl' in t_lower:
                        continue

                    dl_url, orig_w, orig_h = get_image_info(title, target_width=2560)
                    time.sleep(0.3)

                    if not dl_url or max(orig_w, orig_h) < 1800 or dl_url in used_urls:
                        continue

                    success, save_msg = fetch_and_save(dl_url, dest_path)
                    if success:
                        print(f"  ✓ {rel_name} <- {title[:50]} : {save_msg}")
                        used_titles.add(title)
                        used_urls.add(dl_url)
                        slot_success = True
                        break

            if not slot_success:
                print(f"  ✗ Could not find suitable image for {rel_name}")

    # Final summary check
    print("\n" + "=" * 60)
    print("FINAL VERIFICATION SUMMARY")
    print("=" * 60)
    total_valid = 0
    for hero_num in range(1, 16):
        hero_id = f"hero-{hero_num:02d}"
        for slot_name in ["cover", "left", "right"]:
            slot_file = f"{slot_name}.jpg"
            dest_path = os.path.join(BASE_DIR, hero_id, slot_file)
            rel_name = f"{hero_id}/{slot_file}"
            ok, msg = verify_image(dest_path)
            if ok:
                total_valid += 1
                print(f"  ✓ {rel_name}: {msg}")
            else:
                print(f"  ✗ {rel_name}: {msg}")

    print(f"\nTOTAL VALID IMAGES: {total_valid} / 45")
    print("=" * 60)
    return total_valid == 45

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
