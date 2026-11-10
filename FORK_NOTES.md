# thirtydays fork notes

This repo is a copy of [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill)
with a personal research dashboard layered on top. Everything outside the
paths below comes from upstream and should not be edited here, so future
updates merge cleanly.

## What lives only in this fork

| Path | What it does |
|---|---|
| `research/` | Saved research briefs (`<topic>-raw.md`). The dashboard reads these. |
| `dashboard/` | `build.py` turns `research/*.md` into `dashboard/dist/data.json`; `index.html` is the dashboard. |
| `api/chat.py` | Vercel function behind the dashboard chat. Needs `ANTHROPIC_API_KEY` in the Vercel project. |
| `vercel.json` | Vercel build settings (runs `dashboard/build.py`). |
| `.github/workflows/research-auto.yml` | Runs research on the 1st and 15th, saves to `research/`, commits, which redeploys the dashboard. |

Upstream maintainer automation that does not apply to this fork is switched
off: `changelog-guard.yml` and `scorecard.yml` only run on the upstream repo
(their files stay because upstream tests read them), and `dependabot.yml` is
removed so the fork doesn't get dependency PRs.

## Auto Research setup

- Repository secrets (all optional): `SCRAPECREATORS_API_KEY` (TikTok, Instagram),
  `XAI_API_KEY` (X), `BRAVE_API_KEY` (web search), `OPENAI_API_KEY`.
  Reddit, Hacker News, Polymarket, GitHub and YouTube (via yt-dlp) work without keys.
- GitHub turns off scheduled workflows after 60 days without repo activity.
  If the Actions tab says the workflow is disabled, open it and press
  "Enable workflow", then "Run workflow" to test.

## Updating from upstream

```bash
git remote add upstream https://github.com/mvanhorn/last30days-skill  # once
git fetch upstream main
git checkout -b update-upstream
git merge upstream/main
# Keep the repository guard on changelog-guard.yml and scorecard.yml,
# and keep .github/dependabot.yml deleted, if the merge brings them back.
uv run pytest -n auto
```
