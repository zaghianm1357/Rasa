import unittest
from datetime import datetime, timezone
from rasa_replay.models import Candle
from rasa_replay.engine import ReplayEngine
from rasa_replay.session import is_inside_session

def candle(tf, stamp, row=2):
    return Candle("XAUUSD", tf, datetime.fromisoformat(stamp), 100, 102, 99, 101, 10, 2, row)

class ReplayTests(unittest.TestCase):
    def test_deterministic_timeframe_order(self):
        cs = [
            candle("M1", "2026-11-20T10:00:00+00:00"),
            candle("H1", "2026-11-20T10:00:00+00:00"),
            candle("M15", "2026-11-20T10:00:00+00:00"),
        ]
        ev = ReplayEngine(cs).run()
        self.assertEqual([e.timeframe for e in ev], ["H1", "M15", "M1"])

    def test_no_future_event(self):
        cs = [
            candle("M1", "2026-11-20T10:00:00+00:00"),
            candle("M1", "2026-11-20T10:01:00+00:00", 3),
        ]
        engine = ReplayEngine(cs)
        seen = []
        engine.consumer = lambda e: seen.append((e.event_time, engine.current_time))
        engine.run()
        self.assertTrue(all(event_time == clock for event_time, clock in seen))

    def test_session_boundaries(self):
        self.assertFalse(is_inside_session(datetime.fromisoformat("2026-11-20T03:29:00+00:00"))) # 06:59 Tehran
        self.assertTrue(is_inside_session(datetime.fromisoformat("2026-11-20T03:30:00+00:00")))  # 07:00
        self.assertTrue(is_inside_session(datetime.fromisoformat("2026-11-20T19:29:00+00:00"))) # 22:59
        self.assertFalse(is_inside_session(datetime.fromisoformat("2026-11-20T19:30:00+00:00")))# 23:00

    def test_timezone_required(self):
        c = Candle("XAUUSD", "M1", datetime(2026, 11, 20, 10), 100, 102, 99, 101)
        with self.assertRaises(ValueError):
            c.validate()

if __name__ == "__main__":
    unittest.main()
