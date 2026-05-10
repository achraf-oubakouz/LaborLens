import argparse
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from src.streaming.producer import publish_once


@dataclass
class SourceSchedule:
    source: str
    pages: int
    keyword: str
    interval_seconds: int
    next_run_ts: float = 0


def _now_label() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _run_source(schedule: SourceSchedule) -> None:
    try:
        print(
            f"[{_now_label()}] Running {schedule.source} "
            f"pages={schedule.pages} keyword='{schedule.keyword or 'all'}'"
        )
        publish_once(schedule.source, pages=schedule.pages, keyword=schedule.keyword)
    except Exception as exc:
        print(f"[{_now_label()}] ERROR {schedule.source}: {exc}")
    finally:
        schedule.next_run_ts = time.time() + schedule.interval_seconds


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all streaming producers on local schedules")
    parser.add_argument("--rekrute-pages", type=int, default=1)
    parser.add_argument("--rekrute-keyword", default="python")
    parser.add_argument("--rekrute-interval-seconds", type=int, default=60)
    parser.add_argument("--maroc-annonces-pages", type=int, default=2)
    parser.add_argument("--maroc-annonces-interval-seconds", type=int, default=120)
    parser.add_argument("--include-linkedin", action="store_true")
    parser.add_argument("--linkedin-keyword", default="")
    parser.add_argument("--linkedin-interval-seconds", type=int, default=300)
    args = parser.parse_args()

    schedules = [
        SourceSchedule(
            source="rekrute",
            pages=args.rekrute_pages,
            keyword=args.rekrute_keyword,
            interval_seconds=args.rekrute_interval_seconds,
        ),
        SourceSchedule(
            source="maroc_annonces",
            pages=args.maroc_annonces_pages,
            keyword="",
            interval_seconds=args.maroc_annonces_interval_seconds,
        ),
    ]
    if args.include_linkedin:
        schedules.append(
            SourceSchedule(
                source="linkedin",
                pages=1,
                keyword=args.linkedin_keyword,
                interval_seconds=args.linkedin_interval_seconds,
            )
        )

    print("Starting LaborLens streaming supervisor. Press Ctrl+C to stop.")
    try:
        while True:
            now = time.time()
            for schedule in schedules:
                if now >= schedule.next_run_ts:
                    _run_source(schedule)
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping LaborLens streaming supervisor.")


if __name__ == "__main__":
    main()
