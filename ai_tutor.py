import json
import os
from pathlib import Path

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
    return bool(_secret("GEMINI_API_KEY"))


def _knowledge_text():
    chunks = []
    if KNOWLEDGE_DIR.exists():
        for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
            try:
                content = path.read_text(encoding="utf-8")[:7000]
                chunks.append(f"## {path.stem}\n{content}")
            except Exception:
                continue
    return "\n\n".join(chunks)


def ask_tutor(question, context=None):
    key = _secret("GEMINI_API_KEY")
    if not key:
        return None, "AI Tutor is not configured yet. Add GEMINI_API_KEY to Streamlit secrets to enable it."

    model = _secret("GEMINI_MODEL", "gemini-2.5-flash")
    context = context or {}

    system = """You are TradeWar AI Tutor, an economics teacher and application guide inside TradeWar AI Simulator.
Explain economics in clear language suitable for students and researchers. Help users understand what the app is doing and how to use it.
Never invent data, coefficients, market observations, or app capabilities. Treat the app's statistical/economic models as the source of quantitative results; AI is only an explanation layer.
Distinguish observed data, model estimates, assumptions, scenarios and forecasts. Explain correlation versus causation and uncertainty when relevant.
Do not give personalized investment advice. If asked for an investment recommendation, explain the relevant concepts and limitations instead.
If the user asks about a value produced by the app, use the supplied APP CONTEXT and explain what that value means; do not fabricate missing values.
"""

    prompt = f"""APP CONTEXT:
{json.dumps(context, default=str, indent=2)}

KNOWLEDGE:
{_knowledge_text()}

QUESTION:
{question}"""

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.3,
                max_output_tokens=900,
            ),
        )
        text = getattr(response, "text", None)
        return text or "I received a response but could not extract the tutor text.", None
    except Exception as exc:
        message = str(exc)
        lowered = message.lower()
        if "429" in message or "quota" in lowered or "rate limit" in lowered:
            return None, "The Gemini free-tier quota/rate limit has been reached. Please try again later."
        if "api key" in lowered or "authentication" in lowered or "permission" in lowered:
            return None, "Gemini authentication failed. Check the GEMINI_API_KEY in Streamlit secrets."
        if "not found" in lowered or ("model" in lowered and "not found" in lowered):
            return None, f"Gemini model '{model}' was not found. Check GEMINI_MODEL in Streamlit secrets."
        return None, f"The Gemini AI Tutor encountered an error: {message}"


def render_ai_tutor(page, context=None, suggestions=None):
    context = dict(context or {})
    context.setdefault("page", page)
    suggestions = suggestions or [
        "Explain what this page is doing in simple terms.",
        "What should I look at first?",
        "What are the main limitations of this analysis?",
    ]

    input_key = f"tutor_input_{page}"
    answer_key = f"tutor_answer_{page}"
    error_key = f"tutor_error_{page}"

    with st.sidebar.expander("🤖 TradeWar AI Tutor", expanded=False):
        st.caption("Economics tutor + app guide. AI explains results; the app's models calculate them.")

        if not ai_configured():
            st.info("Tutor is ready in the UI but disabled until GEMINI_API_KEY is added to Streamlit secrets.")

        for i, suggestion in enumerate(suggestions[:3]):
            if st.button(suggestion, key=f"tutor_suggestion_{page}_{i}", use_container_width=True):
                st.session_state[input_key] = suggestion
                st.session_state.pop(answer_key, None)
                st.session_state.pop(error_key, None)
                st.rerun()

        st.text_area(
            "Ask a question",
            key=input_key,
            height=90,
            placeholder="e.g. What does this coefficient mean?",
        )

        if st.button("Ask Tutor", key=f"tutor_ask_{page}", type="primary", use_container_width=True):
            question = st.session_state.get(input_key, "").strip()
            if not question:
                st.session_state[error_key] = "Please enter a question first."
                st.session_state.pop(answer_key, None)
            else:
                with st.spinner("Tutor is thinking…"):
                    answer, error = ask_tutor(question, context)
                if error:
                    st.session_state[error_key] = error
                    st.session_state.pop(answer_key, None)
                else:
                    st.session_state[answer_key] = answer
                    st.session_state.pop(error_key, None)

        if st.session_state.get(error_key):
            st.warning(st.session_state[error_key])

        if st.session_state.get(answer_key):
            st.markdown("### 💡 Tutor")
            st.markdown(st.session_state[answer_key])

        st.caption("For sensitive or high-stakes decisions, verify results with primary sources and qualified professionals.")
