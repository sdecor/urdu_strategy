import argparse
import os
import time
from pathlib import Path
import yaml

def load_settings():
    root = Path(__file__).resolve().parents[1]
    settings_path = os.environ.get("SETTINGS_PATH", str(root / "config" / "settings.yaml"))
    if not Path(settings_path).exists():
        return {
            "paths": {"csv_input": str(root / "data" / "input" / "signals.csv")},
            "csv_reader": {"delimiter": ",", "has_header": False, "schema": ["instrument", "action"]},
            "polling": {"interval_ms": 500},
        }
    with open(settings_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

def write_signal(target: Path, delimiter: str, instrument: str, action: str):
    ensure_parent(target)
    with open(target, "a", encoding="utf-8", newline="") as f:
        f.write(f"{instrument}{delimiter}{action}\n")

def main():
    s = load_settings()
    delimiter = s.get("csv_reader", {}).get("delimiter", ",")
    target = Path(s.get("paths", {}).get("csv_input"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--instrument", "-i", required=True)
    parser.add_argument("--action", "-a", required=True, choices=["long", "buy", "short", "sell", "exit", "LONG", "SHORT", "EXIT"])
    parser.add_argument("--count", "-c", type=int, default=1)
    parser.add_argument("--interval-ms", "-t", type=int, default=0)
    args = parser.parse_args()
    for _ in range(args.count):
        write_signal(target, delimiter, args.instrument, args.action)
        if args.interval_ms > 0:
            time.sleep(args.interval_ms / 1000.0)

if __name__ == "__main__":
    main()
