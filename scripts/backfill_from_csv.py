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
            "csv_reader": {"delimiter": ","},
        }
    with open(settings_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

def append_line(target: Path, line: str):
    ensure_parent(target)
    with open(target, "a", encoding="utf-8", newline="") as f:
        f.write(line if line.endswith("\n") else line + "\n")

def main():
    s = load_settings()
    target = Path(s.get("paths", {}).get("csv_input"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", "-s", required=True)
    parser.add_argument("--interval-ms", "-t", type=int, default=0)
    parser.add_argument("--limit", "-n", type=int, default=0)
    parser.add_argument("--skip", "-k", type=int, default=0)
    args = parser.parse_args()

    src = Path(args.source)
    if not src.exists():
        raise SystemExit(f"Missing source: {src}")

    count = 0
    with open(src, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx < args.skip:
                continue
            ln = line.strip()
            if not ln:
                continue
            append_line(target, ln)
            count += 1
            if args.limit and count >= args.limit:
                break
            if args.interval_ms > 0:
                time.sleep(args.interval_ms / 1000.0)

if __name__ == "__main__":
    main()
