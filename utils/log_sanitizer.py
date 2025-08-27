# utils/log_sanitizer.py
from copy import deepcopy

REDACTION = "…redacted…"

def _mask_token(token: str, keep_start: int = 6, keep_end: int = 6) -> str:
    """
    Masque un token en conservant quelques caractères en tête/queue.
    Ex: 'Bearer abcdef...xyz' -> 'Bearer abcdef…redacted…xyz'
    """
    if not isinstance(token, str):
        return REDACTION

    parts = token.split(None, 1)  # ex: ["Bearer", "xxxxx"]
    if len(parts) == 2 and parts[0].lower() == "bearer":
        t = parts[1]
        if len(t) <= keep_start + keep_end:
            return f"{parts[0]} {REDACTION}"
        return f"{parts[0]} {t[:keep_start]}{REDACTION}{t[-keep_end:]}"
    # Pas un bearer; on masque tout de même
    if len(token) <= keep_start + keep_end:
        return REDACTION
    return f"{token[:keep_start]}{REDACTION}{token[-keep_end:]}"


def sanitize_headers(headers: dict) -> dict:
    """
    Retourne une copie des headers avec Authorization (et autres sensibles) masqués.
    """
    if not isinstance(headers, dict):
        return {}

    safe = deepcopy(headers)
    for key in list(safe.keys()):
        k = key.lower()
        if k in ("authorization", "x-api-key", "api-key"):
            safe[key] = _mask_token(str(safe[key]))
        if k in ("cookie", "set-cookie"):
            safe[key] = REDACTION
    return safe


def sanitize_payload(payload: dict) -> dict:
    """
    Nettoie un payload avant log (aucun champ sensible connu ici pour TopstepX).
    """
    if not isinstance(payload, dict):
        return {}
    return deepcopy(payload)


def safe_log_api_call(method: str, url: str, headers: dict, payload: dict, logger_fn, logging_enabled: bool, prefix: str = ""):
    """
    Utilitaire centralisé pour logguer une requête API sans fuite de secrets.
    """
    if not logging_enabled:
        return
    from utils.logger import log as default_log  # évite import circulaire si utilisé ailleurs
    log_fn = logger_fn or default_log
    from utils.log_sanitizer import sanitize_headers, sanitize_payload  # idempotent

    sh = sanitize_headers(headers)
    sp = sanitize_payload(payload)
    pfx = f"{prefix.strip()} " if prefix else ""
    log_fn(f"{pfx}[API] {method.upper()} {url}", True)
    log_fn(f"{pfx}[API] Headers: {sh}", True)
    if sp:
        log_fn(f"{pfx}[API] Payload: {sp}", True)
