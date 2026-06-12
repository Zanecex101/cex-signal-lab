# Changelog

All notable changes to cex-signal-lab. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

(no unreleased changes)

## [0.2.0] — 2026-06-12

### Added
- 5th strategy: FundingFlip — detects funding rate sign flip with
  non-trivial magnitude (regime change signal, complements the four
  extreme-state strategies)

### Changed
- README status badge → stable v0.2.0
- Default config.example.toml ships with FundingFlip enabled
- README v0.3 with a full screenshot of the daily summary

## [0.1.0] — 2026-05 (current)

End of the deliberate-30-day build. Lab is end-to-end functional and
hardened. From this point forward, changes go through CI on every PR.

### Added
- Strategy ABC + 4 reference signal modules:
  funding_extreme_neg / funding_extreme_pos / crash_bounce / pump_short
- Typed Ledger module with atomic writes + .bak rotation + fsync
- Process lock (fcntl.flock) prevents concurrent-scan corruption
- env_filter: 4-factor scoring with strength bonus
- Position monitor: auto SL/TP exit on every scan cycle
- Executor: opens paper-trades respecting cooldown / max-open caps
- TOML-driven config with typed dataclasses
- Telegram notifications with MarkdownV2 escaping + retry/backoff
- stdlib logging (LOG_LEVEL env var)
- `cex-signal-lab` CLI (scanner) + `cex-signal-summary` CLI (stats)
- Dockerfile + docker-compose.yml
- GitHub Actions tests workflow on Python 3.10/11/12
- Unit tests for ledger, config, lock

### Documentation
- Architecture diagram + per-module responsibility map
- Strategies math + intuition
- Configuring guide for every TOML knob
- Contributing walkthrough for new strategies
- Sibling-project example with cex-watch-mcp

## [0.1.0a1] — 2026-05 (initial scaffold)

- Project skeleton: pyproject, LICENSE, README, .gitignore
- Configuration schema in config.example.toml
