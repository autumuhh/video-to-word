import os
import cv2
import numpy as np
from graph.state import AgentState

def extract_keyframes(video_path, output_dir, threshold=30):
    """
    Extracts keyframes based on scene changes.
    Returns a dictionary mapping timestamp (HH:MM:SS) to image path.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {}

    fps = cap.get(cv2.CAP_PROP_FPS)
    prev_frame = None
    screenshots = {}
    frame_count = 0
    
    # Create screenshots directory
    os.makedirs(output_dir, exist_ok=True)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Process every nth frame (e.g., every 1 second) to speed up
        if frame_count % int(fps) == 0:
            timestamp_seconds = frame_count / fps
            timestamp_str = format_timestamp(timestamp_seconds)
            
            # Convert to grayscale for comparison
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            if prev_frame is None:
                # Always save the first frame
                save_frame(frame, output_dir, timestamp_str, screenshots)
                prev_frame = gray
            else:
                # Compute difference
                frame_delta = cv2.absdiff(prev_frame, gray)
                thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
                change_score = np.mean(thresh)
                
                # If change is significant, save as new keyframe
                if change_score > threshold:
                    save_frame(frame, output_dir, timestamp_str, screenshots)
                    prev_frame = gray
        
        frame_count += 1
        
    cap.release()
    return screenshots

def save_frame(frame, output_dir, timestamp_str, screenshots_map):
    filename = f"frame_{timestamp_str.replace(':', '-')}.jpg"
    path = os.path.join(output_dir, filename)
    
    # cv2.imwrite does not support unicode paths on Windows, use imencode + write
    is_success, buffer = cv2.imencode(".jpg", frame)
    if is_success:
        with open(path, "wb") as f:
            f.write(buffer)
        screenshots_map[timestamp_str] = path

def format_timestamp(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "{:02d}:{:02d}:{:02d}".format(int(h), int(m), int(s))

def process_video(state: AgentState) -> AgentState:
    """
    Processes the video to extract keyframes/screenshots.
    """
    video_path = state.get("video_path")
    if not video_path or not os.path.exists(video_path):
        return state
        
    # Define output directory for this specific video processing
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    screenshots_dir = os.path.join(os.getcwd(), "temp", "screenshots", base_name)
    
    try:
        screenshots_map = extract_keyframes(video_path, screenshots_dir)
        return {
            **state,
            "screenshots": screenshots_map
        }
    except Exception as e:
        current_errors = state.get("errors", []) or []
        current_errors.append(f"Processing failed: {str(e)}")
        return {
            **state,
            "errors": current_errors
        }