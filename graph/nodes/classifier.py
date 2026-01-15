import os
import re
from urllib.parse import urlparse
from graph.state import AgentState

def classify_input(state: AgentState) -> AgentState:
    """
    Classifies the input source into types (local file vs URL) 
    and detects the specific platform if it's a URL.
    """
    input_source = state["input_source"]
    
    # Check if it's a local file
    if os.path.exists(input_source):
        return {
            **state,
            "source_type": "local",
            "platform": "local",
            "video_path": input_source
        }
    
    # Assume it's a URL if not a file
    parsed_url = urlparse(input_source)
    domain = parsed_url.netloc.lower()
    
    platform = "other"
    if "bilibili" in domain:
        platform = "bilibili"
    elif "douyin" in domain:
        platform = "douyin"
    elif "xiaohongshu" in domain:
        platform = "xiaohongshu"
    elif "youtube" in domain or "youtu.be" in domain:
        platform = "youtube"
        
    return {
        **state,
        "source_type": "url",
        "platform": platform
    }