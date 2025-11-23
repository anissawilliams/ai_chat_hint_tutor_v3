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
# Import the Memory/Feedback system
from utils.data_collection import get_recent_feedback

print("✅ crew.py loaded!")

# ---------------------------------------------------------
# 1. SETUP & CONFIG
# ---------------------------------------------------------

try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    st.error("⚠️ OPENAI_API_KEY missing in secrets.toml")
    st.stop()


def get_llm():
    return ChatOpenAI(
        model="gpt-5-mini",  # Using your preferred model
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

    # Normalize code blocks
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
    Creates the AI Tutor Crew with DYNAMIC CODE AUDITING.
    """
    print(f"✅ create_crew() called | Persona: {persona} | Proficiency: {proficiency}")

    current_dir = os.path.dirname(__file__)
    agents_config = load_yaml(os.path.join(current_dir, 'config/agents.yaml'))
    tasks_config = load_yaml(os.path.join(current_dir, 'config/tasks.yaml'))

    agent_cfg = agents_config['agents'].get(persona)
    if not agent_cfg:
        raise ValueError(f"Unknown persona: {persona}")

    # ---------------------------------------------------------
    # 🧠 A. FETCH TEACHER FEEDBACK
    # ---------------------------------------------------------
    recent_critiques = get_recent_feedback(persona, limit=3)

    corrections_text = ""
    if recent_critiques:
        corrections_text = "\n🚨 [TEACHER FEEDBACK - OVERRIDE PREVIOUS RULES]:\n"
        for item in recent_critiques:
            corrections_text += f"- PREVIOUS MISTAKE: '{item.get('bad_response', '')[:50]}...'\n"
            corrections_text += f"  FIX: {item.get('critique', '')}\n"

    # ---------------------------------------------------------
    # 🧠 B. DYNAMIC SCAFFOLDING RULES
    # ---------------------------------------------------------

    core_rules = """
    CRITICAL CHAT RULES:
    1. SHORT & PUNCHY: Max 3 sentences.
    2. NO SPOILERS: Never write the full solution.
    3. THE "👉" RULE: End with a specific question/instruction.
    """

    if proficiency == "Beginner":
        scaffolding_instruction = f"""
        {core_rules}
        [MODE: BEGINNER - CODE AUDITOR]
        1. **ANALYZE INPUT FIRST**: Did the student write code?
           - IF YES: **Audit it like a compiler.** What is missing?
             * Example: If they wrote "public sum(int a, int b)", they missed the return type. Tell them: "You missed the return type before the name!"
             * Example: If they wrote "int sum()", they missed params. Tell them: "The parentheses are empty!"
             * **DO NOT** repeat generic concepts if they are already writing code. Fix their syntax specifically.
           - IF NO (Text only): Explain the next tiny step using your persona's metaphor.

        2. **BAN LIST**: Do NOT use keywords (int, void) in explanations unless correcting a specific error.
        3. **PROGRESSION**: If their line of code is correct, immediately say "Perfect" and ask for the next part (the body).
        """
    elif proficiency == "Intermediate":
        scaffolding_instruction = f"""
        {core_rules}
        [MODE: INTERMEDIATE]
        1. Focus on Logic.
        2. If code is provided, check for edge cases or logic errors, not just syntax.
        3. Ask Socratic questions.
        """
    else:  # Advanced
        scaffolding_instruction = f"""
        {core_rules}
        [MODE: ADVANCED]
        1. Critique efficiency and clean code.
        2. Be concise.
        """

    # ---------------------------------------------------------
    # 📚 C. CONTEXT ASSEMBLY
    # ---------------------------------------------------------

    rag_context = rag_tool(tutoring_context)

    full_query_context = f"""
    SYSTEM INSTRUCTIONS:
    {scaffolding_instruction}

    {corrections_text}

    USER QUERY / CONTEXT:
    {tutoring_context}

    RELEVANT DOCUMENTATION:
    {rag_context}
    """

    # ---------------------------------------------------------
    # 🤖 D. AGENT & TASK SETUP
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