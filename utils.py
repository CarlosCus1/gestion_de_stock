import os
import logging
import json
from datetime import datetime, timedelta
import secrets
import time
from functools import wraps

def format_file_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f}{size_names[i]}"

def rate_limit(limit, per=60):
    def decorator(f):
        calls = []
        @wraps(f)
        def wrapped(*args, **kwargs):
            nonlocal calls
            now = time.time()
            calls = [call for call in calls if call > now - per]
            if len(calls) >= limit:
                logging.warning(f"Rate limit excedido para {f.__name__}")
                return {"error": "Too many requests", "status": 429}, 429
            calls.append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator

class TempURLManager:
    def __init__(self, temp_file):
        self.temp_file = temp_file
        self.urls = {}
        self.load_urls()

    def load_urls(self):
        if os.path.exists(self.temp_file):
            try:
                with open(self.temp_file, 'r') as f:
                    self.urls = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.urls = {}
        else:
            self.urls = {}

    def save_urls(self):
        try:
            os.makedirs(os.path.dirname(self.temp_file), exist_ok=True)
            with open(self.temp_file, 'w') as f:
                json.dump(self.urls, f)
        except IOError as e:
            logging.error(f"Error guardando URLs: {e}")

    def generate_url(self, file_path, duration_minutes=30):
        token = secrets.token_urlsafe(16)
        expiry = datetime.now() + timedelta(minutes=duration_minutes)
        self.urls[token] = {
            "file_path": file_path,
            "expiry": expiry.isoformat()
        }
        self.save_urls()
        return token

    def is_valid_url(self, token):
        if token not in self.urls:
            return False
        expiry = datetime.fromisoformat(self.urls[token]["expiry"])
        if datetime.now() > expiry:
            del self.urls[token]
            self.save_urls()
            return False
        return True

    def get_file_path(self, token):
        return self.urls[token]["file_path"] if self.is_valid_url(token) else None
