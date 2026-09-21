import json

import streamlit as st
import streamlit.components.v1 as components

from Agent import Agent
from schema import parse_sql_agent_response
from toolskit import tools


MODEL = "openai/gpt-oss-20b"

AGENT_ROLE = (
    "Answer questions about the SQLite used-cars database. "
    "First call get_database_schema, then generate one read-only SELECT "
    "or WITH query, execute it with execute_sql_query, and explain the results. "
    "Return one valid JSON object with exactly these fields: status, sql_query, "
    "columns, rows, and final_answer. Use success for matching database data. "
    "Use no_results when the question is related but no records match; leave "
    "columns and rows empty and put only a concise answer in final_answer. "
    "If the question is naturally yes/no, answer Yes or No. Use out_of_scope "
    "for unrelated questions; leave sql_query, columns, and rows empty and say "
    "you can only answer questions about the SQLite used-cars database. "
    "Do not use Markdown fences or add text outside JSON."
)


st.set_page_config(
    page_title="Roadwise SQL Agent",
    page_icon="▦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #f2f1ed;
        --muted: #9b9e99;
        --line: #30322f;
        --paper: #111210;
        --panel: #1a1c1a;
        --panel-soft: #161816;
        --accent: #e5a07b;
        --accent-dark: #f0b18f;
    }
    .stApp { background: #111210 !important; color: var(--ink); }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { max-width: 1080px; padding: 1rem 2rem 6rem; }
    [data-testid="stSidebar"] { background: #090a09; border-right: 1px solid #292b29; }
    [data-testid="stSidebar"] > div:first-child { padding: 1.1rem .9rem; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color: var(--muted); }
    [data-testid="stSidebar"] hr { border-color: #30322f; }
    [data-testid="stChatMessage"] { background: transparent; padding: .75rem 0; }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] { color: var(--ink); }
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] form,
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInput"] button {
        background: #1a1c1a !important;
        border-color: #3a3d39 !important;
        color: var(--ink) !important;
    }
    [data-testid="stChatInput"] textarea { caret-color: var(--accent); }
    [data-testid="stChatInput"] textarea::placeholder { color: #858984 !important; }
    [data-testid="stChatInput"] button:hover { background: #272a26 !important; border-color: var(--accent) !important; }
    [data-testid="stTabs"] button { color: var(--muted); }
    [data-testid="stTabs"] button[aria-selected="true"] { color: var(--accent); }
    [data-testid="stDataFrame"] { border: 1px solid var(--line); background: #171917; }
    .brand { display: flex; align-items: center; gap: .6rem; color: var(--ink); font: 700 1rem Georgia, serif; padding: .3rem .2rem 1.4rem; }
    .brand-mark { width: 25px; height: 25px; display: grid; place-items: center; background: var(--accent); color: #28201b; border-radius: 7px; font: 800 .75rem system-ui; }
    .nav-label { color: #777c76; font-size: .67rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; margin: 1.2rem .25rem .45rem; }
    .topline { display:flex; justify-content:space-between; align-items:center; color:var(--muted); font-size:.78rem; margin: .2rem 0 2.8rem; }
    .topline strong { color:var(--ink); font-size:.86rem; }
    .hero {
        text-align: center;
        padding: 1rem 0 1.2rem;
        margin: 0 auto 1.1rem;
        max-width: 700px;
    }
    .eyebrow { color: var(--accent); font-size: .7rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
    .hero h1 {
        color: var(--ink);
        font-family: Georgia, serif;
        font-size: clamp(2rem, 5vw, 3.25rem);
        line-height: .98;
        margin: .45rem 0 .7rem;
    }
    .hero p { color: var(--muted); max-width: 560px; margin: 0 auto; font-size:.9rem; }
    .section-label { color: var(--muted); font-size: .67rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; margin: 1.5rem 0 .4rem; }
    .answer {
        background: var(--panel);
        border: 1px solid var(--line);
        border-left: 3px solid var(--accent);
        padding: .95rem 1.1rem .8rem;
        margin: .35rem 0 .5rem;
        border-radius: 4px;
    }
    .answer-label {
        color: var(--accent);
        font-size: .7rem;
        font-weight: 800;
        letter-spacing: .12em;
        text-transform: uppercase;
        margin-bottom: .35rem;
    }
    div[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p { line-height: 1.55; }
    button[kind="secondary"] { border-color: var(--line); color: var(--ink); background: var(--panel-soft); }
    button[kind="secondary"]:hover { border-color: var(--accent); color: var(--accent); }
    [data-testid="stExpander"] { background: var(--panel-soft); border-color: var(--line); }
    [data-testid="stAlert"] { background: var(--panel) !important; border-color: var(--line) !important; }
    [data-testid="stVerticalBlock"]:has(> [data-testid="stChatInput"]) { background: transparent; }
    </style>
    """,
    unsafe_allow_html=True,
)


def copy_control(value, key):
    components.html(
        f"""
        <style>
            body {{ margin: 0; background: transparent; }}
            button {{
                border: 1px solid #454844; background: #292b28; color: #a7aaa5;
                border-radius: 4px; padding: 4px 9px; cursor: pointer;
                font: 12px system-ui, sans-serif;
            }}
            button:hover {{ border-color: #e5a07b; color: #f0b18f; }}
        </style>
        <button id="copy-{key}" title="Copy to clipboard">⧉ Copy</button>
        <script>
            const button = document.getElementById("copy-{key}");
            button.onclick = async () => {{
                await navigator.clipboard.writeText({json.dumps(value)});
                button.textContent = "Copied";
                setTimeout(() => button.textContent = "⧉ Copy", 1200);
            }};
        </script>
        """,
        height=32,
    )


def render_user_message(text, key):
    st.markdown('<div class="section-label">Question</div>', unsafe_allow_html=True)
    st.write(text)
    copy_control(text, f"question-{key}")


def render_payload(payload, key):
    if payload["status"] == "error":
        st.error(payload["message"])
        return

    if payload["status"] == "out_of_scope":
        st.info(payload["final_answer"])
        copy_control(payload["final_answer"], f"answer-{key}")
        return

    if payload["status"] == "no_results":
        st.info(payload["final_answer"] or "Can you explain what you're looking for?")
        copy_control(payload["final_answer"], f"answer-{key}")
        return

    st.markdown(
        '<div class="answer"><div class="answer-label">Answer</div></div>',
        unsafe_allow_html=True,
    )
    st.write(payload["final_answer"])
    copy_control(payload["final_answer"], f"answer-{key}")
    tab_table, tab_sql, tab_json = st.tabs(["Results", "SQL query", "JSON"])
    with tab_table:
        st.dataframe(payload["rows"], use_container_width=True, hide_index=True)
    with tab_sql:
        st.code(payload["sql_query"], language="sql")
    with tab_json:
        st.json(payload)

with st.sidebar:
    st.markdown(
        '<div class="brand"><span class="brand-mark">R</span><span>Roadwise</span></div>',
        unsafe_allow_html=True,
    )
    if st.button("＋  New chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown('<div class="nav-label">Workspace</div>', unsafe_allow_html=True)
    st.caption("◌  Used-cars analyst")
    st.caption("▦  SQLite / read-only")
    st.markdown('<div class="nav-label">Workspace</div>', unsafe_allow_html=True)
    st.caption("Groq · GPT-OSS 20B")
    st.caption("Schema-aware · read-only")
    st.markdown('<div class="nav-label">Session</div>', unsafe_allow_html=True)
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.caption("Local workspace")
    st.caption("Data stays in your SQLite database.")

st.markdown(
    """
    <div class="topline"><span>SQL agent</span><strong>Used cars · SQLite</strong></div>
    <div class="hero">
        <div class="eyebrow">Local data workspace</div>
        <h1>What would you like to know?</h1>
        <p>Ask naturally. Roadwise checks the schema, writes a read-only query, and brings back the result.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown('<div class="section-label">Start with a question</div>', unsafe_allow_html=True)
    st.caption("Use a starter or write your own question below.")
    starter_one, starter_two = st.columns(2)
    starter_three, starter_four = st.columns(2)
    quick_prompts = [
        (starter_one, "Which locations have the most listings?"),
        (starter_two, "What are the most fuel-efficient cars?"),
        (starter_three, "What is the average price by fuel type?"),
        (starter_four, "Show the five cheapest automatic cars."),
    ]
    for column, question in quick_prompts:
        with column:
            if st.button(question, key=f"quick-{question}", use_container_width=True):
                st.session_state.quick_prompt = question

for message in st.session_state.messages:
    message_id = message.get("id", id(message))
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            render_user_message(message["content"], message_id)
        else:
            render_payload(message["payload"], message_id)

prompt = st.chat_input("Ask about price, mileage, location, year, or listings...")
if not prompt:
    prompt = st.session_state.pop("quick_prompt", None)

if prompt:
    message_id = len(st.session_state.messages)
    st.session_state.messages.append({"role": "user", "content": prompt, "id": message_id})
    with st.chat_message("user"):
        render_user_message(prompt, message_id)

    with st.chat_message("assistant"):
        with st.spinner("Checking the data..."):
            try:
                agent = Agent(
                    name="SQL Agent",
                    role=AGENT_ROLE,
                    model=MODEL,
                    toolkit=tools[:2],
                )
                response_text = agent.invoke(prompt)
                payload = parse_sql_agent_response(response_text)
            except Exception as error:
                payload = {
                    "status": "error",
                    "message": f"The agent could not complete the request: {error}",
                }

        response_id = message_id + 1
        st.session_state.messages.append({"role": "assistant", "payload": payload, "id": response_id})
        render_payload(payload, response_id)
