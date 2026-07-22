import os
import sys
from PIL import Image

EDITORIAL_DIR = "/Users/anuragsaikia/prediction/offline/public/editorial"

def verify_images():
    errors = []
    success_count = 0
    
    for i in range(1, 16):
        hero_id = f"hero-{i:02d}"
        hero_path = os.path.join(EDITORIAL_DIR, hero_id)
        if not os.path.exists(hero_path):
            errors.append(f"Directory missing: {hero_path}")
            continue
            
        for img_name in ["cover.jpg", "left.jpg", "right.jpg"]:
            img_path = os.path.join(hero_path, img_name)
            if not os.path.exists(img_path):
                errors.append(f"Missing: {hero_id}/{img_name}")
                continue
                
            size = os.path.getsize(img_path)
            if size < 300 * 1024:
                errors.append(f"File size too small ({size / 1024:.1f} KB < 300 KB): {hero_id}/{img_name}")
                
            try:
                with Image.open(img_path) as img:
                    if img.format not in ["JPEG", "MPO"]:
                        errors.append(f"Not a JPEG ({img.format}): {hero_id}/{img_name}")
                    w, h = img.size
                    long_edge = max(w, h)
                    if long_edge < 1800:
                        errors.append(f"Resolution too small (long edge {long_edge}px < 1800px, size {w}x{h}): {hero_id}/{img_name}")
                    else:
                        success_count += 1
            except Exception as e:
                errors.append(f"Corrupt/Invalid image file: {hero_id}/{img_name} - {str(e)}")

    print(f"Verified {success_count} / 45 images.")
    if errors:
        print("ERRORS FOUND:")
        for err in errors:
            print(" -", err)
        return False
    else:
        print("ALL 45 IMAGES VERIFIED SUCCESSFULLY!")
        return True

if __name__ == "__main__":
    verify_images()
