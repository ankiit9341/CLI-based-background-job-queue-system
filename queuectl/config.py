# queuectl/config.py
import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'queuectl_config.json')

def _load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _write_config(data):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def get_config(key, default=None):
    data = _load_config()
    return data.get(key, default)

def set_config(key, value):
    data = _load_config()
    data[key] = value
    _write_config(data)
