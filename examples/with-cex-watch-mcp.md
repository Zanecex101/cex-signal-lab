# Driving cex-signal-lab from cex-watch-mcp data

[`cex-watch-mcp`](https://github.com/Zanecex101/cex-watch-mcp) commits
a daily snapshot of every active spot pair on Binance / OKX / Bybit /
Coinbase / Kraken into its `data/` directory. We can use that as a
**dynamic universe filter** for the lab — no manual coin-list curation.

## What you get

- Drop coins that aren't listed on Binance Futures *and* at least one
  spot exchange (i.e. illiquid Binance-only listings)
- Auto-pick up new listings the day after they appear in the snapshot
- No HTTP calls; reads from a sibling repo on disk

## Setup

```bash
# 1. Clone both projects side by side
git clone https://github.com/Zanecex101/cex-watch-mcp.git
git clone https://github.com/Zanecex101/cex-signal-lab.git

# 2. From cex-signal-lab, run the helper
cd cex-signal-lab
python examples/snapshot_universe.py \
    --watch-data ../cex-watch-mcp/data/listings/$(date -u +%F).json \
    > universe.txt
```

## The helper script

Save as `examples/snapshot_universe.py`:

```python
"""Build a tickers allowlist from cex-watch-mcp daily snapshot."""
import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--watch-data", type=Path, required=True,
                   help="Path to cex-watch-mcp data/listings/YYYY-MM-DD.json")
    p.add_argument("--require-min-exchanges", type=int, default=2,
                   help="Symbol (base asset) must appear on at least N exchanges")
    args = p.parse_args()

    payload = json.loads(args.watch_data.read_text())
    counts: dict[str, int] = {}
    for ex_id, info in payload.get("exchanges", {}).items():
        for sym in info.get("pairs_sample", []):
            base = sym.split("-")[0].split("USDT")[0].upper()
            counts[base] = counts.get(base, 0) + 1

    allowed = [b for b, n in counts.items() if n >= args.require_min_exchanges]
    for symbol in sorted(allowed):
        print(symbol + "USDT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## Wiring into the scanner

The scanner doesn't yet read an explicit allowlist (planned post-v0.2),
but you can use the output to update `config.toml`:

```bash
# Generate today's universe
python examples/snapshot_universe.py \
    --watch-data ../cex-watch-mcp/data/listings/$(date -u +%F).json \
    > /tmp/universe.txt

# (Optional) review and prune
wc -l /tmp/universe.txt
```

Then either:

- Use the file as a TOML-list-injection step in your CI / deploy
  script, or
- Wait for the upcoming `[universe.allowlist_file]` config option.

## Why this is interesting

- Two small auditable repos compose into a richer signal pipeline.
- The data layer (cex-watch-mcp) and the strategy layer
  (cex-signal-lab) evolve independently. You can swap either one out.
- Anyone forking *just* the lab still has it work without the sibling
  data feed — coupling is opt-in.
