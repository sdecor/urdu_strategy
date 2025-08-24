from utils.logger import log


class BusinessError(Exception):
    """Erreur métier retournée par l’API (success:false)."""


def assert_business_success(resp_json: dict | None, tag: str, logging_enabled: bool):
    """
    L’API peut renvoyer 200 mais avec success:false. On homogénéise ici.
    """
    if resp_json is None:
        return
    if isinstance(resp_json, dict) and resp_json.get("success") is False:
        code = resp_json.get("errorCode", "N/A")
        msg = resp_json.get("errorMessage", "N/A")
        log(f"{tag} ERREUR MÉTIER: success=false, code={code}, message='{msg}'", logging_enabled)
        raise BusinessError(f"{code}: {msg}")
