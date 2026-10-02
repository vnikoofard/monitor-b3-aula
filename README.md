# Monitor B3 — versão de aula

Um web app completo com banco na nuvem, pipeline Python agendado e frontend no-code:

- **Supabase** guarda as ações, as cotações, as previsões e as carteiras dos usuários, com login, regras de segurança (RLS) e a foto de cada usuário no Storage.
- **Pipeline Python**, rodando todo dia no **GitHub Actions**, baixa as cotações, calcula indicadores técnicos, treina um XGBoost e grava as previsões no banco.
- **Frontend em Streamlit**, hospedado de graça no Streamlit Community Cloud, mostra o ranking e deixa cada usuário montar suas carteiras. (Há também um prompt para gerar o frontend no Lovable, como alternativa.)

## Sequência dos guias das aulas

Os três guias seguem a ordem das aulas, e o guia de implantação é usado aos poucos, ao longo de três delas:

| Aula | Apresentação | Guia usado | Que parte |
|---|---|---|---|
| 1 · SQL e o banco | Aula 1 | [Construindo o banco no Supabase](docs/1-Monitor%20B3%20%E2%80%94%20Construindo%20o%20banco%20no%20Supabase.md) | Inteiro: a construção ao vivo, passo a passo |
| 2 · Git e GitHub | Aula 2 | [Guia de implantação](docs/2-Monitor%20B3%20%E2%80%94%20Guia%20de%20implantação%20passo%20a%20passo.md) | "Antes de começar" e Etapa 2 (repositório no GitHub) |
| 3 · Streamlit | Aula 3 | [Guia de implantação](docs/2-Monitor%20B3%20%E2%80%94%20Guia%20de%20implantação%20passo%20a%20passo.md) | Etapa 6, parte "Testar na sua máquina" |
| 4 · Arquitetura e pipeline | Aula 4 | [A arquitetura do app, explicada](docs/3-Monitor%20B3%20%E2%80%94%20A%20arquitetura%20do%20app,%20explicada.md) e [Guia de implantação](docs/2-Monitor%20B3%20%E2%80%94%20Guia%20de%20implantação%20passo%20a%20passo.md) | A arquitetura como leitura de apoio; do guia de implantação, as Etapas 3 a 5 (workflow, secrets, primeira execução, conferir os dados), o resto da Etapa 6 (publicar o app e testar com dois usuários) e a Rotina |

Os slides de cada aula ficam em [docs/slides](docs/slides):

- [Aula 1 — SQL e o banco do Monitor B3](docs/slides/Aula%201%20%E2%80%94%20SQL%20e%20o%20banco%20do%20Monitor%20B3.pdf)
- [Aula 2 — Git e GitHub](docs/slides/Aula%202%20%E2%80%94%20Git%20e%20GitHub.pdf)
- [Aula 3 — Introdução ao Streamlit](docs/slides/Aula%203%20%E2%80%94%20Introdução%20ao%20Streamlit.pdf)
- [Aula 4 — Arquitetura do Monitor B3 e o pipeline](docs/slides/Aula%204%20%E2%80%94%20Arquitetura%20do%20Monitor%20B3%20e%20o%20pipeline.pdf)


> Um detalhe: a Etapa 1 do guia de implantação (Supabase) repete, de forma resumida, o que o guia de construção faz em detalhe. Quem construiu o banco na Aula 1 pode pular essa etapa, só copiando a URL e a chave secreta do projeto, que aparecem nos itens 5 e 6 dela.



## Estrutura do código

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
| 4 | `modelo.py` | Mede a qualidade nos últimos 30 pregões, retreina com tudo e prevê o último dia |
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
