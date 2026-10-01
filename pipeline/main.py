"""Pipeline diário do Monitor B3, em 5 etapas:

    1. Ler do Supabase a lista de ações ativas
    2. Baixar as cotações do Yahoo Finance
    3. Calcular os indicadores técnicos
    4. Treinar o XGBoost e prever o retorno dos próximos 5 pregões
    5. Gravar preços, modelo e previsões no Supabase

Uso:
    python -m pipeline.main                  # execução normal (diária)
    python -m pipeline.main --primeira-vez   # envia todo o histórico de preços
    python -m pipeline.main --teste-local    # roda sem Supabase e só mostra o resultado
"""

import argparse
import logging
import sys
import warnings
from datetime import datetime
from zoneinfo import ZoneInfo

from . import banco, config, dados, indicadores, modelo

warnings.filterwarnings("ignore", message=".*utcnow is deprecated.*")   # aviso interno do yfinance
log = logging.getLogger("pipeline")


def executar(primeira_vez: bool = False, teste_local: bool = False) -> modelo.Resultado:
    # 1. Lista de ações
    if teste_local:
        sb, tickers = None, config.TICKERS_TESTE_LOCAL
    else:
        sb = banco.conectar()
        tickers = banco.ler_ativos(sb)

    # 2. Preços
    precos = dados.baixar_precos(tickers)

    # 3. Indicadores
    tabela = indicadores.calcular(precos)
    log.info("Indicadores: %d linhas", len(tabela))

    # 4. Modelo
    resultado = modelo.treinar_e_prever(tabela)
    versao = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%dT%H-%M")

    if teste_local:
        print(resultado.previsoes.head(10).to_string(index=False))
        return resultado

    # 5. Gravação no Supabase (o modelo antes das previsões, por causa da chave estrangeira)
    banco.enviar_precos(sb, precos, tudo=primeira_vez)
    banco.registrar_modelo(sb, versao, resultado)
    banco.enviar_previsoes(sb, versao, resultado)
    banco.preencher_realizados(sb, precos)
    log.info("Pipeline concluído (modelo %s)", versao)
    return resultado


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline diário do Monitor B3")
    parser.add_argument("--primeira-vez", action="store_true",
                        help="envia todo o histórico de preços ao Supabase")
    parser.add_argument("--teste-local", action="store_true",
                        help="roda sem Supabase e só mostra as previsões")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        executar(primeira_vez=args.primeira_vez, teste_local=args.teste_local)
    except Exception:
        log.exception("O pipeline falhou")
        sys.exit(1)      # código de erro: o GitHub marca a execução em vermelho e avisa por e-mail


if __name__ == "__main__":
    main()
