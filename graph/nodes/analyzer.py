import os
import base64
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from graph.state import AgentState

# Load environment variables
load_dotenv()

# Configure API Key
API_KEY = os.getenv("GOOGLE_API_KEY")
API_BASE = os.getenv("GOOGLE_API_BASE", "https://cli.dearmer.xyz")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash-exp")

def analyze_video(state: AgentState) -> AgentState:
    """
    Analyzes the video using an OpenAI-compatible API (e.g. OneAPI wrapping Gemini)
    Note: Since OpenAI-compatible APIs typically don't support direct video file upload
    in the same way as native Gemini SDK, we will use the 'screenshots' we extracted earlier
    to perform a 'visual analysis' of the keyframes + audio transcript (if we had it).
    
    HOWEVER, if the user's endpoint SUPPORTS video inputs (like some multimodal wrappers),
    we could try sending the video. But the safest bet for 'sk-' keys on custom endpoints
    is to treat it as a Vision model request with images.
    
    Given the constraint, we will send the KEYFRAMES (Screenshots) to the model.
    """
    screenshots_map = state.get("screenshots", {})
    if not screenshots_map:
        current_errors = state.get("errors", []) or []
        current_errors.append("No screenshots extracted for analysis.")
        return {**state, "errors": current_errors}

    if not API_KEY:
        current_errors = state.get("errors", []) or []
        current_errors.append("API Key not found.")
        return {**state, "errors": current_errors}

    try:
        # Initialize ChatOpenAI
        llm = ChatOpenAI(
            model=LLM_MODEL,
            api_key=API_KEY,
            base_url=f"{API_BASE}/v1" if not API_BASE.endswith("/v1") else API_BASE,
            temperature=0.3,
            max_tokens=4096
        )

        # Prepare System Prompt
        system_prompt = """
        You are an expert academic researcher and technical writer.
        I will provide you with a series of screenshots from a video, indexed by timestamp.
        Your task is to transform this video content into a **professional academic paper (论文)** style document in Markdown format.
        
        **Requirements:**
        
        1.  **Structure**:
            *   **Title**: Formal academic title.
            *   **Abstract (摘要)**: Concise summary of the core content (150-200 words).
            *   **Introduction (引言)**: Background context of the video topic.
            *   **Core Analysis (正文分析)**: Deep dive into the content. Use academic headings (## 1. / ## 2.).
            *   **Conclusion (结论)**: Key takeaways and synthesis.
            
        2.  **Tone & Style**:
            *   Use **Academic/Scholarly tone** (objective, analytical, formal).
            *   Avoid colloquialisms. Use professional terminology.
            *   "Deep Analysis": Don't just describe what is happening; analyze *why* it is important and the underlying logic.
            
        3.  **Visual Evidence**:
            *   Treat screenshots as "Figures".
            *   When discussing a specific visual concept, insert the tag `[INSERT_IMAGE: HH:MM:SS]`.
            *   Refer to images formally, e.g., "As shown in the figure above...".
            
        4.  **Language**: Simplified Chinese (简体中文).
        
        **CRITICAL CONSTRAINT**:
        *   Do NOT invent external references or bibliography (citations).
        *   The "Reference" is ONLY the video content itself.
        *   Do not hallucinate paper titles that were not explicitly mentioned in the video.
        """

        # Prepare User Message with Images
        # We need to limit the number of images to avoid token limits if the video is huge.
        # Let's take up to 20 evenly spaced frames for this version.
        
        sorted_keys = sorted(screenshots_map.keys())
        # Simple sampling if too many
        if len(sorted_keys) > 20:
            step = len(sorted_keys) // 20
            selected_keys = sorted_keys[::step][:20]
        else:
            selected_keys = sorted_keys

        content_parts = []
        content_parts.append({"type": "text", "text": "Here are the keyframes from the video:"})

        for ts in selected_keys:
            img_path = screenshots_map[ts]
            with open(img_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            content_parts.append({
                "type": "text",
                "text": f"Timestamp: {ts}"
            })
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })

        message = HumanMessage(content=content_parts)
        
        print("Sending request to LLM...")
        response = llm.invoke([SystemMessage(content=system_prompt), message])

        return {
            **state,
            "analysis_result": response.content
        }

    except Exception as e:
        current_errors = state.get("errors", []) or []
        current_errors.append(f"Analysis failed: {str(e)}")
        return {
            **state,
            "errors": current_errors
        }