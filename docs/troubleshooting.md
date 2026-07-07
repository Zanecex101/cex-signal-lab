# Troubleshooting

## "trades.json is suddenly empty after reboot"

You hit a power loss mid-write. Atomic-write was added in Day 8; if
you're on an earlier rev, upgrade and restore from `trades.json.bak`.

## "all my open trades are stuck open forever"

Day 17 introduced the monitor pass. If you're on a pre-monitor rev,
upgrade. If you're current, check that `cron` hasn't silently stopped
firing the scanner.

## "env_filter sometimes scores sentiment 0"

The Fear & Greed feed (alternative.me) has a short outage every few
weeks. Day 31 added an explicit log line. Look in your scanner log for
"FGI unavailable". Normal, not a bug.

## "scanner runs but no trades open"

Drop `LOG_LEVEL=DEBUG` and run a single scan. The env_filter line
will show which factor is voting -1.

## "cron fires twice in the same minute"

Use the fcntl lock added in Day 9. The second instance will log
"another scan is in flight" and exit cleanly.
