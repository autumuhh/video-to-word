import os
import re
import time
import requests
import traceback
import yt_dlp
import subprocess
import json
import sys
from graph.state import AgentState

def download_with_playwright(url: str, output_path: str) -> dict:
    """
    Fallback downloader using a separate process for Playwright.
    This avoids asyncio loop conflicts with Streamlit/Tornado on Windows.
    """
    script_path = os.path.join(os.getcwd(), "tools", "universal_downloader.py")
    
    # Run the separate script
    try:
        result = subprocess.run(
            [sys.executable, script_path, url, output_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=False
        )
        
        stdout = result.stdout
        stderr = result.stderr
        print(f"Subprocess Output: {stdout}")
        
        # Parse result
        if "JSON_RESULT:" in stdout:
            json_str = stdout.split("JSON_RESULT:")[1].strip()
            data = json.loads(json_str)
            if data["status"] == "success":
                return data["metadata"]
        
        # Check for specific failure markers
        if "ANTI_BOT_TRIGGERED" in stdout:
            raise Exception("Douyin Anti-Bot verification triggered.")
        if "VIDEO_NOT_FOUND" in stdout:
            raise Exception("Video source could not be found on page.")
            
        raise Exception(f"Subprocess failed. Stderr: {stderr}")
        
    except Exception as e:
        raise Exception(f"External downloader failed: {str(e)}")

def clean_douyin_url(url: str) -> str:
    """
    Cleans Douyin URL to be friendly for yt-dlp.
    Converts .../jingxuan?modal_id=xxx -> .../video/xxx
    """
    if "douyin.com" in url and "modal_id=" in url:
        match = re.search(r'modal_id=(\d+)', url)
        if match:
            video_id = match.group(1)
            return f"https://www.douyin.com/video/{video_id}"
    return url

def get_ydl_opts(url, output_template):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    if "douyin.com" in url:
        headers['Referer'] = 'https://www.douyin.com/'
    elif "bilibili.com" in url:
        headers['Referer'] = 'https://www.bilibili.com/'
        
    return {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'http_headers': headers
    }

def download_video(state: AgentState) -> AgentState:
    """
    Downloads video from the input URL using yt-dlp.
    """
    raw_url = state.get("input_source")
    if not raw_url:
        return state

    # Preprocess URL for specific platforms
    url = clean_douyin_url(raw_url)

    # Ensure temp directory exists
    temp_dir = os.path.join(os.getcwd(), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Template for output filename
    output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')
    
    ydl_opts = get_ydl_opts(url, output_template)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            return {
                **state,
                "video_path": filename,
                "metadata": {
                    "title": info.get("title", "Unknown Title"),
                    "duration": info.get("duration", 0),
                    "uploader": info.get("uploader", "Unknown")
                }
            }
    except Exception as e:
        error_msg = str(e)
        # Check if it's a cookie or 403 issue, try Playwright fallback for Douyin and Bilibili
        is_retryable = any(x in url for x in ["douyin", "bilibili"]) and \
                       any(x in error_msg.lower() for x in ["cookie", "403", "forbidden"])
        
        if is_retryable:
            try:
                fallback_filename = os.path.join(temp_dir, f"fallback_{int(time.time())}.mp4")
                metadata = download_with_playwright(url, fallback_filename)
                
                return {
                    **state,
                    "video_path": fallback_filename,
                    "metadata": metadata
                }
            except Exception as e_pw:
                current_errors = state.get("errors", []) or []
                current_errors.append(f"Download failed (yt-dlp): {error_msg}")
                # Log full traceback to debug the 'empty error' issue
                tb_str = traceback.format_exc()
                current_errors.append(f"Download failed (Playwright fallback): {str(e_pw)} | Trace: {tb_str}")
                return {**state, "errors": current_errors}
        
        current_errors = state.get("errors", []) or []
        current_errors.append(f"Download failed: {error_msg}")
        return {
            **state,
            "errors": current_errors
        }