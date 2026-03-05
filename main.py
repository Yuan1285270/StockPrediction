import argparse
import config
from analyzer import yield_mode
from trigger_engine import event_mode


def parse_args():
    p = argparse.ArgumentParser(
        description="Taiwan stock selector (yfinance-only): estimate next-quarter EPS -> estimate yield, with event-driven trigger."
    )
    p.add_argument(
        "--mode",
        choices=["yield", "event"],
        default="event",
        help="yield: compute for all symbols; event: detect updates and recalc only triggered symbols",
    )
    p.add_argument(
        "--symbols",
        type=str,
        default="",
        help="Optional comma-separated symbols, e.g., 2330.TW,2317.TW",
    )
    p.add_argument("--years", type=int, default=config.YEARS_FOR_PAYOUT, help="Years for payout ratio averaging")
    p.add_argument(
        "--threshold",
        type=float,
        default=config.YIELD_THRESHOLD,
        help="Yield threshold (e.g., 0.06 for 6%%)",
    )
    p.add_argument(
        "--force-all",
        action="store_true",
        help="(event mode) force recalculation for all symbols this run",
    )
    return p.parse_args()


def main():
    args = parse_args()
    symbols = config.SYMBOLS
    if args.symbols.strip():
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    if args.mode == "yield":
        yield_mode(symbols, args.years, args.threshold)
    else:
        event_mode(symbols, args.years, args.threshold, force_recalc_all=args.force_all)


if __name__ == "__main__":
    main()