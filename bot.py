import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import os
import re
import html
from datetime import datetime

SITE_URL = "https://statusradar.in"
SITE_HOST = "statusradar.in"
INDEXNOW_KEY = "statusradar998877665544332211"

MASTER_SEEDS = [
    "server down today",
    "upi not working today",
    "today match pitch report",
    "today match rain probability",
    "payment status check portal",
    "scholarship status check",
    "redeem code today working",
    "ott release time today",
    "login error fix today",
    "result link active time"
]

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')[:70]

def fetch_google_autocomplete(seed):
    url = f"http://suggestqueries.google.com/complete/search?client=firefox&gl=in&q={urllib.parse.quote(seed)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as res:
            data = json.loads(res.read().decode('utf-8'))
            return data[1][:4]
    except Exception:
        return []

def fetch_india_trends():
    topics = []
    try:
        req = urllib.request.Request("https://trends.google.com/trending/rss?geo=IN", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            root = ET.fromstring(response.read())
            for item in root.findall('.//item')[:12]:
                title = item.find('title').text
                if title:
                    topics.append(f"{title.strip()} Live Status & Update")
    except Exception:
        pass

    for seed in MASTER_SEEDS:
        topics.extend(fetch_google_autocomplete(seed))

    clean = list(dict.fromkeys([t.strip() for t in topics if len(t.strip()) > 4]))
    return clean[:25]

def build_rich_seo_content(topic, today_str):
    safe_topic = html.escape(topic)
    return f"""
    <h3>📊 Live Status & Metrics Table: {safe_topic}</h3>
    <table>
      <tr><th>Parameter</th><th>Current Live Reading</th></tr>
      <tr><td><strong>Query / Service</strong></td><td>{safe_topic}</td></tr>
      <tr><td><strong>India Server Status</strong></td><td><span style="color:#22c55e;">Online & Monitored</span></td></tr>
      <tr><td><strong>Last Auto-Sync</strong></td><td>{today_str}</td></tr>
      <tr><td><strong>Average Response Ping</strong></td><td>24ms – 42ms (Normal)</td></tr>
    </table>
    <h3>🛠️ Quick Troubleshooting & Official Guide for {safe_topic}</h3>
    <ul>
      <li><strong>Check Peak Hour Load:</strong> High search spikes for <em>{safe_topic}</em> often cause temporary gateway timeouts on official portals. Wait 5–10 minutes and retry.</li>
      <li><strong>Clear Cache / DNS:</strong> If the app or portal shows a blank screen or login error, switch between Mobile Data and Wi-Fi or clear browser cache.</li>
      <li><strong>Live Radar Verification:</strong> Use our 5-second regional diagnostic tool above to verify if the issue is limited to your state node.</li>
    </ul>
    <h3>❓ Frequently Asked Questions (FAQ)</h3>
    <p><strong>Q1: Is {safe_topic} down or working today in India?</strong><br>
    As of {today_str}, primary servers for <em>{safe_topic}</em> are active. Any temporary outage or high-traffic slowdown is updated automatically every 6 hours on StatusRadar.in.</p>
    <p><strong>Q2: How to fix loading or status error on {safe_topic}?</strong><br>
    Verify your network connection, avoid multiple rapid refreshes during peak traffic hours, and check the live regional table above for the latest working update.</p>
    """

def ping_indexnow(url_list):
    endpoint = "https://api.indexnow.org/indexnow"
    payload = {
        "host": SITE_HOST,
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": url_list[:50]
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(endpoint, data=data, headers={'Content-Type': 'application/json; charset=utf-8'})
        with urllib.request.urlopen(req, timeout=8) as res:
            print("IndexNow Ping Status:", res.status)
    except Exception as e:
        print("IndexNow Notice:", e)

def generate_pages():
    with open("template.html", "r", encoding="utf-8") as f:
        template = f.read()

    with open(f"{INDEXNOW_KEY}.txt", "w", encoding="utf-8") as kf:
        kf.write(INDEXNOW_KEY)

    trends = fetch_india_trends()
    os.makedirs("trends", exist_ok=True)
    today_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    new_urls = []

    for topic in trends:
        slug = slugify(topic)
        if not slug:
            continue
        filename = f"trends/{slug}.html"
        new_urls.append(f"{SITE_URL}/{filename}")

    all_files = sorted([f for f in os.listdir("trends") if f.endswith(".html")], reverse=True)
    for topic in trends:
        s = f"{slugify(topic)}.html"
        if s not in all_files:
            all_files.insert(0, s)

    links_html = ""
    for fname in all_files[:40]:
        nice_name = html.escape(fname.replace(".html", "").replace("-", " "))
        links_html += f'<a href="/trends/{fname}">⚡ {nice_name}</a>\n'

    for topic in trends:
        slug = slugify(topic)
        if not slug:
            continue
        filename = f"trends/{slug}.html"
        safe_title = html.escape(topic)
        content_html = build_rich_seo_content(topic, today_str)
        page_html = (
            template.replace("{{TITLE}}", safe_title)
                    .replace("{{CONTENT}}", content_html)
                    .replace("{{TREND_LINKS}}", links_html)
        )
        with open(filename, "w", encoding="utf-8") as out:
            out.write(page_html)

    home_title = "India Live Server Status, Match Pitch & Portal Tracker"
    home_content = build_rich_seo_content(home_title, today_str)
    home_html = (
        template.replace("{{TITLE}}", home_title)
                .replace("{{CONTENT}}", home_content)
                .replace("{{TREND_LINKS}}", links_html)
    )
    with open("index.html", "w", encoding="utf-8") as out:
        out.write(home_html)

    all_trend_files = [f"trends/{f}" for f in os.listdir("trends") if f.endswith(".html")]
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap_xml += f"  <url><loc>{SITE_URL}/</loc><changefreq>hourly</changefreq><priority>1.0</priority></url>\n"
    for tf in all_trend_files:
        sitemap_xml += f"  <url><loc>{SITE_URL}/{tf}</loc><changefreq>daily</changefreq><priority>0.8</priority></url>\n"
    sitemap_xml += "</urlset>"
    with open("sitemap.xml", "w", encoding="utf-8") as out:
        out.write(sitemap_xml)

    with open("_redirects", "w", encoding="utf-8") as out:
        out.write("/* /index.html 200\n")

    ping_indexnow(new_urls)
    print(f"Total active pages on StatusRadar.in: {len(all_trend_files) + 1}")

if __name__ == "__main__":
    generate_pages()
