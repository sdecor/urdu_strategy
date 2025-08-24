import datetime

LOG_FILE = "urdu_bot.log"

def set_log_file(path: str):
    global LOG_FILE
    LOG_FILE = path

def _write_to_file(message: str):
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def log(message: str, enabled: bool = True):
    if enabled:
        print(message)
    _write_to_file(message)
