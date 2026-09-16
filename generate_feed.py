#!/usr/bin/env python3
import argparse, datetime as dt, email.utils, hashlib, html, json, os, pathlib, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

UA = "DailyNewsFeed/1.0 (+personal podcast feed generator)"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()

def resolve(source):
    if source.get("feed_url"):
        return source["feed_url"]
    if source.get("feed_env"):
        return os.environ.get(source["feed_env"])
    query = urllib.parse.urlencode({"term": source["search"], "media": "podcast", "entity": "podcast", "limit": 20})
    results = json.loads(get("https://itunes.apple.com/search?" + query)).get("results", [])
    target = source["search"].casefold(); publisher = source.get("publisher", "").casefold()
    def score(x):
        name = x.get("collectionName", "").casefold(); artist = x.get("artistName", "").casefold()
        return (100 if name == target else 60 if target in name or name in target else 0) + (30 if publisher and publisher in artist else 0)
    matches = [x for x in results if x.get("feedUrl")]
    best = max(matches, key=score) if matches else None
    return best.get("feedUrl") if best and score(best) >= 60 else None

def local(tag): return tag.rsplit("}", 1)[-1].lower()
def child(node, *names):
    wanted = {n.lower() for n in names}
    return next((x for x in node if local(x.tag) in wanted), None)
def text_of(node, *names):
    x = child(node, *names); return (x.text or "").strip() if x is not None else ""

def parse_date(value):
    try:
        d = email.utils.parsedate_to_datetime(value)
        return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
    except Exception: return dt.datetime.min.replace(tzinfo=dt.timezone.utc)

def newest(feed_bytes):
    root = ET.fromstring(feed_bytes)
    candidates = [x for x in root.iter() if local(x.tag) in {"item", "entry"}]
    parsed = []
    for item in candidates:
        enclosure = child(item, "enclosure")
        audio = enclosure.get("url") if enclosure is not None else ""
        if not audio:
            for link in [x for x in item if local(x.tag) == "link"]:
                if link.get("rel") == "enclosure" or link.get("type", "").startswith("audio/"):
                    audio = link.get("href", ""); break
        date_s = text_of(item, "pubDate", "published", "updated")
        if audio: parsed.append((parse_date(date_s), item, audio, enclosure))
    return max(parsed, key=lambda x: x[0]) if parsed else None

def esc(s): return html.escape(s or "", quote=True)

def build(config, base_url):
    now = dt.datetime.now(dt.timezone.utc); selected=[]; status=[]
    for index, source in enumerate(config["sources"]):
        if not source.get("enabled", True): continue
        try:
            url = resolve(source)
            if not url: raise ValueError("no matching public podcast feed")
            episode = newest(get(url))
            if not episode: raise ValueError("feed has no playable audio enclosure")
            published, item, audio, enclosure = episode
            if audio.startswith("http://"):
                audio = "https://" + audio[len("http://"):]
            age = (now - published).total_seconds() / 3600
            if age > config.get("max_age_hours", 72): raise ValueError(f"newest episode is {age:.0f} hours old")
            title = text_of(item, "title") or source["name"]
            desc = text_of(item, "description", "summary", "content")
            guid = text_of(item, "guid", "id") or audio
            mime = enclosure.get("type", "audio/mpeg") if enclosure is not None else "audio/mpeg"
            length = enclosure.get("length", "0") if enclosure is not None else "0"
            selected.append({"source": source["name"], "title": title, "description": desc, "audio": audio,
                             "guid": hashlib.sha256((source["name"]+guid).encode()).hexdigest(), "mime": mime,
                             "length": length, "date": now-dt.timedelta(minutes=index)})
            status.append({"source": source["name"], "status": "included", "feed": url, "episode": title})
        except Exception as e:
            status.append({"source": source["name"], "status": "skipped", "reason": str(e)})
    feed_url = urllib.parse.urljoin(base_url.rstrip("/") + "/", "feed.xml")
    lines=['<?xml version="1.0" encoding="UTF-8"?>',
           '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"><channel>',
           f'<title>{esc(config["title"])}</title>', f'<link>{esc(base_url)}</link>',
           f'<description>{esc(config["description"])}</description>', '<language>en-gb</language>',
           f'<atom:link href="{esc(feed_url)}" rel="self" type="application/rss+xml"/>',
           '<itunes:type>episodic</itunes:type>', '<itunes:author>Robin Dutta</itunes:author>',
           f'<itunes:summary>{esc(config["description"])}</itunes:summary>',
           '<itunes:explicit>false</itunes:explicit>', '<itunes:category text="News"/>',
           f'<lastBuildDate>{email.utils.format_datetime(now)}</lastBuildDate>']
    for x in selected:
        item_title = x["source"]+" — "+x["title"]
        lines += ['<item>', f'<title>{esc(item_title)}</title>', f'<itunes:title>{esc(item_title)}</itunes:title>',
                  f'<description>{esc(x["description"])}</description>', f'<guid isPermaLink="false">{x["guid"]}</guid>',
                  f'<link>{esc(x["audio"])}</link>', '<itunes:episodeType>full</itunes:episodeType>',
                  f'<pubDate>{email.utils.format_datetime(x["date"])}</pubDate>',
                  f'<enclosure url="{esc(x["audio"])}" length="{esc(x["length"])}" type="{esc(x["mime"])}"/>', '</item>']
    lines += ['</channel></rss>']
    return "\n".join(lines)+"\n", status

def main():
    p=argparse.ArgumentParser(); p.add_argument("--config", default="feeds.json"); p.add_argument("--output", default="public/feed.xml")
    p.add_argument("--base-url", required=True); a=p.parse_args(); config=json.loads(pathlib.Path(a.config).read_text(encoding="utf-8"))
    xml,status=build(config,a.base_url); out=pathlib.Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(xml,encoding="utf-8"); (out.parent/"status.json").write_text(json.dumps(status,indent=2),encoding="utf-8")
    print(f"Wrote {out} with {sum(x['status']=='included' for x in status)} episodes")
if __name__ == "__main__": main()
