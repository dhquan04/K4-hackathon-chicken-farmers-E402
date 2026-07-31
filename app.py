"""
Root entrypoint delegating to project/codebase/app.py
"""
import os
import sys

# Ensure project codebase is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CODEBASE_DIR = os.path.join(BASE_DIR, "project", "codebase")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if CODEBASE_DIR not in sys.path:
    sys.path.insert(0, CODEBASE_DIR)

# Import and execute app script
app_path = os.path.join(CODEBASE_DIR, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    code = f.read()

exec(compile(code, app_path, 'exec'))
