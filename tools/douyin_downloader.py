import sys
import os
import json
import requests
from playwright.sync_api import sync_playwright

# Ensure stdout is utf-8
sys.stdout.reconfigure(encoding='utf-8')

def download_video(url, output_path):
    print(f"Starting separate process download (SYNC) for: {url}", flush=True)
    metadata = {"title": "Douyin_Video", "duration": 0, "uploader": "Unknown"}
    
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
            
            # Strategy 1
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

            # Strategy 2
            if not video_src:
                video_src = page.evaluate("""() => {
                    const video = document.querySelector('video');
                    if (video) return video.src;
                    const sources = document.querySelectorAll('source');
                    for (const s of sources) {
                        if (s.src && s.src.includes('http')) return s.src;
                    }
                    return null;
                }""")

            if not video_src:
                print("VIDEO_NOT_FOUND")
                return

            print(f"Video Source Found: {video_src[:50]}...", flush=True)
            
            # Get Title
            try:
                title_el = page.query_selector('h1') or page.query_selector('.video-info-title')
                if title_el:
                    metadata["title"] = title_el.inner_text()[:50]
            except:
                pass

            # Download
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.douyin.com/"
            }
            
            r = requests.get(video_src, headers=headers, stream=True)
            if r.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                
                # Output result as JSON to stdout for the caller to parse
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
    url = sys.argv[1]
    output_path = sys.argv[2]
    download_video(url, output_path)