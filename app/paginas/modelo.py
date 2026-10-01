"""Histórico do modelo: uma linha por treino diário (tabela modelos)."""

import altair as alt
import pandas as pd
import streamlit as st

from conexao import cliente, consultar

st.title("Modelo")

modelos = consultar(cliente().table("modelos").select("*").order("treinado_em"))
if not modelos:
    st.info("O modelo ainda não foi treinado. Ele aparece depois da primeira execução do pipeline.")
    st.stop()

df = pd.DataFrame(modelos)
df["treinado_em"] = pd.to_datetime(df["treinado_em"])
ultimo = df.iloc[-1]

c1, c2, c3 = st.columns(3)
c1.metric("Último treino", ultimo["treinado_em"].tz_convert("America/Sao_Paulo").strftime("%d/%m/%Y %H:%M"))
c2.metric("Amostras de treino", f"{int(ultimo['n_amostras']):,}".replace(",", "."))
c3.metric("IC na validação", f"{ultimo['ic_validacao']:.3f}")

st.write("O IC mede se o modelo acerta a **ordem** das ações, de -1 a 1. "
         "Zero significa que ele não acerta mais que o acaso.")

linha = alt.Chart(df).mark_line(point=True).encode(
    x=alt.X("treinado_em:T", title="Treino"),
    y=alt.Y("ic_validacao:Q", title="IC na validação"),
    tooltip=["versao", "ic_validacao"])
zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(strokeDash=[4, 4]).encode(y="y:Q")
st.altair_chart(linha + zero, width="stretch")
