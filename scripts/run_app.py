#!/usr/bin/env python
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# Charge .env minimal (TOPSTEPX_API_KEY, SETTINGS_PATH)
env_path = ROOT / ".env"
if env_path.exists():
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("'").strip('"'))
    except Exception:
        pass

# Assure l'import du paquet depuis src/
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Lance l'app du paquet
import urdu_exec_bot.app as app  # noqa: E402

if hasattr(app, "main") and callable(getattr(app, "main")):
    sys.exit(app.main() or 0)
elif hasattr(app, "run") and callable(getattr(app, "run")):
    sys.exit(app.run() or 0)
else:
    # Fallback: importer suffit si l'app s'exécute au module import
    sys.exit(0)
