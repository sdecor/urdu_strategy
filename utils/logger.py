import datetime
import os

# --- Helpers ---
def _utc_now_iso() -> str:
    # Python 3.13+: utcnow() est déprécié, on utilise timezone-aware
    return datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")

# --- Logging simple ---
_log_file = None

def set_log_file(path: str):
    global _log_file
    _log_file = path
    # Crée le dossier si inexistant
    os.makedirs(os.path.dirname(path), exist_ok=True)


def log(message: str, enabled: bool = True):
    if not enabled:
        return

    timestamp = _utc_now_iso()
    line = f"{timestamp} {message}"

    # Console
    print(line)

    # Fichier
    if _log_file:
        try:
            with open(_log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:
            print(f"[LOGGER] Erreur écriture log: {e}")
