"""Etapa 3: calcular indicadores técnicos a partir dos preços.

Regra de ouro: o indicador da data t usa só preços até t. A única coluna que
olha para o futuro é o alvo (o retorno dos próximos dias), que o modelo
aprende a prever."""

import numpy as np
import pandas as pd

from . import config

INDICADORES = [
    "retorno_5d", "retorno_21d", "retorno_63d",       # quanto subiu na semana, no mês, no trimestre
    "volatilidade_21d",                               # quanto oscilou no último mês
    "rsi_14",                                         # índice de força relativa (0 a 100)
    "distancia_mm20", "distancia_mm50",               # distância do preço para as médias móveis
    "volume_relativo",                                # volume de hoje × volume médio do mês
]


def _rsi(preco: pd.Series, n: int = 14) -> pd.Series:
    variacao = preco.diff()
    alta = variacao.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    baixa = (-variacao.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + alta / baixa.replace(0, np.nan))


def _uma_acao(df: pd.DataFrame) -> pd.DataFrame:
    p = df["fechamento_ajustado"]
    saida = df[["ticker", "data"]].copy()
    saida["retorno_5d"] = p.pct_change(5)
    saida["retorno_21d"] = p.pct_change(21)
    saida["retorno_63d"] = p.pct_change(63)
    saida["volatilidade_21d"] = p.pct_change().rolling(21).std()
    saida["rsi_14"] = _rsi(p)
    saida["distancia_mm20"] = p / p.rolling(20).mean() - 1
    saida["distancia_mm50"] = p / p.rolling(50).mean() - 1
    saida["volume_relativo"] = df["volume"] / df["volume"].rolling(21).mean()
    # alvo: retorno dos próximos H pregões (olha para o futuro!)
    saida["alvo"] = p.shift(-config.HORIZONTE_DIAS) / p - 1
    return saida


def calcular(precos: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por (ticker, data) com os indicadores e o alvo.
    Linhas sem histórico suficiente para os indicadores são descartadas."""
    tabela = pd.concat([_uma_acao(g) for _, g in precos.groupby("ticker")], ignore_index=True)
    tabela = tabela.replace([np.inf, -np.inf], np.nan)
    return tabela.dropna(subset=INDICADORES).reset_index(drop=True)
