import argparse
from datetime import datetime
from pathlib import Path
from .csv_loader import load_candles
from .engine import ReplayEngine, write_outputs

def parse_dt(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None

def main():
    p = argparse.ArgumentParser(description="RASA historical replay foundation")
    p.add_argument("--h1", required=True)
    p.add_argument("--m15", required=True)
    p.add_argument("--m1", required=True)
    p.add_argument("--symbol", default="XAUUSD")
    p.add_argument("--start")
    p.add_argument("--end")
    p.add_argument("--output", default="output")
    args = p.parse_args()

    candles = []
    for tf, path in (("H1", args.h1), ("M15", args.m15), ("M1", args.m1)):
        loaded = load_candles(path, tf, args.symbol)
        print(f"{tf}: loaded {len(loaded)} candles")
        candles.extend(loaded)

    engine = ReplayEngine(candles)
    events = engine.run(parse_dt(args.start), parse_dt(args.end))
    summary = write_outputs(events, Path(args.output))
    print("\nReplay completed")
    for key, value in summary.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()
