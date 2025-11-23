import os
import sys
import re
import yaml
import streamlit as st
from crewai import Crew, Agent, Task
from langchain_openai import ChatOpenAI
from . import levels  # Ensure levels.py is in the same directory

# 🔧 Base paths & Imports
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

# Import RAG builder
from ai_hint_project.tools.rag_tool import build_rag_tool

print("✅ crew.py loaded!")

# ---------------------------------------------------------
# 1. SETUP & CONFIG
# ---------------------------------------------------------

# Retrieve API Key
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    st.error("⚠️ OPENAI_API_KEY missing in secrets.toml")
    st.stop()


def get_llm():
    return ChatOpenAI(
        model="gpt-5-mini",  # ✅ Using preferred model
        api_key=OPENAI_API_KEY,
        temperature=0.7,
    )


# ✅ Build RAG tool (Loaded once at startup)
rag_folder = os.path.join(base_dir, "baeldung_scraper")
rag_tool, _ = build_rag_tool(
    index_path=os.path.join(rag_folder, "baeldung_scraper"),
    chunks_path=os.path.join(rag_folder, "chunks.json")
)


# 📦 Load YAML Helper
def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)


# 🧹 Response Cleaner
def format_response(raw_text):
    # Remove <think> tags (common in reasoning models)
    cleaned = re.sub(r"<think>.*?</think>\n?", "", str(raw_text), flags=re.DOTALL)

    # Normalize code blocks if the model lazily used indentation
    if "public static" in cleaned or "def " in cleaned:
        cleaned = re.sub(r"(?:\n\s{4,}.*)+", lambda m: f"\n```java\n{m.group(0)}\n```", cleaned)

    return cleaned.strip()


# 🧠 Helper to check chat mode
def is_chat():
    return st.session_state.get('chat_mode', False)


# ---------------------------------------------------------
# 2. CREW EXECUTION
# ---------------------------------------------------------

def create_crew(persona: str, tutoring_context: str, proficiency: str = "Beginner"):
    """
    Creates the AI Tutor Crew with Adaptive Scaffolding + STRICT Chat Control.
    """
    print(f"✅ create_crew() called | Persona: {persona} | Proficiency: {proficiency}")

    current_dir = os.path.dirname(__file__)
    agents_config = load_yaml(os.path.join(current_dir, 'config/agents.yaml'))
    tasks_config = load_yaml(os.path.join(current_dir, 'config/tasks.yaml'))

    agent_cfg = agents_config['agents'].get(persona)
    if not agent_cfg:
        raise ValueError(f"Unknown persona: {persona}")

    # ---------------------------------------------------------
    # 🧠 ADAPTIVE SCAFFOLDING + CHAT CONTROL RULES
    # ---------------------------------------------------------

    # Core Rules that apply to EVERYONE (Prevents endless chats)
    core_rules = """
    CRITICAL CHAT RULES:
    1. KEEP IT SHORT: Max 3-4 sentences. No walls of text.
    2. STEP-BY-STEP: Do not give the full solution. Guide them one logic block at a time.
    3. THE "👉" RULE: Every response MUST end with a specific, focused question to prompt the user's next action.
    """

    if proficiency == "Beginner":
        scaffolding_instruction = f"""
        {core_rules}
        [MODE: BEGINNER]
        1. Use the "Step X —" format explicitly.
        2. Explain keywords (like 'void', 'public') simply.
        3. If they fail twice, offer a fill-in-the-blank snippet.
        4. Tone: Highly encouraging.
        """
    elif proficiency == "Intermediate":
        scaffolding_instruction = f"""
        {core_rules}
        [MODE: INTERMEDIATE]
        1. Focus on Logic and Data Flow.
        2. Do NOT explain basic syntax unless asked.
        3. Ask Socratic questions (e.g., "What does this loop condition imply?").
        4. Tone: Professional partner.
        """
    else:  # Advanced
        scaffolding_instruction = f"""
        {core_rules}
        [MODE: ADVANCED]
        1. Critique code efficiency (Big O) and cleanliness.
        2. Be concise and technical.
        3. Challenge them to optimize.
        """

    # ---------------------------------------------------------
    # 📚 RAG & CONTEXT ASSEMBLY
    # ---------------------------------------------------------

    rag_context = rag_tool(tutoring_context)

    full_query_context = f"""
    SYSTEM INSTRUCTIONS:
    {scaffolding_instruction}

    USER QUERY / CONTEXT:
    {tutoring_context}

    RELEVANT DOCUMENTATION:
    {rag_context}
    """

    # ---------------------------------------------------------
    # 🤖 AGENT & TASK SETUP (Standard)
    # ---------------------------------------------------------

    llm = get_llm()

    agent = Agent(
        role=agent_cfg["role"],
        goal=agent_cfg["goal"],
        backstory=agent_cfg["backstory"],
        level=agent_cfg.get("level", "beginner"),
        verbose=False,
        llm=llm
    )

    task_type = "guided_learning" if is_chat() else "explainer"
    task_template = tasks_config['tasks'][task_type]

    task = Task(
        name=task_template['name'],
        description=task_template['description'].format(query=full_query_context),
        expected_output=task_template['expected_output'],
        agent=agent
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff()

    try:
        levels.update_level(persona)
    except:
        pass

    if result.tasks_output:
        cleaned_content = format_response(result.tasks_output[0].raw)
    else:
        cleaned_content = format_response(str(result))

    return cleaned_content