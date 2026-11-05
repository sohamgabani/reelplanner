# reelplanner

A small command-line tool to plan Instagram reels across several pages: ideas, hooks, captions, status and post dates. Data is stored locally in SQLite (`~/.reelplanner/reels.db`). No accounts, no API keys, no other people's data.

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Use

```bash
reelplanner page add brandbreakdown.lab --niche "brand breakdowns"
reelplanner add brandbreakdown.lab "Why Nike wins" --hook "Nike doesn't sell shoes"
reelplanner list --status idea
reelplanner edit 1 --status scripted --date 2026-11-10 --caption "Nike sells a feeling. #branding"
reelplanner check 1      # caption checks: length, first line, hashtags, em dashes
reelplanner week         # what's scheduled in the next 7 days
```

## Tests

```bash
pytest
```

See `ROADMAP.md` for planned features.
