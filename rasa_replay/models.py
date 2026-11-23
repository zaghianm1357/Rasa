from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any

TIMEFRAME_PRIORITY = {"H1": 0, "M15": 1, "M1": 2}

@dataclass(frozen=True)
class Candle:
    symbol: str
    timeframe: str
    timestamp: datetime  # candle open time, timezone-aware
    open: float
    high: float
    low: float
    close: float
    tick_volume: int = 0
    spread: float = 0.0
    source_row: int = 0

    def validate(self) -> None:
        if self.timeframe not in TIMEFRAME_PRIORITY:
            raise ValueError(f"Unsupported timeframe: {self.timeframe}")
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("Timestamp must include an explicit timezone")
        if not all(map(lambda x: isinstance(x, (int, float)), (self.open, self.high, self.low, self.close))):
            raise ValueError("OHLC values must be numeric")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("Invalid OHLC: high is below another OHLC value")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("Invalid OHLC: low is above another OHLC value")
        if self.tick_volume < 0 or self.spread < 0:
            raise ValueError("tick_volume and spread cannot be negative")

@dataclass(frozen=True)
class MarketEvent:
    event_id: str
    event_type: str
    symbol: str
    timeframe: str
    event_time: datetime
    candle: Candle
    inside_session: bool

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["event_time"] = self.event_time.isoformat()
        d["candle"]["timestamp"] = self.candle.timestamp.isoformat()
        return d
