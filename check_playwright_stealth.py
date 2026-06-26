
import playwright_stealth
print("Contents of playwright_stealth package:")
import os
print(os.listdir(os.path.dirname(playwright_stealth.__file__)))

print("\nTrying to import stealth_async and stealth_sync:")
try:
    from playwright_stealth import stealth_async
    print("✓ stealth_async imported successfully!")
except ImportError as e:
    print(f"✗ stealth_async import failed: {e}")

try:
    from playwright_stealth import stealth_sync
    print("✓ stealth_sync imported successfully!")
except ImportError as e:
    print(f"✗ stealth_sync import failed: {e}")

print("\nChecking playwright_stealth.stealth module:")
import playwright_stealth.stealth
print(dir(playwright_stealth.stealth))
