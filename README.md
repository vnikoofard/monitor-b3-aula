# Monitor B3 — versão de aula

Um web app completo com banco na nuvem, pipeline Python agendado e frontend no-code:

- **Supabase** guarda as ações, as cotações, as previsões e as carteiras dos usuários, com login, regras de segurança (RLS) e a foto de cada usuário no Storage.
- **Pipeline Python**, rodando todo dia no **GitHub Actions**, baixa as cotações, calcula indicadores técnicos, treina um XGBoost e grava as previsões no banco.
- **Frontend em Streamlit**, hospedado de graça no Streamlit Community Cloud, mostra o ranking e deixa cada usuário montar suas carteiras. (Há também um prompt para gerar o frontend no Lovable, como alternativa.)

```
monitor-b3-aula/
├── sql/01_schema.sql                  # cria todo o banco no Supabase
├── pipeline/
│   ├── config.py                      # parâmetros
│   ├── banco.py                       # etapas 1 e 5: ler e gravar no Supabase
│   ├── dados.py                       # etapa 2: baixar cotações do Yahoo Finance
│   ├── indicadores.py                 # etapa 3: indicadores técnicos
│   ├── modelo.py                      # etapa 4: treinar e prever com XGBoost
│   └── main.py                        # roda as 5 etapas em ordem
├── app/                               # frontend em Streamlit
│   ├── streamlit_app.py               # login e navegação
│   ├── conexao.py                     # conexão com o Supabase (uma por usuário)
│   ├── paginas/                       # ranking, ação, montar carteira, carteiras, modelo, perfil
│   └── requirements.txt               # bibliotecas do app (usadas pelo Streamlit Cloud)
├── .streamlit/secrets.toml.example    # modelo das chaves do app
├── tests/teste_offline.py             # testa o pipeline sem internet e sem Supabase
├── tests/teste_app.py                 # testa o app Streamlit com um banco falso
├── .github/workflows/pipeline-diario.yml   # agenda o pipeline no GitHub Actions
└── frontend/prompt_lovable.md         # alternativa: prompt para gerar o frontend no Lovable
```

## As 5 etapas do pipeline

| Etapa | Arquivo | O que faz |
|---|---|---|
| 1 | `banco.py` | Lê da tabela `ativos` quais ações acompanhar |
| 2 | `dados.py` | Baixa 3 anos de cotações do Yahoo Finance |
| 3 | `indicadores.py` | Calcula 8 indicadores técnicos e o alvo (retorno dos próximos 5 pregões) |
| 4 | `modelo.py` | Mede a qualidade nos últimos 60 pregões, retreina com tudo e prevê o último dia |
| 5 | `banco.py` | Grava preços, a versão do modelo e as previsões; preenche os retornos realizados |

Os 8 indicadores: retorno em 5, 21 e 63 pregões; volatilidade de 21 pregões; RSI de 14;
distância do preço para as médias móveis de 20 e 50; volume relativo.

## Rodar na sua máquina

```bash
pip install -r requirements.txt
python -m tests.teste_offline          # sem internet: deve terminar com OK
python -m pipeline.main --teste-local  # baixa dados reais, mostra o ranking, não grava nada
```

Para gravar no Supabase a partir da sua máquina:

```bash
export SUPABASE_URL="https://xxxxxxxx.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="sb_secret_..."
python -m pipeline.main --primeira-vez   # só na primeira vez: envia 3 anos de preços
python -m pipeline.main                  # execução normal
```

## Rodar o app Streamlit na sua máquina

```bash
pip install -r app/requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # e preencha URL e chave publishable
streamlit run app/streamlit_app.py
```

O app usa a chave **publishable** e o login do Supabase: depois que o usuário entra, cada
consulta vai ao banco com a identidade dele, e a RLS decide o que ele vê. A conexão de cada
usuário fica em `st.session_state`; nunca em `st.cache_resource`, que é compartilhado entre
todos os usuários do app.

## Implantação

1. **Supabase:** rode `sql/01_schema.sql` no SQL Editor de um projeto novo.
2. **GitHub:** crie um repositório público com estes arquivos (a pasta `.github` precisa
   ficar na raiz) e cadastre os secrets `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY`
   em Settings → Secrets and variables → Actions.
3. **Primeira execução:** aba Actions → Pipeline diário → Run workflow, marcando
   "Enviar todo o histórico". Depois disso, ele roda sozinho de segunda a sexta às 22h.
4. **Frontend:** em share.streamlit.io, crie um app a partir deste repositório, com o arquivo
   principal `app/streamlit_app.py`, e cole em **Secrets** as duas linhas de
   `.streamlit/secrets.toml.example`, preenchidas com a URL e a chave publishable.

A chave secreta (`sb_secret_...`) ignora as regras de segurança do banco: ela só pode ficar
nos secrets do GitHub, nunca no código nem no frontend.

**Aviso:** projeto educacional; as previsões não são recomendação de investimento.
