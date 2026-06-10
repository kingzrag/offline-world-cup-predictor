import sys

try:
    import requests
    print("✓ requests is successfully installed (version: " + requests.__version__ + ")")
except ImportError as e:
    print("✗ requests is NOT installed:", e)

try:
    import bs4
    print("✓ beautifulsoup4 (bs4) is successfully installed (version: " + bs4.__version__ + ")")
except ImportError as e:
    print("✗ beautifulsoup4 (bs4) is NOT installed:", e)

try:
    import lxml
    print("✓ lxml is successfully installed")
except ImportError as e:
    print("✗ lxml is NOT installed:", e)

try:
    import requests
    import bs4
    import lxml
    print("\nSUCCESS: All dependencies are available and imported correctly!")
    sys.exit(0)
except ImportError:
    print("\nFAILURE: Some dependencies are missing!")
    sys.exit(1)
