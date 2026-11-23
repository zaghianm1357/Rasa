import csv
from datetime import datetime
from pathlib import Path
from .models import Candle

REQUIRED = {"timestamp", "open", "high", "low", "close"}

def load_candles(path: str | Path, timeframe: str, symbol: str = "XAUUSD") -> list[Candle]:
    path = Path(path)
    rows: list[Candle] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        missing = REQUIRED - fields
        if missing:
            raise ValueError(f"{path}: missing columns: {', '.join(sorted(missing))}")
        previous = None
        for line_no, row in enumerate(reader, start=2):
            raw_ts = (row.get("timestamp") or "").strip()
            try:
                ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
            except Exception as exc:
                raise ValueError(f"{path}:{line_no}: invalid timestamp {raw_ts!r}") from exc
            if ts.tzinfo is None or ts.utcoffset() is None:
                raise ValueError(f"{path}:{line_no}: timestamp has no timezone; do not guess it")
            if previous is not None and ts <= previous:
                raise ValueError(f"{path}:{line_no}: timestamps are not strictly increasing")
            previous = ts
            c = Candle(
                symbol=symbol, timeframe=timeframe, timestamp=ts,
                open=float(row["open"]), high=float(row["high"]),
                low=float(row["low"]), close=float(row["close"]),
                tick_volume=int(float(row.get("tick_volume") or 0)),
                spread=float(row.get("spread") or 0),
                source_row=line_no,
            )
            c.validate()
            rows.append(c)
    return rows
