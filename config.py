import os
import sys
import json

# Check if running as a compiled .exe via PyInstaller
if getattr(sys, 'frozen', False):
    APPLICATION_PATH = os.path.dirname(sys.executable)
else:
    # If running as a standard Python script
    APPLICATION_PATH = os.path.dirname(os.path.abspath(__file__))

# Combine folder path with JSON filename
CONFIG_FILE = os.path.join(APPLICATION_PATH, "macropad-m33.json")

VID = 0x4b59 
PID = 0x0000
USAGE_PAGE = 0xFF60
USAGE = 0x61

def load_config():
    """Load JSON config or create default if not exists."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
            
    # Default configuration
    default = {str(i): [""]*8 for i in range(1, 7)}
    default["autostart"] = False
    return default

def save_config(data):
    """Save dictionary to JSON file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)
