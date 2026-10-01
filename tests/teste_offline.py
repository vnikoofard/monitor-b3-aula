"""Teste sem internet e sem Supabase: gera preços sintéticos, roda o pipeline
completo e confere o que seria gravado no banco (nomes de colunas, tipos).

    python -m tests.teste_offline
"""
import json
import logging
from types import SimpleNamespace
from unittest import mock

import numpy as np
import pandas as pd

from pipeline import banco, config, dados, main

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


# ---------- preços sintéticos: 24 ações, ~3 anos de pregões ----------
def precos_sinteticos() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    datas = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=750)
    linhas = []
    for t in config.TICKERS_TESTE_LOCAL:
        r = rng.normal(0.0003, 0.018, len(datas))
        p = 20 * np.exp(np.cumsum(r))
        linhas.append(pd.DataFrame({
            "ticker": t, "data": datas, "abertura": p, "maxima": p * 1.01, "minima": p * 0.99,
            "fechamento": p, "fechamento_ajustado": p,
            "volume": rng.integers(1e5, 1e7, len(datas)).astype(float)}))
    return pd.concat(linhas, ignore_index=True)


PRECOS = precos_sinteticos()

# ---------- Supabase falso: registra o que seria gravado ----------
gravado = {}


class Consulta:
    def __init__(self, tabela):
        self.tabela = tabela

    def select(self, *a): return self
    def eq(self, *a): return self
    def order(self, *a): return self
    def is_(self, *a): return self

    def upsert(self, linhas, on_conflict):
        json.dumps(linhas)                                  # precisa ser JSON válido
        gravado.setdefault(self.tabela, []).extend(linhas)
        return self

    def execute(self):
        if self.tabela == "ativos":
            return SimpleNamespace(data=[{"ticker": t} for t in config.TICKERS_TESTE_LOCAL])
        if self.tabela == "previsoes":                      # uma previsão antiga pendente
            antiga = PRECOS["data"].drop_duplicates().sort_values().iloc[-20]
            return SimpleNamespace(data=[{"data_referencia": antiga.date().isoformat(),
                                          "ticker": "PETR4", "modelo_versao": "antigo",
                                          "retorno_previsto": 0.01, "posicao": 1,
                                          "retorno_realizado": None}])
        return SimpleNamespace(data=[])


cliente_falso = SimpleNamespace(table=Consulta)

with mock.patch.object(dados, "baixar_precos", return_value=PRECOS), \
     mock.patch.object(banco, "conectar", return_value=cliente_falso):
    res = main.executar(primeira_vez=False)

# ---------- conferências ----------
colunas_schema = {
    "precos_diarios": {"ticker", "data", "abertura", "maxima", "minima", "fechamento", "volume"},
    "modelos": {"versao", "n_amostras", "ic_validacao"},
    "previsoes": {"data_referencia", "ticker", "modelo_versao", "retorno_previsto", "posicao",
                  "retorno_realizado"},
}
for tabela, colunas in colunas_schema.items():
    assert tabela in gravado, f"nada gravado em {tabela}"
    for linha in gravado[tabela]:
        assert set(linha) <= colunas, f"{tabela}: coluna fora do schema {set(linha) - colunas}"

assert len(res.previsoes) == len(config.TICKERS_TESTE_LOCAL)
assert list(res.previsoes["posicao"]) == list(range(1, len(res.previsoes) + 1))
assert len({l["data"] for l in gravado["precos_diarios"]}) == config.DIAS_PARA_ENVIAR
realizado = [l for l in gravado["previsoes"] if l.get("retorno_realizado") is not None]
assert len(realizado) == 1, "retorno realizado da previsão antiga não foi preenchido"
print({t: len(v) for t, v in gravado.items()})
print("OK")
