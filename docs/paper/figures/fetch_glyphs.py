"""Download the ancient glyph forms used in qi-figure.tex from Wikimedia Commons, convert them to PDF with
Inkscape, and write CREDITS.md. Run from this folder:  python fetch_glyphs.py
The files are the Wiktionary glyph-origin images (Commons file names like 器-bronze.svg); the licence is read from
Commons at download time. A form that does not exist for a character is simply skipped."""
import json, subprocess, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

UA = {"User-Agent": "zitex-figure/0.1 (research; wen.gong.research@gmail.com)"}
CHARS = "器囂哭喪武戈兵犬頁"
KINDS = ["oracle", "bronze", "seal"]
out = Path("glyphs")
out.mkdir(exist_ok=True)

titles = [f"File:{c}-{k}.svg" for c in CHARS for k in KINDS]
rows = []
for i in range(0, len(titles), 40):
    q = urllib.parse.urlencode({"action": "query", "titles": "|".join(titles[i:i + 40]), "prop": "imageinfo",
                                "iiprop": "url|extmetadata", "format": "json"})
    data = json.load(urllib.request.urlopen(urllib.request.Request("https://commons.wikimedia.org/w/api.php?" + q, headers=UA), timeout=30))
    for p in data["query"]["pages"].values():
        if "imageinfo" in p:
            info = p["imageinfo"][0]
            rows.append((p["title"][5:], info["url"], info["extmetadata"].get("LicenseShortName", {}).get("value", "?")))


def download(url: str) -> bytes:
    """Commons rate-limits bots: go slowly, and wait and retry on 429."""
    for wait in (2, 10, 30, 60):
        try:
            time.sleep(1.5)
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(wait)
    raise RuntimeError(f"still rate limited: {url}")


for name, url, lic in sorted(rows):
    svg = out / name
    if svg.exists() and svg.with_suffix(".pdf").exists():
        continue                                        # already fetched
    svg.write_bytes(download(url))
    subprocess.run(["inkscape", str(svg), "--export-type=pdf", f"--export-filename={svg.with_suffix('.pdf')}"], check=True, capture_output=True)
Path("CREDITS.md").write_text(
    "# Glyph images\n\nAncient forms from Wikimedia Commons (the images used in Wiktionary's glyph-origin sections). "
    "Licence as read from Commons on download:\n\n" + "\n".join(f"- `{n}`: {lic}. {u}" for n, u, lic in sorted(rows)) + "\n", encoding="utf-8")
print(len(rows), "glyph files")
