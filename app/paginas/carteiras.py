"""Carteiras do usuário logado (view v_desempenho_carteiras + carteira_itens)."""

import altair as alt
import pandas as pd
import streamlit as st

from conexao import cliente, consultar, percentual

st.title("Minhas carteiras")

carteiras = consultar(cliente().table("v_desempenho_carteiras").select("*")
                      .order("carteira_id", desc=True))
if not carteiras:
    st.info("Você ainda não tem carteiras. Crie uma em **Montar carteira**.")
    st.stop()

for c in carteiras:
    with st.container(border=True):
        data = pd.to_datetime(c["data_referencia"]).strftime("%d/%m/%Y")
        topo, botao = st.columns([5, 1])
        topo.subheader(c["nome"])
        topo.caption(f"Pregão de {data} · {c['n_acoes']} ações")
        if botao.button("Excluir", key=f"excluir_{c['carteira_id']}", icon=":material/delete:"):
            consultar(cliente().table("carteiras").delete().eq("id", c["carteira_id"]))
            st.rerun()

        m1, m2 = st.columns(2)
        m1.metric("Retorno previsto", percentual(c["retorno_previsto"]))
        if c["concluida"]:
            m2.metric("Retorno realizado", percentual(c["retorno_realizado"]))
        else:
            m2.metric("Retorno realizado", "em andamento")

        aberta = st.session_state.get("carteira_aberta") == c["carteira_id"]
        with st.expander("Ações da carteira", expanded=aberta):
            itens = consultar(cliente().table("carteira_itens")
                              .select("ticker, peso, ativos(nome)")
                              .eq("carteira_id", c["carteira_id"]))
            if itens:
                df = pd.DataFrame([{"Ticker": i["ticker"], "Empresa": i["ativos"]["nome"],
                                    "Peso": float(i["peso"])} for i in itens])
                esquerda, direita = st.columns(2)
                esquerda.dataframe(df, hide_index=True, width="stretch",
                                   column_config={"Peso": st.column_config.NumberColumn(format="percent")})
                pizza = alt.Chart(df).mark_arc().encode(theta="Peso:Q", color="Ticker:N",
                                                        tooltip=["Ticker", "Empresa", "Peso"])
                direita.altair_chart(pizza, width="stretch")
