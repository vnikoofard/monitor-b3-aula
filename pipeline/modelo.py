"""Etapa 4: treinar o XGBoost e prever o retorno de cada ação.

1. Separa os últimos DIAS_VALIDACAO pregões para medir a qualidade (IC).
2. Retreina com todos os dados que já têm alvo conhecido.
3. Prevê o retorno dos próximos 5 pregões para o último dia disponível."""

import logging
from dataclasses import dataclass

import pandas as pd
from xgboost import XGBRegressor

from . import config
from .indicadores import INDICADORES

log = logging.getLogger(__name__)


@dataclass
class Resultado:
    previsoes: pd.DataFrame      # ticker, retorno_previsto, posicao
    data_referencia: pd.Timestamp
    n_amostras: int
    ic_validacao: float


def ic_medio(df: pd.DataFrame, coluna_prevista: str) -> float:
    """IC: correlação entre a ORDEM prevista e a ORDEM real das ações em cada dia
    (de -1 a 1; 0 = o modelo não acerta a ordem), em média ao longo dos dias."""
    por_dia = df.groupby("data").apply(
        lambda g: g[coluna_prevista].rank().corr(g["alvo"].rank()))
    return float(por_dia.mean())


def treinar_e_prever(tabela: pd.DataFrame) -> Resultado:
    com_alvo = tabela.dropna(subset=["alvo"])
    datas = com_alvo["data"].drop_duplicates().sort_values()

    # --- 1. validação: treina com o passado, mede nos últimos dias ---
    inicio_validacao = datas.iloc[-config.DIAS_VALIDACAO]
    # intervalo de H dias entre treino e validação: os alvos não podem se sobrepor
    fim_treino = datas.iloc[-config.DIAS_VALIDACAO - config.HORIZONTE_DIAS - 1]
    treino = com_alvo[com_alvo["data"] <= fim_treino]
    validacao = com_alvo[com_alvo["data"] >= inicio_validacao].copy()

    modelo = XGBRegressor(**config.XGB_PARAMS)
    modelo.fit(treino[INDICADORES], treino["alvo"])
    validacao["previsto"] = modelo.predict(validacao[INDICADORES])
    ic = ic_medio(validacao, "previsto")
    log.info("Validação (%s a %s): IC médio = %.4f",
             inicio_validacao.date(), datas.iloc[-1].date(), ic)

    # --- 2. modelo final com todos os dados que têm alvo ---
    modelo = XGBRegressor(**config.XGB_PARAMS)
    modelo.fit(com_alvo[INDICADORES], com_alvo["alvo"])

    # --- 3. previsão para o último pregão (alvo ainda desconhecido) ---
    ultimo_dia = tabela["data"].max()
    hoje = tabela[tabela["data"] == ultimo_dia].copy()
    hoje["retorno_previsto"] = modelo.predict(hoje[INDICADORES])
    hoje = hoje.sort_values("retorno_previsto", ascending=False).reset_index(drop=True)
    hoje["posicao"] = range(1, len(hoje) + 1)
    log.info("Previsões para o pregão de %s: %d ações", ultimo_dia.date(), len(hoje))

    return Resultado(previsoes=hoje[["ticker", "retorno_previsto", "posicao"]],
                     data_referencia=ultimo_dia, n_amostras=len(com_alvo), ic_validacao=ic)
