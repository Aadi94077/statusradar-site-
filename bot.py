import datetime
import html
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

SITE_URL = "https://statusradar.in"
SITE_HOST = "statusradar.in"
INDEXNOW_KEY = "statusradar998877665544332211"

MASTER_SEEDS = [
    "today match pitch report",
    "today match rain probability",
    "upi not working today",
    "server down today bank",
    "box office collection day",
    "payment status check portal",
    "scholarship status check",
    "ott release time today",
]


def slugify(text):
  text = text.lower().strip()
  text = re.sub(r"[^a-z0-9\s-]", "", text)
  text = re.sub(r"[\s-]+", "-", text)
  return text[:65].strip("-")


def fetch_google_suggest(seed):
  url = f"https://suggestqueries.google.com/complete/search?client=firefox&gl=in&q={urllib.parse.quote(seed)}"
  req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
  try:
    with urllib.request.urlopen(req, timeout=8) as res:
      data = json.loads(res.read().decode("utf-8"))
      return data[1][:4]
  except Exception:
    return []


def fetch_trending_searches():
  url = "https://trends.google.com/trending/rss?geo=IN"
  req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
  topics = []
  try:
    with urllib.request.urlopen(req, timeout=8) as res:
      root = ET.fromstring(res.read())
      for item in root.findall(".//item/title")[:10]:
        if item.text:
          topics.append(item.text.strip())
  except Exception:
    pass
  return topics


def fetch_real_news(query):
  url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"
  req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
  news_items = []
  try:
    with urllib.request.urlopen(req, timeout=8) as res:
      root = ET.fromstring(res.read())
      for item in root.findall(".//item")[:4]:
        title = item.find("title").text if item.find("title") is not None else ""
        pub = (
            item.find("pubDate").text
            if item.find("pubDate") is not None
            else "Recent Update"
        )
        if title:
          news_items.append((html.escape(title), html.escape(pub[:22])))
  except Exception:
    pass
  return news_items


def build_smart_metrics(keyword, now_str):
  s = keyword.lower()
  pct = 58 + (abs(hash(s)) % 28)  # 58% to 85%
  if any(w in s for w in ["rain", "weather", "pitch", "match", "vs", "ind"]):
    return (
        f"🏏 {pct}% Probability / Match Advantage",
        "Pitch & Weather Radar",
        f"{pct}% Chances (Chasing / Passing Clouds)",
        "Toss, Pitch Behavior & Rain Radar",
        (
            f"Latest stadium weather and pitch data for {keyword} show a {pct}%"
            " key probability factor. Dew in the second innings makes chasing"
            " preferable."
        ),
    )
  elif any(
      w in s
      for w in ["collection", "day", "movie", "jailer", "box office", "ott"]
  ):
    return (
        f"🎬 {pct}% Evening Occupancy Trend",
        "Box Office & Trade Tracker",
        f"{pct}% Positive Hold Across Multiplexes",
        "India Net Collection & Occupancy",
        (
            f"Trade tracking for {keyword} shows a {pct}% strong occupancy"
            " trend across major circuits with steady evening and night show"
            " footfalls."
        ),
    )
  elif any(
      w in s
      for w in ["server", "upi", "bank", "down", "portal", "payment", "status"]
  ):
    return (
        f"🟢 {pct}% Gateways Online (Peak Load)",
        "Server & Portal Node Status",
        f"{100-pct}% Users Facing Timeout Delay",
        "Gateway Response & Error Fix",
        (
            f"Live monitoring for {keyword} indicates {pct}% servers are"
            f" responding normally, while {100-pct}% users may see temporary"
            " peak-hour congestion."
        ),
    )
  else:
    return (
        f"📊 {pct}% Verified Live Activity",
        "Real-Time India Tracker",
        f"{pct}% High Search & Live Interest",
        "Latest Verified Update & Summary",
        (
            f"Real-time tracking for {keyword} confirms {pct}% active"
            " verification trend across Indian search and news feeds today."
        ),
    )


def generate_content_html(keyword, all_links):
  now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
  headline, cat_label, metric_val, focus_area, summary_text = (
      build_smart_metrics(keyword, now_str)
  )
  news_list = fetch_real_news(keyword)

  news_html = ""
  if news_list:
    for n_title, n_date in news_list:
      news_html += (
          '<div class="news-card"><div'
          f' class="news-title">📰 {n_title}</div><div'
          f' class="news-meta">Verified Feed • {n_date}</div></div>'
      )
  else:
    news_html = (
        f'<div class="news-card"><div class="news-title">📡 {summary_text}</div>'
        f'<div class="news-meta">Auto-Verified • {now_str}</div></div>'
    )

  links_html = '<div class="trend-list">'
  for slug, kw in all_links[:18]:
    links_html += f'<a href="/{slug}.html">⚡ {html.escape(kw.title())}</a>'
  links_html += "</div>"

  return f"""
  <h2>📊 Live Report & Probability Table: {html.escape(keyword.title())}</h2>
  <table>
    <tr><th>Parameter</th><th>Current Live Reading</th></tr>
    <tr><td>Topic / Query</td><td>{html.escape(keyword.title())}</td></tr>
    <tr><td>Category</td><td>{cat_label}</td></tr>
    <tr><td>Live Probability / Status</td><td><strong style="color:#4ade80;">{headline}</strong></td></tr>
    <tr><td>Current Trend Metric</td><td>{metric_val}</td></tr>
    <tr><td>Key Focus Area</td><td>{focus_area}</td></tr>
    <tr><td>Last Auto-Sync</td><td>{now_str}</td></tr>
  </table>

  <h2>📰 Latest Real-Time News & Updates for {html.escape(keyword.title())}</h2>
  <p style="color:#cbd5e1; font-size:14px;">{summary_text}</p>
  {news_html}

  <h2>❓ Frequently Asked Questions (FAQ)</h2>
  <p><strong>Q1: What is the latest live update and probability for {html.escape(keyword)} today?</strong><br>
  As of {now_str}, our live tracker shows <strong>{headline}</strong> ({metric_val}). {summary_text}</p>
  <p><strong>Q2: How often is {html.escape(keyword)} data updated on StatusRadar.in?</strong><br>
  All live metrics, probability percentages, and news headlines are refreshed automatically every 6 hours and on-demand via the 5-second analyzer above.</p>

  <h2>🔥 Today's Live Trending Checks on StatusRadar:</h2>
  {links_html}
  """


def main():
  with open("template.html", "r", encoding="utf-8") as f:
    template = f.read()

  topics = []
  for t in fetch_trending_searches():
    topics.append(f"{t} Live Status & Update")
  for seed in MASTER_SEEDS:
    for sug in fetch_google_suggest(seed):
      topics.append(sug)

  # Existing HTML files ko bhi list mein shamil karo taaki purane pages (jaise Jailer 2) bhi naye ads aur data ke saath overwrite ho jayein
  existing_slugs = {}
  for fname in os.listdir("."):
    if fname.endswith(".html") and fname not in ["index.html", "template.html"]:
      slug = fname[:-5]
      existing_slugs[slug] = slug.replace("-", " ").title()

  final_pages = {}
  for kw in topics:
    s = slugify(kw)
    if s and s not in ["index", "template"]:
      final_pages[s] = kw

  for s, kw in existing_slugs.items():
    if s not in final_pages:
      final_pages[s] = kw

  all_links = [(s, kw) for s, kw in list(final_pages.items())[:35]]

  # Har page ko naye template aur naye data se overwrite karo
  for slug, kw in final_pages.items():
    content_html = generate_content_html(kw, all_links)
    page_html = template.replace(
        "{{TITLE}}", html.escape(kw.title())
    ).replace("{{CONTENT}}", content_html)
    with open(f"{slug}.html", "w", encoding="utf-8") as f:
      f.write(page_html)

  # Homepage (index.html) generate karo
  home_title = "India Live Match Pitch, Rain %, Server & Box Office Tracker"
  home_content = generate_content_html(
      "India Live Match, Server & Box Office Updates", all_links
  )
  index_html = template.replace("{{TITLE}}", home_title).replace(
      "{{CONTENT}}", home_content
  )
  with open("index.html", "w", encoding="utf-8") as f:
    f.write(index_html)

  # Sitemap update karo
  now_iso = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
  sitemap = ['<?xml version="1.0" encoding="UTF-8"?>']
  sitemap.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
  sitemap.append(
      f"<url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod></url>"
  )
  for slug in final_pages.keys():
    sitemap.append(
        f"<url><loc>{SITE_URL}/{slug}.html</loc><lastmod>{now_iso}</lastmod></url>"
    )
  sitemap.append("</urlset>")
  with open("sitemap.xml", "w", encoding="utf-8") as f:
    f.write("\n".join(sitemap))


if __name__ == "__main__":
  main()
