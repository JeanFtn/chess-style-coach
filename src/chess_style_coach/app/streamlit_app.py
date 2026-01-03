import sys
import asyncio

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


import streamlit as st

from chess_style_coach.app.chat_core import ChatRequest, ChatMemory, generate_answer

st.set_page_config(page_title="ChessGPT", page_icon="♟️")

st.title("♟️ ChessGPT")
st.caption("Prototype : Stockfish + explications pédagogiques (sans API LLM).")

# Mémoire de conversation côté UI
if "messages" not in st.session_state:
    st.session_state.messages = []

if "memory" not in st.session_state:
    st.session_state.memory = ChatMemory()

with st.sidebar:
    st.header("Paramètres")
    mode = st.selectbox("Mode de réponse", ["short", "detailed"], index=1)
    depth = st.number_input("Profondeur (depth)", min_value=6, max_value=24, value=14, step=1)
    multipv = st.number_input("Coups candidats (MultiPV)", min_value=1, max_value=6, value=3, step=1)
    st.markdown("---")
    st.markdown("**Entrée position**")
    fen = st.text_input("FEN", placeholder="Colle une FEN (ex: position de départ)")

st.subheader("Chat")

# Affichage de l’historique
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("Pose ta question (ex: Quel est le plan ici ?)")
if prompt:
    # 1) Affiche le message user
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2) Génère la réponse
    req = ChatRequest(
        question=prompt,
        fen=fen if fen.strip() else None,
        mode=mode,
        depth=int(depth),
        multipv=int(multipv),
    )

    with st.chat_message("assistant"):
        with st.spinner("Analyse en cours..."):
            answer, st.session_state.memory = generate_answer(req, st.session_state.memory)
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
