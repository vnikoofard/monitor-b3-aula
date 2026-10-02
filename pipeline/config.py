"""Parâmetros do pipeline. A lista de ações NÃO fica aqui: ela é lida da
tabela `ativos` do Supabase (para incluir uma ação, basta inserir uma linha)."""

ANOS_DE_HISTORICO = 3        # quanto histórico de preços baixar para treinar
HORIZONTE_DIAS = 5           # prever o retorno dos próximos 5 pregões
DIAS_VALIDACAO = 30  #60        # últimos pregões usados para medir a qualidade do modelo

# XGBoost: um modelo pequeno, de propósito
XGB_PARAMS = {
    "n_estimators": 300,
    "learning_rate": 0.03,
    "max_depth": 3,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 20,
    "random_state": 42,
}

DIAS_PARA_ENVIAR = 10        # execução diária: reenvia os preços dos últimos 10 pregões
TAMANHO_LOTE = 500           # linhas por requisição ao Supabase

# Usada só no modo --teste-local (sem Supabase). Na execução normal, a lista
# vem da tabela `ativos` do banco. É a mesma lista do script SQL.
TICKERS_TESTE_LOCAL = [
    "PETR4", "PRIO3", "VALE3", "GGBR4", "SUZB3", "KLBN11", "ITUB4", "BBDC4",
    "BBAS3", "BPAC11", "ITSA4", "B3SA3", "EQTL3", "CMIG4", "SBSP3", "VIVT3",
    "TOTS3", "WEGE3", "RENT3", "ABEV3", "RADL3", "LREN3", "MGLU3", "CYRE3",
]
