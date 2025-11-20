import os
import sys
import re
import yaml
from openai import OpenAI
import streamlit as st
from crewai import Crew, Agent, Task
from ai_hint_project.tools.rag_tool import build_rag_tool
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEndpoint
import requests
from streamlit import session_state

from . import levels

print("✅ crew.py loaded!")

# 🔧 Base paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_dir)

import requests
import streamlit as st
import json

# Retrieve the OpenAI API key from Streamlit secrets
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Retrieve the OpenAI API key from Streamlit secrets
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]


def get_llm():
    return ChatOpenAI(
        model="gpt-5-mini",
        api_key=st.secrets["OPENAI_API_KEY"],
        temperature=0.7,
    )

llm = get_llm()
resp = llm.invoke("Say hello as a Java tutor.")
print(resp.content)


# Rest of your code stays the same...
# (persona_reactions, is_code_input, load_yaml, etc.)

# ✅ Build RAG tool
rag_folder = os.path.join(base_dir, "baeldung_scraper")
rag_tool, _ = build_rag_tool(
    index_path=os.path.join(rag_folder, "baeldung_scraper"),
    chunks_path=os.path.join(rag_folder, "chunks.json")
)

# 🎭 Persona reactions
persona_reactions = {
    "Batman": "Code received. Let's patch the vulnerability.",
    "Yoda": "Code, you have pasted. Analyze it, we must.",
    "Spider-Gwen": "Let's swing through this syntax.",
    "Shuri": "Let's scan it with Wakandan tech.",
    "Elsa": "Let me freeze the bugs and refactor.",
    "Wednesday Addams": "Let's dissect it like a corpse.",
    "Iron Man": "Let's run diagnostics and upgrade it.",
    "Nova": "Let's orbit through its logic.",
    "Zee": "Let's treat this like a boss fight.",
    "Sherlock Holmes": "Let's deduce its structure."
}


# 🧠 Detect code input
def is_code_input(text):
    code_patterns = [
        r"\bdef\b", r"\bclass\b", r"\bimport\b", r"\breturn\b",
        r"\bif\b\s*\(?.*?\)?\s*:", r"\bfor\b\s*\(?.*?\)?\s*:", r"\bwhile\b\s*\(?.*?\)?\s*:",
        r"\btry\b\s*:", r"\bexcept\b\s*:", r"\w+\s*=\s*.+", r"\w+\(.*?\)", r"{.*?}", r"<.*?>"
    ]
    return any(re.search(pattern, text) for pattern in code_patterns)

def is_chat():
    if st.session_state.get('chat_mode') == True:
        return True
    else:
        return False

# 📦 Load YAML
def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def format_response(raw_text):
    # Remove <think> tags
    cleaned = re.sub(r"<think>.*?</think>\n?", "", raw_text, flags=re.DOTALL)

    # Normalize code blocks (if model uses indentation instead of backticks)
    if "public static" in cleaned or "def " in cleaned:
        cleaned = re.sub(r"(?:\n\s{4,}.*)+", lambda m: f"\n```java\n{m.group(0)}\n```", cleaned)

    return cleaned.strip()


# 🚀 Crew creation
def create_crew(persona: str, tutoring_context: str):
    print(f"✅ create_crew() called with persona: {persona}")

    base_dir = os.path.dirname(__file__)
    agents_config = load_yaml(os.path.join(base_dir, 'config/agents.yaml'))
    tasks_config = load_yaml(os.path.join(base_dir, 'config/tasks.yaml'))

    agent_cfg = agents_config['agents'].get(persona)
    if not agent_cfg:
        raise ValueError(f"Unknown persona: {persona}")

    # Get the LLM instance (ChatOpenAI with GPT-5-mini)

    llm = get_llm()
    agent = Agent(
        role=agent_cfg["role"],
        goal=agent_cfg["goal"],
        backstory=agent_cfg["backstory"],
        level=agent_cfg.get("level", "beginner"),
        verbose=False,
        llm=llm
    )

    # Use tutoring context instead of just persona reaction
    task_description = f"{tutoring_context}"

    # Get RAG context for the question
    rag_context = rag_tool(tutoring_context)

    # Determine which task template to use
    task_type = "guided_learning" if is_chat() else "explainer"
    task_template = tasks_config['tasks'][task_type]

    # Create the task with tutoring + RAG context
    task = Task(
        name=task_template['name'],
        description=task_template['description'].format(
            query=f"{task_description}\n\nRelevant context:\n{rag_context}"),
        expected_output=task_template['expected_output'],
        agent=agent
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=True)
    result = crew.kickoff()
    levels.update_level(persona)
    cleaned_content = format_response(result.tasks_output[0].raw)

    return cleaned_content
