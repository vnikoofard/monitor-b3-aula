# Prompt do frontend — Monitor B3 (Lovable, Bolt ou v0, reflex)

Antes da primeira mensagem, crie um projeto NOVO e conecte o seu Supabase
(no Lovable: More → Cloud → "Already have a Supabase project?" → Connect). Não deixe o
Lovable ativar o backend próprio dele (Lovable Cloud): depois de ativado, não é mais
possível conectar o seu Supabase, e o pipeline Python não consegue gravar no banco dele. No plano gratuito, envie **uma fase por vez** (são cinco) e só avance quando a anterior
estiver funcionando.

---

## Fase 1 — Fundação e login

```
Crie o frontend do "Monitor B3", um app educacional que mostra previsões de retorno de
ações da B3 e permite a cada usuário montar carteiras. Use React, TypeScript, Tailwind CSS,
shadcn/ui e Recharts.

O BACKEND JÁ ESTÁ PRONTO NO MEU PROJETO SUPABASE, que já está conectado a este projeto.
Não ative o Lovable Cloud, não crie tabelas, não rode migrations e não altere políticas
de segurança. Apenas leia e escreva nas tabelas, views e funções descritas. Se alguma
tabela ou view não for encontrada, pare e me avise em vez de criá-la.

Estilo: claro e sóbrio. Fundo #F8FAFC, cards brancos com sombra leve, cor primária #1E40AF,
verde #059669 para valores positivos, vermelho #DC2626 para negativos. Números com
tabular-nums. Moeda e percentuais no padrão brasileiro (Intl pt-BR).

Rodapé fixo em todas as páginas: "Projeto educacional. As previsões não são recomendação
de investimento."

Autenticação com Supabase Auth (e-mail e senha):
- Página /login e página /cadastro, centralizadas.
- No cadastro, peça nome, e-mail e senha, e envie o nome em options.data.nome
  (um trigger no banco usa esse campo para criar o perfil).
- Todas as outras páginas exigem login; sem sessão, redirecionar para /login.

Layout com barra lateral: Ranking, Montar carteira, Minhas carteiras, Modelo, e um botão
Sair. Crie um componente reutilizável Percent que recebe um número decimal (0.0123),
mostra "1,23%" e pinta de verde se positivo e vermelho se negativo.
```

## Fase 2 — Ranking e página da ação

```
Página Ranking (rota /):
- Leia a view v_ranking_atual, ordenada por posicao. Colunas: posicao, ticker, nome,
  setor, ultimo_preco (R$), retorno_previsto (usar o componente Percent).
- No topo, mostre a data do pregão (data_referencia, formato dd/mm/aaaa) e o texto
  "Retorno previsto para os próximos 5 pregões".
- Filtro por setor (Select com os setores distintos da própria view) e busca por ticker.
- Clicar numa linha abre /acao/:ticker.

Página da ação (rota /acao/:ticker):
- Nome e setor: tabela ativos com join em setores (ativos.setor_id = setores.id).
- Gráfico de linha do fechamento dos últimos 12 meses: tabela precos_diarios filtrada
  pelo ticker, ordenada por data.
- Tabela com as últimas 20 previsões da ação (tabela previsoes, filtrar por ticker,
  ordenar por data_referencia decrescente): data, retorno_previsto e retorno_realizado
  (mostrar "aguardando" quando for nulo).

Regras de dados:
- As colunas retorno_previsto e retorno_realizado são decimais (0.0123 = 1,23%).
- As tabelas setores, ativos, precos_diarios, modelos e previsoes são somente leitura.
```

## Fase 3 — Carteiras

```
Página Montar carteira (rota /carteiras/nova):
- Campo "Número de ações" (de 1 a 20, padrão 5) e campo "Nome da carteira" (opcional).
- Botão "Gerar carteira" chama supabase.rpc('montar_carteira', { p_n, p_nome }).
  A função devolve o id da carteira criada; em seguida, navegar para /carteiras/:id.
- Mostre os erros da função num toast (por exemplo, "Ainda não há previsões").

Página Minhas carteiras (rota /carteiras):
- Cards da view v_desempenho_carteiras: nome, data_referencia, n_acoes,
  retorno_previsto e, se concluida for verdadeiro, retorno_realizado com cor;
  se for falso, um Badge "em andamento".
- Botão Excluir em cada card: delete na tabela carteiras pelo id (os itens são apagados
  junto, pelo banco).

Detalhe da carteira (rota /carteiras/:id):
- Itens da tabela carteira_itens filtrados por carteira_id, com join em ativos para o nome:
  ticker, nome e peso (em %).
- Gráfico de pizza dos pesos.

Regras de dados:
- Carteiras são criadas SOMENTE pela função montar_carteira, nunca por insert direto.
- Nunca envie user_id: o banco preenche sozinho com o usuário logado.
- IDs de carteira são números inteiros.
```

## Fase 4 — Página do modelo

```
Página Modelo (rota /modelo):
- Card com o último registro da tabela modelos (ordenar por treinado_em decrescente):
  versao, data e hora do treino, n_amostras e ic_validacao.
- Explique em uma frase: "O IC mede se o modelo acerta a ordem das ações, de -1 a 1;
  zero significa que ele não acerta mais que o acaso."
- Gráfico de linha do ic_validacao ao longo do tempo (todos os registros de modelos,
  ordenados por treinado_em), com uma linha horizontal em zero.
```

## Fase 5 — Perfil e foto do usuário

```
Página Meu perfil (rota /perfil), com um item "Meu perfil" na barra lateral:
- Leia a linha do usuário logado na tabela profiles (colunas nome e avatar_url).
- Campo para editar o nome: update em profiles onde id = id do usuário logado.
- Foto do usuário:
  - Mostre a foto de avatar_url num círculo; se for nula, mostre as iniciais do nome.
  - Botão "Trocar foto" aceita só PNG, JPEG ou WEBP de até 2 MB (valide antes de enviar
    e avise num toast se o arquivo não servir).
  - Envie para o bucket público "avatares" do Supabase Storage, no caminho
    "<id do usuário>/avatar", com upsert: true (substitui a foto anterior).
  - Pegue a URL pública com getPublicUrl, acrescente "?v=" + Date.now() (para o navegador
    não mostrar a foto antiga guardada em cache) e grave em profiles.avatar_url.
- Mostre a mesma foto, pequena, no topo da barra lateral, ao lado do nome.

Regras: o caminho do arquivo PRECISA começar com o id do usuário logado; as regras de
segurança do Storage recusam qualquer outro caminho.
```

---

Se algo quebrar, copie a mensagem de erro exata do console do navegador e cole na
conversa com a ferramenta, em vez de pedir apenas "conserte".
