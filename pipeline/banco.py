"""Etapas 1 e 5: ler e gravar no Supabase.

O pipeline usa a chave SECRETA (sb_secret_...), que ignora a RLS: é o único
programa autorizado a escrever nas tabelas de mercado. As escritas são do tipo
UPSERT (insere ou atualiza), então rodar duas vezes no mesmo dia não duplica nada."""

import logging
import math
import os

import pandas as pd
from supabase import Client, create_client

from . import config

log = logging.getLogger(__name__)


def conectar() -> Client:
    url = os.environ.get("SUPABASE_URL")
    chave = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not chave:
        raise RuntimeError("Defina as variáveis SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, chave)


def _json(valor):
    """Converte valores do pandas/numpy para tipos que o Supabase aceita."""
    if isinstance(valor, pd.Timestamp):
        return valor.date().isoformat()
    if hasattr(valor, "item"):                      # números do numpy
        valor = valor.item()
    if isinstance(valor, float) and math.isnan(valor):
        return None
    return valor


def _upsert(sb: Client, tabela: str, linhas: list[dict], chave: str) -> None:
    linhas = [{k: _json(v) for k, v in linha.items()} for linha in linhas]
    for i in range(0, len(linhas), config.TAMANHO_LOTE):
        sb.table(tabela).upsert(linhas[i:i + config.TAMANHO_LOTE], on_conflict=chave).execute()
    log.info("%s: %d linhas gravadas", tabela, len(linhas))


# ---------------------------------------------------------------------
def ler_ativos(sb: Client) -> list[str]:
    """Etapa 1: a lista de ações vem do banco, não do código."""
    resp = sb.table("ativos").select("ticker").eq("ativo", True).order("ticker").execute()
    tickers = [linha["ticker"] for linha in resp.data]
    if not tickers:
        raise RuntimeError("A tabela 'ativos' está vazia: rode o script SQL primeiro")
    log.info("Ações ativas no banco: %d", len(tickers))
    return tickers


def enviar_precos(sb: Client, precos: pd.DataFrame, tudo: bool) -> None:
    if not tudo:                                    # execução diária: só os últimos pregões
        datas = precos["data"].drop_duplicates().sort_values()
        precos = precos[precos["data"] >= datas.iloc[-config.DIAS_PARA_ENVIAR]]
    colunas = ["ticker", "data", "abertura", "maxima", "minima", "fechamento", "volume"]
    linhas = precos[colunas].to_dict("records")
    for linha in linhas:
        linha["volume"] = None if pd.isna(linha["volume"]) else int(linha["volume"])
    _upsert(sb, "precos_diarios", linhas, "ticker,data")


def registrar_modelo(sb: Client, versao: str, resultado) -> None:
    _upsert(sb, "modelos", [{"versao": versao, "n_amostras": resultado.n_amostras,
                             "ic_validacao": resultado.ic_validacao}], "versao")


def enviar_previsoes(sb: Client, versao: str, resultado) -> None:
    linhas = [{"data_referencia": resultado.data_referencia, "ticker": p.ticker,
               "modelo_versao": versao, "retorno_previsto": p.retorno_previsto,
               "posicao": p.posicao}
              for p in resultado.previsoes.itertuples()]
    _upsert(sb, "previsoes", linhas, "data_referencia,ticker")


def preencher_realizados(sb: Client, precos: pd.DataFrame) -> None:
    """Completa o retorno_realizado das previsões cujos 5 pregões já passaram."""
    pendentes = (sb.table("previsoes").select("*")
                   .is_("retorno_realizado", "null").execute().data)
    if not pendentes:
        return
    tabela = precos.pivot(index="data", columns="ticker", values="fechamento_ajustado")
    datas = list(tabela.index)
    prontas = []
    for p in pendentes:
        dia = pd.Timestamp(p["data_referencia"])
        if dia not in tabela.index or p["ticker"] not in tabela.columns:
            continue
        i = datas.index(dia)
        if i + config.HORIZONTE_DIAS >= len(datas):
            continue                                # ainda não se passaram 5 pregões
        inicio = tabela.iloc[i][p["ticker"]]
        fim = tabela.iloc[i + config.HORIZONTE_DIAS][p["ticker"]]
        if pd.notna(inicio) and pd.notna(fim):
            prontas.append({**p, "retorno_realizado": fim / inicio - 1})
    if prontas:
        _upsert(sb, "previsoes", prontas, "data_referencia,ticker")
