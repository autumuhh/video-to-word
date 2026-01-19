import sys
import os
import json
import requests
from playwright.sync_api import sync_playwright

# Ensure stdout is utf-8
sys.stdout.reconfigure(encoding='utf-8')

def get_referer(url):
    if "douyin.com" in url:
        return "https://www.douyin.com/"
    if "bilibili.com" in url:
        return "https://www.bilibili.com/"
    return None

def download_video(url, output_path):
    print(f"Starting separate process download (SYNC) for: {url}", flush=True)
    metadata = {"title": "Web_Video", "duration": 0, "uploader": "Unknown"}
    
    referer = get_referer(url)
    
    with sync_playwright() as p:
        print("Launching browser...", flush=True)
        browser = p.chromium.launch(headless=True)
        print("Browser launched. Creating context...", flush=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            print(f"Navigating to {url}...", flush=True)
            page.goto(url, timeout=45000)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass
            
            page_title = page.title()
            print(f"Page Title: {page_title}", flush=True)
            
            # Anti-bot check
            if "验证" in page_title or "verify" in page.url:
                print("ANTI_BOT_TRIGGERED")
                return

            video_src = None
            
            # Strategy 1: Find video tag
            try:
                video_element = page.wait_for_selector('video', state="attached", timeout=8000)
                if video_element:
                    video_src = video_element.get_attribute('src')
                    if not video_src or video_src.startswith('blob:'):
                        source = page.query_selector('video source')
                        if source:
                            video_src = source.get_attribute('src')
            except:
                pass

            # Strategy 2: JS Eval
            if not video_src or video_src.startswith('blob:'):
                video_src = page.evaluate("""() => {
                    const video = document.querySelector('video');
                    if (video && video.src && !video.src.startsWith('blob:')) return video.src;
                    const sources = document.querySelectorAll('source');
                    for (const s of sources) {
                        if (s.src && s.src.includes('http') && !s.src.startswith('blob:')) return s.src;
                    }
                    return null;
                }""")

            if not video_src:
                print("VIDEO_NOT_FOUND_OR_BLOB")
                # If it's Bilibili or similar, it might be using DASH/HLS which shows as blob.
                # In such cases, we might need a more specialized extractor or just rely on yt-dlp 
                # but with better headers/cookies.
                return

            print(f"Video Source Found: {video_src[:50]}...", flush=True)
            
            # Get Title
            try:
                title_el = page.query_selector('h1') or page.query_selector('.video-info-title') or page.query_selector('.video-title')
                if title_el:
                    metadata["title"] = title_el.inner_text()[:50]
            except:
                pass

            # Download
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            if referer:
                headers["Referer"] = referer
            
            r = requests.get(video_src, headers=headers, stream=True)
            if r.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                
                result = {
                    "status": "success",
                    "path": output_path,
                    "metadata": metadata
                }
                print("JSON_RESULT:" + json.dumps(result), flush=True)
            else:
                print(f"DOWNLOAD_ERROR:{r.status_code}", flush=True)

        except Exception as e:
            print(f"EXCEPTION:{str(e)}", flush=True)
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python universal_downloader.py <url> <output_path>")
        sys.exit(1)
    url = sys.argv[1]
    output_path = sys.argv[2]
    download_video(url, output_path)
