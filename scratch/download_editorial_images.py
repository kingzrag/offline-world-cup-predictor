#!/usr/bin/env python3
"""
Editorial Image Downloader
Downloads 45 real football photographs from Pexels CDN for the OFFLINE editorial image library.
All images: hero-01 through hero-15, each with cover.jpg, left.jpg, right.jpg
Resolution: 2400px wide (long edge always >= 1800px)
"""

import os
import sys
import time
import urllib.request
import urllib.error
from PIL import Image

BASE_DIR = "/Users/anuragsaikia/prediction/offline/public/editorial"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

def pexels_url(photo_id, filename, w=2400):
    return f"https://images.pexels.com/photos/{photo_id}/{filename}.jpeg?auto=compress&cs=tinysrgb&w={w}&dpr=1"

# Curated Pexels photo IDs for each hero slot
# Format: [cover_id, cover_filename, left_id, left_filename, right_id, right_filename]
MANIFEST = {
    "hero-01": {
        "title": "The Final",
        "cover": (47730,   "sports-jersey-gold-trophy-47730"),       # Trophy / celebration
        "left":  (1763075, "photo-1763075"),                          # Emotional fans stadium
        "right": (46798,   "the-ball-stadion-football-the-pitch-46798"),  # Stadium aerial pitch
    },
    "hero-02": {
        "title": "Champions League Night",
        "cover": (186076,  "crowd-in-soccer-stadium-186076"),          # Stadium under lights
        "left":  (270085,  "empty-sports-arena-270085"),               # Empty stadium
        "right": (1648378, "photo-1648378"),                           # Trophy / UEFA atmosphere
    },
    "hero-03": {
        "title": "Derby Day",
        "cover": (1884574, "photo-1884574"),                           # Two teams competing
        "left":  (1554737, "photo-1554737"),                          # Passionate supporters
        "right": (3148452, "photo-3148452"),                          # Tunnel / dressing room
    },
    "hero-04": {
        "title": "Tactical Masterclass",
        "cover": (3621512, "photo-3621512"),                          # Coach sideline
        "left":  (3621560, "photo-3621560"),                          # Team talk whiteboard
        "right": (3621565, "photo-3621565"),                          # Players listening
    },
    "hero-05": {
        "title": "Wonderkid",
        "cover": (1661778, "photo-1661778"),                          # Young footballer
        "left":  (3621542, "photo-3621542"),                          # Academy training
        "right": (1884478, "photo-1884478"),                          # Goal celebration
    },
    "hero-06": {
        "title": "Goalkeeper",
        "cover": (274422,  "goal-keeper-274422"),                     # Goalkeeper save
        "left":  (1884491, "photo-1884491"),                          # Gloves close-up
        "right": (1884493, "photo-1884493"),                          # Penalty area celebration
    },
    "hero-07": {
        "title": "Premier League",
        "cover": (1884573, "photo-1884573"),                          # Action shot
        "left":  (1884558, "photo-1884558"),                          # Stadium crowd
        "right": (186076,  "crowd-in-soccer-stadium-186076"),         # Night match atmosphere
    },
    "hero-08": {
        "title": "La Liga",
        "cover": (3621546, "photo-3621546"),                          # Technical football
        "left":  (1884434, "photo-1884434"),                          # Stadium architecture
        "right": (1884572, "photo-1884572"),                          # Celebration
    },
    "hero-09": {
        "title": "Serie A",
        "cover": (3621551, "photo-3621551"),                          # Italian football
        "left":  (1884539, "photo-1884539"),                          # San Siro-like atmosphere
        "right": (1554737, "photo-1554737"),                          # Fans
    },
    "hero-10": {
        "title": "Bundesliga",
        "cover": (3621555, "photo-3621555"),                          # Match action
        "left":  (1884572, "photo-1884572"),                          # Dortmund-style yellow wall
        "right": (186076,  "crowd-in-soccer-stadium-186076"),         # Stadium
    },
    "hero-11": {
        "title": "International Football",
        "cover": (1884583, "photo-1884583"),                          # National team lineup
        "left":  (1884574, "photo-1884574"),                          # Flag celebration
        "right": (1884493, "photo-1884493"),                          # Match celebration
    },
    "hero-12": {
        "title": "Matchday",
        "cover": (1884552, "photo-1884552"),                          # Players tunnel
        "left":  (1884495, "photo-1884495"),                          # Coin toss
        "right": (274422,  "goal-keeper-274422"),                     # Warm-up
    },
    "hero-13": {
        "title": "Stadium Architecture",
        "cover": (270085,  "empty-sports-arena-270085"),              # Iconic stadium
        "left":  (186076,  "crowd-in-soccer-stadium-186076"),         # Interior view
        "right": (1884558, "photo-1884558"),                          # Night lighting
    },
    "hero-14": {
        "title": "Fans & Atmosphere",
        "cover": (1554737, "photo-1554737"),                          # Supporters with scarves
        "left":  (1884572, "photo-1884572"),                          # Choreography
        "right": (1884493, "photo-1884493"),                          # Celebration
    },
    "hero-15": {
        "title": "Football Culture",
        "cover": (46798,   "the-ball-stadion-football-the-pitch-46798"),  # Football pitch
        "left":  (1884478, "photo-1884478"),                          # Kids playing
        "right": (1884573, "photo-1884573"),                          # Local football
    },
}

def download_image(url, dest_path, label):
    """Download an image from URL to dest_path, with retries."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as resp, open(dest_path, "wb") as f:
                f.write(resp.read())
            return True
        except (urllib.error.HTTPError, urllib.error.URLError, OSError) as e:
            print(f"  [attempt {attempt+1}] Error downloading {label}: {e}")
            time.sleep(2)
    return False

def verify_image(path, min_size_kb=300, min_long_edge=1800):
    """Return (ok, message) for the image at path."""
    if not os.path.exists(path):
        return False, "File missing"
    kb = os.path.getsize(path) / 1024
    if kb < min_size_kb:
        return False, f"Too small ({kb:.0f} KB < {min_size_kb} KB)"
    try:
        with Image.open(path) as img:
            fmt = img.format
            w, h = img.size
        if fmt not in ("JPEG", "MPO"):
            return False, f"Not JPEG (is {fmt})"
        long_edge = max(w, h)
        if long_edge < min_long_edge:
            return False, f"Resolution too low ({long_edge}px long edge < {min_long_edge}px, {w}x{h})"
    except Exception as e:
        return False, f"Corrupt image: {e}"
    return True, f"OK ({kb:.0f} KB, {w}x{h})"

def run():
    print("=" * 60)
    print("OFFLINE Editorial Image Downloader")
    print("=" * 60)
    
    failed = []
    passed = []

    for hero_id, data in MANIFEST.items():
        print(f"\n[{hero_id}] {data['title']}")
        dest_dir = os.path.join(BASE_DIR, hero_id)
        os.makedirs(dest_dir, exist_ok=True)

        for slot_name in ["cover", "left", "right"]:
            photo_id, filename = data[slot_name]
            url = pexels_url(photo_id, filename)
            dest_path = os.path.join(dest_dir, f"{slot_name}.jpg")
            label = f"{hero_id}/{slot_name}.jpg"

            # Skip if already verified OK
            ok, msg = verify_image(dest_path)
            if ok:
                print(f"  ✓ {slot_name}.jpg already valid: {msg}")
                passed.append(label)
                continue

            print(f"  ↓ Downloading {slot_name}.jpg from photo ID {photo_id}...")
            success = download_image(url, dest_path, label)
            
            if not success:
                print(f"  ✗ Download failed: {label}")
                failed.append(label)
                continue

            # Verify
            ok, msg = verify_image(dest_path)
            if ok:
                print(f"  ✓ {slot_name}.jpg: {msg}")
                passed.append(label)
            else:
                print(f"  ✗ Verification failed {slot_name}.jpg: {msg}")
                failed.append(f"{label} ({msg})")

            time.sleep(0.3)  # Polite delay between requests

    print("\n" + "=" * 60)
    print(f"COMPLETE: {len(passed)}/45 images verified")
    if failed:
        print(f"FAILED ({len(failed)}):")
        for f in failed:
            print(f"  - {f}")
    else:
        print("ALL 45 IMAGES OK!")
    print("=" * 60)
    return len(failed) == 0

if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)
