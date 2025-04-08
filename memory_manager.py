
import json
from pathlib import Path
from datetime import datetime

MEMORY_FILE = Path("analysis_memory.json")

def load_memory():
    if MEMORY_FILE.exists():
        with MEMORY_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_memory(memory):
    with MEMORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def add_analysis(user_id, input_text, response_text):
    memory = load_memory()
    user_key = str(user_id)

    if user_key not in memory:
        memory[user_key] = []

    memory[user_key].append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "input": input_text,
        "response": response_text
    })

    save_memory(memory)

def delete_user_memory(user_id):
    memory = load_memory()
    user_key = str(user_id)
    if user_key in memory:
        del memory[user_key]
        save_memory(memory)
        return True
    return False
