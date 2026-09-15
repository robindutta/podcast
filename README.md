# Daily News Feed

Builds one podcast-compatible RSS feed containing the newest episode from each configured news source, in a fixed listening order. It is intended as a replacement for a broken Google Home **Play news** routine.

## What is included

The default configuration searches Apple's public podcast directory for close public equivalents of the sources in the supplied Google Home list:

1. BBC Global News Podcast
2. NPR News Now
3. Reuters World News
4. Sky News Daily
5. CNN 5 Things
6. CBC World Report
7. CNBC TechCheck
8. Weird AF News
9. POLITICO Playbook Daily Briefing
10. DW News Brief
11. IGN Game & Entertainment News
12. Science by SciTech Brief
13. The Intelligence (requires a private subscriber URL)
14. NPR technology coverage

Google-only BBC summaries/headlines are represented by one BBC podcast to avoid duplicate stories. Edit `feeds.json` to change the order, search names, age limit, or enable/disable a source.

## Run locally

Python 3.11+; no third-party packages are required.

```bash
python generate_feed.py --base-url https://robindutta.github.io/podcast/
```

This writes `public/feed.xml` and `public/status.json`. For The Economist, set `ECONOMIST_RSS_URL` to your Podcasts+ private RSS URL before running.

## Publish automatically with GitHub Pages

1. In **Settings → Pages**, choose **GitHub Actions** as the source.
2. If you subscribe to Economist Podcasts+, add its private feed as the repository secret `ECONOMIST_RSS_URL`.
3. Run the workflow once. Subscribe your podcast app to `https://robindutta.github.io/podcast/feed.xml`.

The workflow refreshes at 06:00 UTC daily and can also be run manually. Standard GitHub Pages publishing makes the generated `feed.xml` public, so omit the private Economist source unless you host the output privately.

## Google Home playback

Google Home does not reliably accept an arbitrary RSS URL directly. Add the generated URL to a podcast app/service that supports custom RSS, then ask Google Home to play/cast that podcast. Test voice playback before making it the media action in your morning automation.
