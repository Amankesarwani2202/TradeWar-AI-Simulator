import json
import os
from pathlib import Path

import requests
import streamlit as st

KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"


def _secret(name, default=None):
    try:
        value = st.secrets.get(name)
        if value:
            return value
    except Exception:
        pass
    return os.getenv(name, default)


def ai_configured():
    return bool(_secret("OPENAI_API_KEY"))


def _knowledge_text():
    chunks = []
    if KNOWLEDGE_DIR.exists():
        for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
            try:
                chunks.append(f"## {path.stem}\n{path.read_text(encoding='utf-8')[:7000]}")
            except Exception:
                continue
    return "\n\n".join(chunks)


def ask_tutor(question, context=None):
    key = _secret("OPENAI_API_KEY")
    if not key:
        return None, "AI Tutor is not configured yet. Add OPENAI_API_KEY to Streamlit secrets to enable it."
    model = _secret("OPENAI_MODEL", "gpt-5.6-luna")
    endpoint = _secret("OPENAI_RESPONSES_URL", "https://api.openai.com/v1/responses")
    context = context or {}
    system = """You are TradeWar AI Tutor, an economics teacher and application guide inside TradeWar AI Simulator.
Explain economics in clear language suitable for students and researchers. Help users understand what the app is doing and how to use it.
Never invent data, coefficients, market observations, or app capabilities. Treat the app's statistical/economic models as the source of quantitative results; AI is only an explanation layer.
Distinguish observed data, model estimates, assumptions, scenarios and forecasts. Explain correlation versus causation and uncertainty when relevant.
Do not give personalized investment advice. If asked for an investment recommendation, explain the relevant concepts and limitations instead.
"""
    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": system},
            {"role": "user", "content": f"APP CONTEXT:\n{json.dumps(context, default=str, indent=2)}\n\nKNOWLEDGE:\n{_knowledge_text()}\n\nQUESTION:\n{question}"},
        ],
        "max_output_tokens": 900,
    }
    try:
        response = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload,
            timeout=45,
        )
        response.raise_for_status()
        data = response.json()
        text = data.get("output_text")
        if not text:
            for item in data.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") in {"output_text", "text"} and content.get("text"):
                        text = content["text"]
                        break
                if text:
                    break
        return text or "I received a response but could not extract the tutor text.", None
    except requests.RequestException as exc:
        return None, f"The AI Tutor could not reach the configured provider: {exc}"
    except Exception as exc:
        return None, f"The AI Tutor encountered an unexpected error: {exc}"


def render_ai_tutor(page, context=None, suggestions=None):
    context = dict(context or {})
    context.setdefault("page", page)
    suggestions = suggestions or [
        "Explain what this page is doing in simple terms.",
        "What should I look at first?",
        "What are the main limitations of this analysis?",
    ]
    with st.sidebar.expander("🤖 TradeWar AI Tutor", expanded=False):
        st.caption("Economics tutor + app guide. AI explains results; the app's models calculate them.")
        if not ai_configured():
            st.info("Tutor is ready in the UI but disabled until OPENAI_API_KEY is added to Streamlit secrets.")
        for i, suggestion in enumerate(suggestions[:3]):
            if st.button(suggestion, key=f"tutor_suggestion_{page}_{i}", use_container_width=True):
                st.session_state["tutor_question"] = suggestion
        question = st.text_area("Ask a question", value=st.session_state.pop("tutor_question", ""), height=90, placeholder="e.g. What does this coefficient mean?")
        if st.button("Ask Tutor", type="primary", use_container_width=True) and question.strip():
            with st.spinner("Tutor is thinking…"):
                answer, error = ask_tutor(question.strip(), context)
            if error:
                st.warning(error)
            elif answer:
                st.markdown(answer)
        st.caption("For sensitive or high-stakes decisions, verify results with primary sources and qualified professionals.")
