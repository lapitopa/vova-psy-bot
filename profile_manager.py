
import json
from pathlib import Path

PROFILE_FILE = Path("user_profiles.json")

def load_profiles():
    if PROFILE_FILE.exists():
        with PROFILE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_profiles(profiles):
    with PROFILE_FILE.open("w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)
