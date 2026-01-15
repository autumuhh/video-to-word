import os
import re
from datetime import datetime, timedelta
from graph.state import AgentState

# Note: In a real agentic runtime, we would use the `use_mcp_tool` capability.
# However, since we are inside the application logic here, we will simulate the MCP client
# or directly call the logic if the server is local. 
# For this implementation, to keep it robust and self-contained, I will import the logic 
# directly but structure it as if it were a tool call, preparing for the actual MCP integration.
#
# If the user wants strictly MCP interaction, we would set up an MCP client here.
# For simplicity in this codebase, I will reuse the logic from the server file directly 
# or implement the "Client" side of the logic.

from word_mcp_server.server import generate_docx  # Direct import for simplicity in monolithic app

def parse_timestamp(timestamp_str):
    """Parses HH:MM:SS to total seconds."""
    try:
        parts = list(map(int, timestamp_str.split(':')))
        if len(parts) == 3:
            return parts[0]*3600 + parts[1]*60 + parts[2]
        elif len(parts) == 2:
            return parts[0]*60 + parts[1]
    except:
        return 0
    return 0

def find_closest_screenshot(target_ts_str, screenshots_map):
    """Finds the closest screenshot key to the target timestamp."""
    if not screenshots_map:
        return None
        
    target_seconds = parse_timestamp(target_ts_str)
    
    closest_key = None
    min_diff = float('inf')
    
    for key in screenshots_map.keys():
        current_seconds = parse_timestamp(key)
        diff = abs(current_seconds - target_seconds)
        
        if diff < min_diff:
            min_diff = diff
            closest_key = key
            
    # Allow a tolerance, e.g., within 5 seconds
    if min_diff <= 10:
        return closest_key
    return None

def generate_document(state: AgentState) -> AgentState:
    """
    Generates the final Word document.
    """
    markdown_content = state.get("analysis_result")
    screenshots_map = state.get("screenshots", {})
    metadata = state.get("metadata", {})
    
    if not markdown_content:
        return state

    # Pre-process content to match LLM timestamps with actual file keys
    # The LLM might say 00:05:00 but we have frame_00-05-02.jpg
    
    final_image_map = {}
    
    def replace_tag(match):
        ts_str = match.group(1)
        closest_key = find_closest_screenshot(ts_str, screenshots_map)
        
        if closest_key:
            # We use the original timestamp from LLM as the key in the doc generation
            # and map it to the actual file path we found
            final_image_map[ts_str] = screenshots_map[closest_key]
            return f"[INSERT_IMAGE: {ts_str}]"
        else:
            return f"(Image at {ts_str} not available)"

    processed_content = re.sub(r'\[INSERT_IMAGE:\s*(.*?)\]', replace_tag, markdown_content)
    
    # Define Output Path
    output_dir = os.path.join(os.getcwd(), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    safe_title = re.sub(r'[\\/*?:"<>|]', "", metadata.get("title", "document"))
    filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d%H%M')}.docx"
    output_path = os.path.join(output_dir, filename)
    
    try:
        # Call the "Tool" (Function)
        generate_docx(processed_content, output_path, final_image_map)
        
        return {
            **state,
            "doc_path": output_path
        }
    except Exception as e:
        current_errors = state.get("errors", []) or []
        current_errors.append(f"Document generation failed: {str(e)}")
        return {
            **state,
            "errors": current_errors
        }