"""Testa o app Streamlit sem Supabase: um banco falso responde às consultas e o
teste percorre login e todas as páginas, conferindo que nenhuma quebra.

    python -m tests.teste_app
"""
from datetime import date, timedelta
from types import SimpleNamespace
from unittest import mock

import supabase
from streamlit.testing.v1 import AppTest

HOJE = date.today()
DIAS = [(HOJE - timedelta(days=i)).isoformat() for i in range(300, 0, -1)]
FALSO = {
    "v_ranking_atual": [
        {"posicao": i + 1, "ticker": t, "nome": n, "setor": s, "retorno_previsto": r,
         "ultimo_preco": 30.0 + i, "data_referencia": DIAS[-1], "modelo_versao": "v1"}
        for i, (t, n, s, r) in enumerate([("ITUB4", "Itaú", "Bancos", 0.012),
                                          ("VALE3", "Vale", "Mineração", 0.008),
                                          ("PETR4", "Petrobras", "Petróleo e gás", -0.003)])],
    "ativos": [{"ticker": "ITUB4", "nome": "Itaú", "setores": {"nome": "Bancos"}},
               {"ticker": "VALE3", "nome": "Vale", "setores": {"nome": "Mineração"}}],
    "precos_diarios": [{"data": d, "fechamento": 30 + i * 0.01} for i, d in enumerate(DIAS)],
    "previsoes": [{"data_referencia": DIAS[-1], "posicao": 1, "retorno_previsto": 0.012,
                   "retorno_realizado": None},
                  {"data_referencia": DIAS[-10], "posicao": 3, "retorno_previsto": 0.004,
                   "retorno_realizado": -0.01}],
    "v_desempenho_carteiras": [{"carteira_id": 42, "user_id": "u1", "nome": "Teste",
                                "data_referencia": DIAS[-1], "n_acoes": 2,
                                "retorno_previsto": 0.01, "retorno_realizado": None,
                                "concluida": False}],
    "carteira_itens": [{"ticker": "ITUB4", "peso": "0.5000", "ativos": {"nome": "Itaú"}},
                       {"ticker": "VALE3", "peso": "0.5000", "ativos": {"nome": "Vale"}}],
    "modelos": [{"versao": f"v{i}", "treinado_em": f"{DIAS[-5 + i]}T22:00:00+00:00",
                 "n_amostras": 16000 + i, "ic_validacao": 0.02 * (i - 2)} for i in range(5)],
    "profiles": [{"nome": "Ana", "avatar_url": None}],
}
chamadas = []


class Consulta:
    def __init__(self, tabela): self.tabela = tabela
    def __getattr__(self, nome):                     # select, eq, gte, order, limit, update, delete...
        def metodo(*args, **kwargs):
            chamadas.append((self.tabela, nome, args))
            return self
        return metodo
    def execute(self):
        return SimpleNamespace(data=42 if self.tabela == "rpc" else FALSO.get(self.tabela, []))


class Bucket:
    def upload(self, path, file, file_options): chamadas.append(("storage", "upload", (path,)))
    def get_public_url(self, path): return f"https://x.supabase.co/storage/v1/object/public/avatares/{path}"


class ClienteFalso:
    def __init__(self, *a):
        usuario = SimpleNamespace(id="u1", email="ana@teste.com")
        self.auth = SimpleNamespace(
            sign_in_with_password=lambda cred: SimpleNamespace(user=usuario, session=object()),
            sign_up=lambda dados: SimpleNamespace(user=usuario, session=object()),
            sign_out=lambda: None)
        self.storage = SimpleNamespace(from_=lambda nome: Bucket())
    def table(self, nome): return Consulta(nome)
    def rpc(self, nome, params): chamadas.append(("rpc", nome, (params,))); return Consulta("rpc")


def sem_erros(at, onde):
    assert not at.exception, f"{onde}: {at.exception}"
    assert not at.error, f"{onde}: {[e.value for e in at.error]}"


with mock.patch.object(supabase, "create_client", ClienteFalso):
    at = AppTest.from_file("../app/streamlit_app.py", default_timeout=30)
    at.secrets["SUPABASE_URL"] = "https://x.supabase.co"
    at.secrets["SUPABASE_PUBLISHABLE_KEY"] = "sb_publishable_teste"
    at.run()
    sem_erros(at, "tela de login")
    assert at.title[0].value == "📈 Monitor B3"

    at.text_input[0].input("ana@teste.com")
    at.text_input[1].input("123456")
    at.button[0].click().run()                      # "Entrar"
    sem_erros(at, "ranking")
    assert at.title[0].value == "Ranking do dia"

    for pagina, titulo in [("paginas/acao.py", "Ação"),
                           ("paginas/montar_carteira.py", "Montar carteira"),
                           ("paginas/carteiras.py", "Minhas carteiras"),
                           ("paginas/modelo.py", "Modelo"),
                           ("paginas/perfil.py", "Meu perfil")]:
        at.switch_page(pagina).run()
        sem_erros(at, pagina)
        assert at.title[0].value == titulo, (pagina, [t.value for t in at.title])

    at.switch_page("paginas/montar_carteira.py").run()
    [b for b in at.button if b.label == "Gerar carteira"][0].click().run()
    sem_erros(at, "gerar carteira")
    assert ("rpc", "montar_carteira", ({"p_n": 5, "p_nome": None},)) in chamadas
    assert at.title[0].value == "Minhas carteiras"   # foi redirecionado

print("OK — login e as 6 páginas funcionam")
