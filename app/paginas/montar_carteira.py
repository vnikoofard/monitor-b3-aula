"""Monta uma carteira chamando a função montar_carteira do banco."""

import streamlit as st
from postgrest.exceptions import APIError

from conexao import cliente

st.title("Montar carteira")
st.write("A carteira recebe as ações com maior retorno previsto no último pregão, com pesos iguais.")

with st.form("nova_carteira"):
    n = st.number_input("Número de ações", min_value=1, max_value=20, value=5, step=1)
    nome = st.text_input("Nome da carteira (opcional)")
    enviar = st.form_submit_button("Gerar carteira", type="primary")

if enviar:
    try:
        # a regra de negócio está no banco: o app só chama a função (RPC)
        carteira_id = cliente().rpc("montar_carteira",
                                    {"p_n": int(n), "p_nome": nome.strip() or None}).execute().data
        st.success(f"Carteira {carteira_id} criada.")
        st.session_state.carteira_aberta = carteira_id
        st.switch_page("paginas/carteiras.py")
    except APIError as erro:
        st.error(erro.message)
