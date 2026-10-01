"""Detalhes de uma ação: gráfico de preços e histórico de previsões."""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from conexao import cliente, consultar, percentual

st.title("Ação")

# a lista de ações, com o nome do setor (JOIN pela chave estrangeira setor_id)
ativos = consultar(cliente().table("ativos").select("ticker, nome, setores(nome)")
                   .eq("ativo", True).order("ticker"))
if not ativos:
    st.stop()
tickers = [a["ticker"] for a in ativos]
inicial = tickers.index(st.session_state.get("ticker")) if st.session_state.get("ticker") in tickers else 0
ticker = st.selectbox("Ação", tickers, index=inicial)
st.session_state.ticker = ticker

ativo = next(a for a in ativos if a["ticker"] == ticker)
st.subheader(f"{ativo['nome']} · {ativo['setores']['nome']}")

# preços dos últimos 12 meses
um_ano = (date.today() - timedelta(days=365)).isoformat()
precos = consultar(cliente().table("precos_diarios").select("data, fechamento")
                   .eq("ticker", ticker).gte("data", um_ano).order("data"))
if precos:
    df = pd.DataFrame(precos)
    df["data"] = pd.to_datetime(df["data"])
    st.line_chart(df.set_index("data")["fechamento"], y_label="Fechamento (R$)")
else:
    st.info("Sem cotações para esta ação ainda.")

# últimas previsões e o que aconteceu de fato
st.subheader("Últimas previsões")
prev = consultar(cliente().table("previsoes")
                 .select("data_referencia, posicao, retorno_previsto, retorno_realizado")
                 .eq("ticker", ticker).order("data_referencia", desc=True).limit(20))
if prev:
    df = pd.DataFrame(prev)
    df["data_referencia"] = pd.to_datetime(df["data_referencia"]).dt.strftime("%d/%m/%Y")
    df["retorno_previsto"] = df["retorno_previsto"].map(percentual)
    df["retorno_realizado"] = df["retorno_realizado"].map(
        lambda v: "aguardando" if pd.isna(v) else percentual(v))
    st.dataframe(df, hide_index=True, width="stretch", column_config={
        "data_referencia": "Data", "posicao": "Posição no ranking",
        "retorno_previsto": "Previsto", "retorno_realizado": "Realizado (5 pregões)"})
