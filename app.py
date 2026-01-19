import os
import time
import sys
import asyncio
import re
import streamlit as st
from dotenv import load_dotenv
from ddgs import DDGS
from graph.graph_builder import build_graph

# Fix for Playwright on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Setup Page
st.set_page_config(
    page_title="Video2Word Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Load environment variables silently
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Custom CSS for beautification
st.markdown("""
<style>
    /* Main container padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
        max-width: 900px; /* Limit width for better readability on wide screens */
    }
    /* Chat input styling */
    .stChatInputContainer {
        padding-bottom: 20px;
        max-width: 900px;
        margin: 0 auto;
    }
    /* Message bubbles */
    .stChatMessage {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    .stChatMessage[data-testid="stChatMessageUser"] {
        background-color: #f0f7ff;
        border-color: #d0e3ff;
    }
    /* Header styling */
    h1 {
        color: #0d47a1;
        font-weight: 800;
        font-size: 2.2rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    /* Custom button */
    .stButton button {
        background-color: #1976d2;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1.2rem;
        border: none;
        transition: all 0.2s;
    }
    .stButton button:hover {
        background-color: #1565c0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    /* Caption */
    .custom-caption {
        text-align: center;
        color: #666;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    /* Hide Streamlit Toolbar/Footer */
    [data-testid="stToolbar"] {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
</style>
""", unsafe_allow_html=True)

# Header Area
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("🤖 视频转文档智能助手")
    st.markdown('<p class="custom-caption">全自动视频理解 • 智能截图 • Word 笔记生成</p>', unsafe_allow_html=True)

# Sidebar - Simplified
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=80)
    st.markdown("### 🛠️ 功能菜单")
    
    st.info(f"🟢 系统状态: 在线\n\n🧠 模型: **Gemini 3 Flash Preview**")
    
    st.markdown("---")
    st.markdown("**支持平台:**")
    st.markdown("- 📺 Bilibili / YouTube")
    st.markdown("- 🎵 抖音 / 小红书")
    st.markdown("- 📂 本地视频文件")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "你好！我是你的视频笔记助手。请发送一个视频链接，或者直接上传视频文件，我帮你生成 Word 笔记。"}
    ]

# Display Chat Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# File Uploader in Sidebar (as chat usually doesn't handle heavy file uploads gracefully inline)
with st.sidebar:
    uploaded_file = st.file_uploader("📂 上传本地视频", type=["mp4", "mov", "avi", "mkv"])
    if uploaded_file:
        # Save to temp
        temp_dir = os.path.join(os.getcwd(), "temp", "uploads")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Inject as a user message if not already added
        if not any(m["content"] == f"已上传文件: {uploaded_file.name}" for m in st.session_state.messages):
             st.session_state.messages.append({"role": "user", "content": f"已上传文件: {uploaded_file.name}"})
             st.session_state.processing_file = temp_path
             st.rerun()

def is_url(text):
    """Simple check if input is a URL"""
    return re.match(r'^https?://', text.strip())

def search_videos(query):
    """Search for videos using DuckDuckGo"""
    with st.chat_message("assistant"):
        with st.status(f"🔍 正在搜索相关视频: {query}...", expanded=True):
            try:
                results = DDGS().videos(query, max_results=5)
                return results
            except Exception as e:
                st.error(f"搜索失败: {e}")
                return []

def run_workflow(input_source, source_type, api_key):
    """Executes the LangGraph workflow and updates UI"""
    
    if not api_key:
        with st.chat_message("assistant"):
            st.error("❌ 未检测到 API Key。请检查 .env 文件配置。")
        return

    # Use a status container for the progress
    with st.chat_message("assistant"):
        status_container = st.status("🚀 智能体正在初始化...", expanded=True)
        progress_bar = st.progress(0)
        
        try:
            app_graph = build_graph()
            
            initial_state = {
                "input_source": input_source,
                "source_type": source_type,
                "errors": [],
                "metadata": {},
                "screenshots": {}
            }
            
            status_container.write("🔄 正在连接工作流...")
            events = app_graph.stream(initial_state)
            final_state = None
            
            # Simulated steps for progress bar
            steps = {
                "classifier": 10,
                "downloader": 40,
                "processor": 60,
                "analyzer": 90,
                "generator": 100
            }
            
            status_container.update(label="🚀 正在全速处理中...", state="running")

            for event in events:
                node_name = list(event.keys())[0]
                state_update = event[node_name]
                
                # Update progress
                if node_name in steps:
                    progress_bar.progress(steps[node_name])

                # Updates based on Node
                if node_name == "classifier":
                    platform = state_update.get("platform", "unknown")
                    status_container.write(f"🕵️ [1/5] 识别到平台: **{platform}** (准备下载...)")
                    status_container.update(label="📥 正在下载视频资源...", state="running")
                    
                elif node_name == "downloader":
                    title = state_update.get("metadata", {}).get("title", "Video")
                    status_container.write(f"📥 [2/5] 视频下载完成: **{title}**")
                    status_container.update(label="🖼️ 正在提取关键帧...", state="running")
                    
                elif node_name == "processor":
                    count = len(state_update.get("screenshots", {}))
                    status_container.write(f"🖼️ [3/5] 关键帧提取: **{count} 张**")
                    status_container.write("🧠 [4/5] 正在进行 AI 多模态深度分析 (这可能需要 1-2 分钟)...")
                    status_container.update(label="🧠 AI 正在思考中...", state="running")
                    
                elif node_name == "analyzer":
                    status_container.write("🧠 [4/5] AI 分析完成！")
                    status_container.update(label="📝 正在生成 Word 文档...", state="running")
                    
                elif node_name == "generator":
                    final_state = state_update
                    status_container.write("📝 [5/5] 文档生成完毕")
                    progress_bar.progress(100)

            # Final Result processing
            status_container.update(label="✅ 任务完成！", state="complete", expanded=False)
            
            if final_state and final_state.get("doc_path"):
                doc_path = final_state["doc_path"]
                filename = os.path.basename(doc_path)
                
                # Read file for download
                with open(doc_path, "rb") as f:
                    file_data = f.read()
                    
                st.success(f"🎉 笔记已生成：**{filename}**")
                
                # Show Download Button
                st.download_button(
                    label="📥 点击下载 Word 笔记 (.docx)",
                    data=file_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary"
                )
                
                # Save to history so it persists
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"✅ 任务完成！笔记已生成：**{filename}**"
                })
            else:
                err_msg = "任务处理中遇到问题，未能生成文档。"
                if final_state and final_state.get("errors"):
                    err_msg += f"\n错误信息: {final_state['errors']}"
                status_container.update(label="❌ 任务失败", state="error")
                st.error(err_msg)
                st.session_state.messages.append({"role": "assistant", "content": err_msg})

        except Exception as e:
            status_container.update(label="❌ 系统错误", state="error")
            st.error(f"发生系统错误: {str(e)}")


# 1. Handle File Upload Trigger
if "processing_file" in st.session_state:
    file_path = st.session_state.processing_file
    del st.session_state.processing_file # consume it immediately
    run_workflow(file_path, "local", api_key)

# 2. Handle Chat Input Trigger
if prompt := st.chat_input("请输入视频链接 或 搜索内容..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Decision Logic
    if is_url(prompt):
        run_workflow(prompt, "url", api_key)
    else:
        # Search Mode
        results = search_videos(prompt)
        if results:
            st.session_state.messages.append({"role": "assistant", "content": f"为您找到关于“{prompt}”的视频，请点击选择进行分析："})
            with st.chat_message("assistant"):
                st.write(f"为您找到关于“**{prompt}**”的视频，请点击解析：")
                for v in results:
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        # Sometimes image is empty
                        if v.get('images'):
                            st.image(v['images']['small'], width=120)
                    with col2:
                        st.markdown(f"**{v['title']}**")
                        st.caption(f"来源: {v['publisher']} | 时长: {v['duration']}")
                        if st.button("开始分析", key=v['content']):
                            # This button click won't work perfectly in nested loop without rerun logic
                            # Streamlit buttons in loops need callback usually
                            # But for simplicity, we set session state and rerun
                            st.session_state.processing_url = v['content']
                            st.rerun()
        else:
            with st.chat_message("assistant"):
                st.warning("未找到相关视频，请尝试更具体的关键词。")

# 3. Handle Search Selection Trigger
if "processing_url" in st.session_state:
    url = st.session_state.processing_url
    del st.session_state.processing_url
    
    # Add a message to show what was selected
    st.session_state.messages.append({"role": "user", "content": f"开始分析视频: {url}"})
    # Force rerun to show the new message then run workflow
    # Actually, running workflow immediately is better UX
    run_workflow(url, "url", api_key)
