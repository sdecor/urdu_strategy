import argparse
import json
import os
from datetime import datetime
from pathlib import Path
import shutil
import yaml

def load_settings():
    root = Path(__file__).resolve().parents[1]
    settings_path = os.environ.get("SETTINGS_PATH", str(root / "config" / "settings.yaml"))
    if not Path(settings_path).exists():
        return {
            "paths": {
                "csv_input": str(root / "data" / "input" / "signals.csv"),
                "archive_dir": str(root / "data" / "archive"),
                "state": {
                    "trade_state": str(root / "state" / "trade_state.json"),
                    "offset": str(root / "state" / "offsets" / "signals.offset"),
                },
            }
        }
    with open(settings_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

def write_json(path: Path, data):
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def write_text(path: Path, text: str):
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def archive_file(src: Path, dst_dir: Path):
    dst_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = dst_dir / f"{src.stem}_{ts}{src.suffix}"
    shutil.move(str(src), str(dst))
    return dst

def main():
    s = load_settings()
    trade_state_path = Path(s["paths"]["state"]["trade_state"])
    offset_path = Path(s["paths"]["state"]["offset"])
    signals_path = Path(s["paths"]["csv_input"])
    archive_dir = Path(s["paths"]["archive_dir"])

    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-signals", action="store_true")
    parser.add_argument("--clear-signals", action="store_true")
    args = parser.parse_args()

    write_json(trade_state_path, {"positions": {}, "pnl_day": 0.0, "last_reset": datetime.now().isoformat()})
    write_text(offset_path, "0")

    if args.archive_signals and signals_path.exists():
        archive_file(signals_path, archive_dir)
        ensure_parent(signals_path)
        write_text(signals_path, "")
    elif args.clear_signals:
        ensure_parent(signals_path)
        write_text(signals_path, "")

if __name__ == "__main__":
    main()
