from langgraph.graph import StateGraph, END
from graph.state import AgentState

# Import nodes
from graph.nodes.classifier import classify_input
from graph.nodes.downloader import download_video
from graph.nodes.processor import process_video
from graph.nodes.analyzer import analyze_video
from graph.nodes.generator import generate_document

def route_input(state: AgentState):
    """
    Router determines whether to go to Downloader (URL) or directly to Processor (Local File).
    """
    if state["source_type"] == "url":
        return "downloader"
    return "processor"

def build_graph():
    """
    Constructs the LangGraph workflow.
    """
    workflow = StateGraph(AgentState)
    
    # 1. Add Nodes
    workflow.add_node("classifier", classify_input)
    workflow.add_node("downloader", download_video)
    workflow.add_node("processor", process_video)
    workflow.add_node("analyzer", analyze_video)
    workflow.add_node("generator", generate_document)
    
    # 2. Add Edges
    
    # Start -> Classifier
    workflow.set_entry_point("classifier")
    
    # Classifier -> (Router) -> Downloader OR Processor
    workflow.add_conditional_edges(
        "classifier",
        route_input,
        {
            "downloader": "downloader",
            "processor": "processor"
        }
    )
    
    # Downloader -> Processor
    workflow.add_edge("downloader", "processor")
    
    # Processor -> Analyzer
    workflow.add_edge("processor", "analyzer")
    
    # Analyzer -> Generator
    workflow.add_edge("analyzer", "generator")
    
    # Generator -> End
    workflow.add_edge("generator", END)
    
    # 3. Compile
    return workflow.compile()