"""Conexão com o Supabase e login.

Regra de segurança mais importante do app: cada usuário tem a SUA conexão,
guardada em st.session_state (individual por sessão do navegador).
NUNCA guarde a conexão em @st.cache_resource: esse cache é compartilhado entre
todos os usuários, e o próximo visitante herdaria o login do anterior.

O app usa a chave PUBLISHABLE. Depois do login, toda consulta vai ao banco com a
identidade do usuário, e as políticas de RLS decidem o que ele pode ver."""

import streamlit as st
import supabase
from postgrest.exceptions import APIError


def cliente():
    """A conexão desta sessão (criada na primeira vez)."""
    if "sb" not in st.session_state:
        st.session_state.sb = supabase.create_client(
            st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_PUBLISHABLE_KEY"])
    return st.session_state.sb


def usuario():
    """O usuário logado nesta sessão, ou None."""
    return st.session_state.get("usuario")


def consultar(consulta, padrao=None):
    """Executa uma consulta e mostra o erro na tela, em vez de quebrar o app."""
    try:
        return consulta.execute().data
    except APIError as erro:
        st.error(f"Erro do banco: {erro.message}")
    except Exception as erro:  # noqa: BLE001
        st.error(f"Erro: {erro}")
    return padrao if padrao is not None else []


def tela_login():
    """Abas de entrar e criar conta. Ao entrar, guarda o usuário na sessão."""
    st.title("📈 Monitor B3")
    st.caption("Previsões de retorno de ações da B3 e carteiras de estudo.")
    entrar, criar = st.tabs(["Entrar", "Criar conta"])

    with entrar:
        with st.form("entrar"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", type="primary"):
                try:
                    resp = cliente().auth.sign_in_with_password({"email": email, "password": senha})
                    st.session_state.usuario = resp.user
                    st.rerun()
                except Exception as erro:  # noqa: BLE001
                    st.error(f"Não foi possível entrar: {erro}")

    with criar:
        with st.form("criar"):
            nome = st.text_input("Nome")
            email = st.text_input("E-mail", key="email_novo")
            senha = st.text_input("Senha (mínimo 6 caracteres)", type="password", key="senha_nova")
            if st.form_submit_button("Criar conta", type="primary"):
                try:
                    # o trigger do banco lê "nome" para criar a linha em profiles
                    resp = cliente().auth.sign_up({"email": email, "password": senha,
                                                   "options": {"data": {"nome": nome}}})
                    if resp.session:                 # confirmação de e-mail desligada
                        st.session_state.usuario = resp.user
                        st.rerun()
                    else:
                        st.success("Conta criada. Confirme pelo link enviado ao seu e-mail e depois entre.")
                except Exception as erro:  # noqa: BLE001
                    st.error(f"Não foi possível criar a conta: {erro}")


def sair():
    try:
        cliente().auth.sign_out()
    finally:
        st.session_state.clear()
        st.rerun()


def perfil():
    """Linha do usuário logado na tabela profiles (nome e foto)."""
    linhas = consultar(cliente().table("profiles").select("nome, avatar_url")
                       .eq("id", usuario().id))
    return linhas[0] if linhas else {"nome": None, "avatar_url": None}


def percentual(valor) -> str:
    """0.0123 -> '1,23%' (padrão brasileiro)."""
    if valor is None:
        return "—"
    return f"{valor * 100:+.2f}%".replace(".", ",")
