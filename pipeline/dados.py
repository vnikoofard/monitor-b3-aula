"""Etapa 2: baixar as cotações diárias do Yahoo Finance."""

import logging
import time
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from . import config

log = logging.getLogger(__name__)


def baixar_precos(tickers: list[str]) -> pd.DataFrame:
    """Retorna uma tabela longa: uma linha por (ticker, data), com
    abertura, maxima, minima, fechamento, fechamento_ajustado e volume."""
    inicio = date.today() - timedelta(days=365 * config.ANOS_DE_HISTORICO)
    simbolos = [t + ".SA" for t in tickers]          # no Yahoo, ações da B3 têm o sufixo .SA

    bruto = None
    for tentativa in range(1, 4):                    # o Yahoo às vezes falha: tenta 3 vezes
        try:
            bruto = yf.download(simbolos, start=inicio.isoformat(), auto_adjust=False,
                                group_by="ticker", progress=False, threads=True)
            if bruto is not None and not bruto.empty:
                break
        except Exception as erro:  # noqa: BLE001
            log.warning("Yahoo falhou (tentativa %d/3): %s", tentativa, erro)
        time.sleep(5 * tentativa)
    if bruto is None or bruto.empty:
        raise RuntimeError("Não foi possível baixar os preços do Yahoo Finance")

    if not isinstance(bruto.columns, pd.MultiIndex):        # acontece com uma única ação
        bruto.columns = pd.MultiIndex.from_product([simbolos, bruto.columns])

    partes = []
    for ticker, simbolo in zip(tickers, simbolos):
        if simbolo not in bruto.columns.get_level_values(0):
            log.warning("%s: sem dados no Yahoo — ignorado", ticker)
            continue
        df = bruto[simbolo].dropna(subset=["Close"])
        if df.empty:
            log.warning("%s: sem dados no Yahoo — ignorado", ticker)
            continue
        partes.append(pd.DataFrame({
            "ticker": ticker,
            "data": pd.to_datetime(df.index).tz_localize(None).normalize(),
            "abertura": df["Open"].to_numpy(),
            "maxima": df["High"].to_numpy(),
            "minima": df["Low"].to_numpy(),
            "fechamento": df["Close"].to_numpy(),
            "fechamento_ajustado": df["Adj Close"].to_numpy(),   # corrigido por dividendos
            "volume": df["Volume"].to_numpy(),
        }))
    precos = pd.concat(partes, ignore_index=True).sort_values(["ticker", "data"])
    log.info("Preços: %d ações, %d linhas, de %s a %s", precos["ticker"].nunique(), len(precos),
             precos["data"].min().date(), precos["data"].max().date())
    return precos.reset_index(drop=True)
