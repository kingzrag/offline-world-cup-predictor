
import playwright_stealth
import os
context_managers_path = os.path.join(os.path.dirname(playwright_stealth.__file__), 'context_managers.py')
with open(context_managers_path, 'r') as f:
    print(f.read())
