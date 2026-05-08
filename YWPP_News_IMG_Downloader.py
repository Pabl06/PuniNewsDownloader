import re
import os
import time
import urllib.request
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser

BANNER_PAGE_URL = "https://gameserver.yw-p.com/web/noticeBannerPage.nhn"
RESOURCE_BASE   = "https://resource.yw-p.com/web/"
OUTPUT_DIR      = "Assets"
DELAY_SECONDS   = 0.5
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

class ImageExtractor(HTMLParser):

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.found: set[str] = set()

    def handle_starttag(self, tag: str, attrs):
        attrs_dict = dict(attrs)
        candidates = []

        if tag == "img" and "src" in attrs_dict:
            candidates.append(attrs_dict["src"])
        elif tag == "a" and "href" in attrs_dict:
            candidates.append(attrs_dict["href"])

        for url in candidates:
            full = urljoin(self.base_url, url)
            if re.search(r"\.(png|gif)(\?.*)?$", full, re.IGNORECASE):
                self.found.add(full)

def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")

def download_image(url: str, dest_path: str) -> bool:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        with open(dest_path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"ERROR {url}: {e}")
        return False

def derive_extra_folders(found_urls: set[str]) -> list[str]:

    folder_re = re.compile(r"XX(\d{6})_([A-Za-z0-9]+)")
    known: set[tuple] = set()
    for url in found_urls:
        m = folder_re.search(url)
        if m:
            known.add((m.group(1), m.group(2)))

    extra: list[str] = []
    for yyyymm, token in known:
        folder = f"XX{yyyymm}_{token}"
        for n in range(1, 31):
            pass
        extra.append(f"{RESOURCE_BASE}{folder}/")
    return extra

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"[1/3] News Website: {BANNER_PAGE_URL}")
    try:
        html = fetch_html(BANNER_PAGE_URL)
    except Exception as e:
        print(f"ERROR: {e}")
        return

    parser = ImageExtractor(BANNER_PAGE_URL)
    parser.feed(html)
    found_urls = parser.found

    extra_hits = set(re.findall(
        r'https://resource\.yw-p\.com/[^\s"\'<>]+\.(?:png|gif)',
        html,
        re.IGNORECASE
    ))
    found_urls.update(extra_hits)

    if not found_urls:
        print("No [.png] were found.")
        return

    print(f"    → {len(found_urls)} images found.\n")

    print(f"[2/3] Downloading images in '{OUTPUT_DIR}/'")
    ok = 0
    fail = 0
    skipped = 0

    for url in sorted(found_urls):
        parsed   = urlparse(url)
        filename = os.path.basename(parsed.path)
        subdir   = os.path.dirname(parsed.path).lstrip("/")
        local_dir = os.path.join(OUTPUT_DIR, subdir)
        os.makedirs(local_dir, exist_ok=True)
        dest = os.path.join(local_dir, filename)

        if os.path.exists(dest):
            print(f"  ↷ Already exists: {filename}")
            skipped += 1
            continue

        print(f"  ↓ {url}")
        if download_image(url, dest):
            ok += 1
        else:
            fail += 1
        time.sleep(DELAY_SECONDS)

    print(f"\n[3/3] Summary:")
    print(f"  Downloaded: {ok}")
    print(f"  Skipped   : {skipped}")
    print(f"  ERROR     : {fail}")

if __name__ == "__main__":
    main()