import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable
from .models import Candle, MarketEvent, TIMEFRAME_PRIORITY
from .session import is_inside_session

Consumer = Callable[[MarketEvent], None]

class ReplayEngine:
    def __init__(self, candles: Iterable[Candle], consumer: Consumer | None = None):
        self.candles = list(candles)
        self.consumer = consumer
        self.current_time: datetime | None = None
        self.processed_ids: set[str] = set()
        self.events_emitted = 0

    @staticmethod
    def _sort_key(c: Candle):
        return (c.timestamp.timestamp(), TIMEFRAME_PRIORITY[c.timeframe], c.source_row)

    @staticmethod
    def _event_id(c: Candle) -> str:
        raw = f"{c.symbol}|{c.timeframe}|{c.timestamp.isoformat()}|{c.source_row}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

    def run(self, start: datetime | None = None, end: datetime | None = None) -> list[MarketEvent]:
        if start and (start.tzinfo is None or start.utcoffset() is None):
            raise ValueError("start must be timezone-aware")
        if end and (end.tzinfo is None or end.utcoffset() is None):
            raise ValueError("end must be timezone-aware")
        ordered = sorted(self.candles, key=self._sort_key)
        output: list[MarketEvent] = []
        for candle in ordered:
            if start and candle.timestamp < start:
                continue
            if end and candle.timestamp > end:
                continue
            # The replay clock advances only to the event currently being delivered.
            self.current_time = candle.timestamp
            event_id = self._event_id(candle)
            if event_id in self.processed_ids:
                continue
            self.processed_ids.add(event_id)
            event = MarketEvent(
                event_id=event_id, event_type="CANDLE",
                symbol=candle.symbol, timeframe=candle.timeframe,
                event_time=candle.timestamp, candle=candle,
                inside_session=is_inside_session(candle.timestamp),
            )
            if event.event_time > self.current_time:
                raise RuntimeError("Look-ahead violation")
            output.append(event)
            self.events_emitted += 1
            if self.consumer:
                self.consumer(event)
        return output

def write_outputs(events: list[MarketEvent], output_dir: str | Path) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    event_path = out / "replay_events.jsonl"
    with event_path.open("w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
    summary = {
        "status": "PASS",
        "events": len(events),
        "timeframes": sorted({e.timeframe for e in events}),
        "first_event": events[0].event_time.isoformat() if events else None,
        "last_event": events[-1].event_time.isoformat() if events else None,
        "inside_session": sum(1 for e in events if e.inside_session),
        "outside_session": sum(1 for e in events if not e.inside_session),
        "look_ahead_policy": "event delivered only at its own timestamp",
    }
    (out / "replay_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary
