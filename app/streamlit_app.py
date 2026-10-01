"""Monitor B3 — frontend em Streamlit.

Rodar na sua máquina (a partir da raiz do repositório):
    streamlit run app/streamlit_app.py
"""

import streamlit as st

from conexao import perfil, sair, tela_login, usuario

st.set_page_config(page_title="Monitor B3", page_icon="📈", layout="wide")

# --- sem login, só a tela de entrar / criar conta ---
if usuario() is None:
    tela_login()
    st.stop()

# --- barra lateral: foto, nome e botão de sair ---
dados = perfil()
with st.sidebar:
    if dados.get("avatar_url"):
        st.image(dados["avatar_url"], width=72)
    st.markdown(f"**{dados.get('nome') or usuario().email}**")
    if st.button("Sair", icon=":material/logout:"):
        sair()

# --- páginas ---
navegacao = st.navigation([
    st.Page("paginas/ranking.py", title="Ranking", icon=":material/leaderboard:", default=True),
    st.Page("paginas/acao.py", title="Ação", icon=":material/show_chart:"),
    st.Page("paginas/montar_carteira.py", title="Montar carteira", icon=":material/add_circle:"),
    st.Page("paginas/carteiras.py", title="Minhas carteiras", icon=":material/work:"),
    st.Page("paginas/modelo.py", title="Modelo", icon=":material/insights:"),
    st.Page("paginas/perfil.py", title="Meu perfil", icon=":material/person:"),
])
navegacao.run()

st.divider()
st.caption("Projeto educacional. As previsões não são recomendação de investimento.")
