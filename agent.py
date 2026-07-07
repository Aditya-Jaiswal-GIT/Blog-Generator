from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from state import BlogState

# Initialize the local LLM (Ollama)
llm = ChatOllama(model="gemma4:31b-cloud", temperature=0.7)

def research_node(state: BlogState):
    topic = state.get("topic")
    human_feedback = state.get("human_feedback", "")
    
    print("\n[AI Researcher] Gathering facts and structuring insights...")
    prompt = f"Conduct research and outline 3-4 key talking points for a blog post about: {topic}."
    
    if human_feedback:
        prompt += f"\n\nIncorporate this human feedback into your revised research: {human_feedback}"
        
    response = llm.invoke([HumanMessage(content=prompt)])
    return {
        "research_notes": response.content,
        "current_stage": "research"
    }

def writer_node(state: BlogState):
    topic = state.get("topic")
    research_notes = state.get("research_notes")
    
    print("\n[AI Writer] Drafting the blog post...")
    prompt = f"Write a full, engaging blog post about '{topic}' using exactly these research notes:\n\n{research_notes}"
        
    response = llm.invoke([HumanMessage(content=prompt)])
    return {
        "article": response.content,
        "current_stage": "writing"
    }

def editor_node(state: BlogState):
    article = state.get("article")
    
    print("\n[AI Editor]  . Critiquing draft for quality and tone...")
    prompt = f"Give mark xx/10 .You are a strict senior editor. Review the following blog post draft. Provide 2-3 specific points of constructive feedback on how to improve it. Do NOT rewrite the article, just provide the critique.\n\nDraft:\n{article} "
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return {
        "editor_feedback": response.content,
        "current_stage": "editing"
    }