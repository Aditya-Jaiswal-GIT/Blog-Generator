from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from state import BlogState
from agent import research_node, writer_node, editor_node

APPROVAL_WORDS = {'y', 'yes', 'yess', 'approved', 'approve', 'finish', 'processed', 'ok', 'done'}

# ---------------------------------------------------------
# Routing Logic
# ---------------------------------------------------------
def route_after_human_review(state: BlogState):
    # If the human approved it during the interrupt, we finish.
    if state.get("is_approved"):
        return END
    # If rejected, route back to the researcher to start the cycle over
    return "research_node"

# ---------------------------------------------------------
# Graph Construction
# ---------------------------------------------------------
builder = StateGraph(BlogState)

# Add our three AI roles
builder.add_node("research_node", research_node)
builder.add_node("writer_node", writer_node)
builder.add_node("editor_node", editor_node)

# Define the sequential pipeline
builder.add_edge(START, "research_node")
builder.add_edge("research_node", "writer_node")
builder.add_edge("writer_node", "editor_node")

# Conditional edge evaluates the state AFTER the human interacts with it
builder.add_conditional_edges("editor_node", route_after_human_review)

# Compile with Checkpointer (Interrupt after the editor generates its critique)
memory = MemorySaver()
app = builder.compile(
    checkpointer=memory,
    interrupt_after=["editor_node"]
)


def create_config(thread_id: str = "multi_agent_blog_1"):
    return {"configurable": {"thread_id": thread_id}}


def run_to_next_interrupt(initial_state, config):
    for event in app.stream(initial_state, config=config):
        pass


def resume_workflow(config):
    for event in app.stream(None, config=config):
        pass


def get_workflow_snapshot(config):
    return app.get_state(config)


def apply_review(config, is_approved: bool, human_feedback: str = ""):
    app.update_state(config, {"is_approved": is_approved, "human_feedback": human_feedback})

# ---------------------------------------------------------
# Execution Loop (Human-in-the-Loop Interface)
# ---------------------------------------------------------
if __name__ == "__main__":
    config = create_config()
    
    topic = input("Enter the topic for your blog post: ")
    print(f"\n--- Starting Multi-Agent Blog Workflow ---")
    
    # Initialize the graph state
    initial_state = {
        "topic": topic,
        "human_feedback": "",
        "is_approved": False
    }
    
    # 1. Start execution (Will run Research -> Writer -> Editor -> PAUSE)
    run_to_next_interrupt(initial_state, config)

    # 2. Continuous loop to handle human interactions
    while True:
        snapshot = app.get_state(config)
        
        # If there is no 'next' node, the graph has reached END
        if not snapshot.next:
            print("\n🎉 Workflow completed successfully!")
            print("\n=== FINAL APPROVED BLOG POST ===")
            print(snapshot.values.get("article"))
            break

        state = snapshot.values
        
        # Display the Writer's work and the Editor's critique
        print("\n" + "="*60)
        print("📝 ARTICLE DRAFT READY FOR HUMAN REVIEW")
        print("="*60)
        print(state["article"])
        print("\n" + "-"*60)
        print("🤖 AI EDITOR'S CRITIQUE:")
        print("-"*60)
        print(state["editor_feedback"])
        print("="*60)
            
        user_input = input("\nApprove this draft? (e.g., y, yes, approved, finish, processed): ")
        
        # Define a list of acceptable approval words
        # 3. Update the graph state based on your decision
        if user_input.strip().lower() in APPROVAL_WORDS:
            apply_review(config, True, "")
        else:
            print("\nRouting back to the Research & Writing team...")
            feedback = input("Provide instructions for the revision: ")
            apply_review(config, False, feedback)

        # 4. Passing None resumes execution, triggering the conditional router
        resume_workflow(config)