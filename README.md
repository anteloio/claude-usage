# claude-limits

How much of your Claude plan is gone, printed in your terminal instead of hidden
behind `/usage` inside a Claude Code session.

```
claude plan limits · max

  session (5h)       ████····················  15%  resets in 1h52m
  week (all models)  ████████················  32%  resets in 8h52m
  week (Fable)       ███·····················  14%  resets in 8h52m
```

## Install

```sh
git clone <this repo> ~/projects/claude-limits
cd ~/projects/claude-limits && ./install.sh
```

That symlinks `claude-limits` into `~/.local/bin` and appends a hook to `~/.zshrc`
so every new shell opens with the report. Both steps are idempotent.

macOS only for now: the OAuth token is read from the login keychain.

## Usage

| command | what it does |
| --- | --- |
| `claude-limits` | report, refreshing only if the cache is older than 10 minutes |
| `claude-limits --cached` | print instantly from cache, refresh in the background |
| `claude-limits --fresh` | force a refresh now |
| `claude-limits --oneline` | `5h 15% · 7d 32% · fable 14%` |
| `claude-limits --json` | the raw endpoint payload |
| `claude-limits --watch` | redraw every 60s |

`cl` is aliased to `claude-limits --fresh`.

## Where the numbers come from

`GET https://api.anthropic.com/api/oauth/usage`, the same endpoint the built-in
`/usage` screen reads, authenticated with the OAuth token Claude Code already
stores in the keychain under `Claude Code-credentials`. Nothing is sent anywhere
else and nothing is written outside `~/.cache/claude-limits`.

The endpoint is undocumented and can change without notice.

The response carries a `limits[]` array, which is what gets rendered:

- `kind: "session"` — the rolling 5-hour window, shared by every model
- `kind: "weekly_all"` — the 7-day window, shared by every model
- `kind: "weekly_scoped"` — a 7-day window for one model, eg Fable

There is no session-scoped variant. A model with its own weekly cap still spends
from the shared 5-hour window, so it can hit either ceiling.

## Why it is so careful about refreshing

The endpoint rate-limits aggressively and sends no `Retry-After`. Polling at 30s,
60s and even 120s has been reported to produce 429s that then persist for half an
hour ([claude-code#31637](https://github.com/anthropics/claude-code/issues/31637),
closed as not planned). The failure mode is a tool that keeps hammering and never
recovers, so three things guard against it:

**A 10-minute TTL.** These are 5-hour and 7-day windows. Reading them once a
minute was never worth anything.

**Backoff persisted to disk.** On a 429 the next allowed attempt is written to
`~/.cache/claude-limits/state.json` and grows 5m → 10m → 20m → 1h, reset on the
first success. It has to live on disk: every new shell is a fresh process, so
in-memory backoff would be no backoff at all.

**Stale data never becomes an error.** A failed refresh keeps the previous
payload and adds an `as of 12m ago` note. Your prompt does not get a stack trace
because an endpoint was grumpy.

`--cached`, which is what the shell hook calls, never blocks on the network at
all: it prints what is on disk and forks the refresh. Cold start is one blocking
fetch so the first run is not empty; after that it is a file read.

## What this is not

It is not [ccusage](https://github.com/ccusage/ccusage) or
[Claude-Code-Usage-Monitor](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor).
Those parse local session transcripts and estimate token counts and a dollar
figure. They do not know your plan's ceilings. This reports the percentages
Anthropic actually enforces, and nothing else.

There are also several status line projects that show the same 5h and 7d numbers
inside Claude Code, taken for free from `rate_limits` on the status line's stdin.
If that is all you want, use one of those — no network, no 429. Two reasons to
want this instead: it works in a plain terminal with no Claude Code session
running, and the status line payload carries only `five_hour` and `seven_day`,
so per-model buckets like Fable are not in it.
