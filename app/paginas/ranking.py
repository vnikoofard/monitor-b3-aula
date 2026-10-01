"""Ranking do último pregão (view v_ranking_atual)."""

import pandas as pd
import streamlit as st

from conexao import cliente, consultar

st.title("Ranking do dia")

linhas = consultar(cliente().table("v_ranking_atual").select("*").order("posicao"))
if not linhas:
    st.info("Ainda não há previsões. Elas aparecem depois da primeira execução do pipeline.")
    st.stop()

df = pd.DataFrame(linhas)
data = pd.to_datetime(df["data_referencia"].iloc[0]).strftime("%d/%m/%Y")
st.caption(f"Pregão de {data} · retorno previsto para os próximos 5 pregões · "
           f"modelo {df['modelo_versao'].iloc[0]}")

col1, col2 = st.columns(2)
setor = col1.selectbox("Setor", ["Todos"] + sorted(df["setor"].unique()))
busca = col2.text_input("Buscar ticker").strip().upper()
if setor != "Todos":
    df = df[df["setor"] == setor]
if busca:
    df = df[df["ticker"].str.contains(busca)]

df["previsto_pct"] = df["retorno_previsto"] * 100
selecao = st.dataframe(
    df[["posicao", "ticker", "nome", "setor", "ultimo_preco", "previsto_pct"]],
    hide_index=True, width="stretch",
    on_select="rerun", selection_mode="single-row",
    column_config={
        "posicao": st.column_config.NumberColumn("#", width="small"),
        "ticker": "Ticker", "nome": "Empresa", "setor": "Setor",
        "ultimo_preco": st.column_config.NumberColumn("Último preço", format="R$ %.2f"),
        "previsto_pct": st.column_config.NumberColumn("Retorno previsto", format="%.2f%%"),
    },
)
st.caption("Clique numa linha para ver os detalhes da ação.")

if selecao.selection.rows:
    st.session_state.ticker = df.iloc[selecao.selection.rows[0]]["ticker"]
    st.switch_page("paginas/acao.py")
