# Stories & Tasks — Personal Finance Roadmap

> **Tech Lead:** Documento de planejamento para as features solicitadas.
> **Data:** 2026-03-13 · **Ultima revisao:** 2026-03-21
> **Convencao de branches:** `feat/<slug-da-historia>`

---

## STATUS ATUAL — Leia isto primeiro

| Campo | Valor |
|-------|-------|
| **Proxima historia a implementar** | **S11 — Docker e Containerizacao** |
| **Proxima task a implementar** | **T11.1** |
| **Historias concluidas** | S0, S1, S2, S3, S4, S5, S6, S7, S8, S9, S10 |
| **Historias pendentes** | S11, S12, S13, S14, S15, S16 |
| **Branch ativa** | `feat/schema-optimization` (pronta para merge) |
| **Mudancas nao commitadas em main** | Nenhuma |
| **Bloqueios conhecidos** | Nenhum |

### O que fazer agora

1. Ler a secao da proxima historia (S11) e suas tasks
2. Criar a branch `feat/docker`
3. Implementar as tasks na ordem indicada
4. Rodar `pytest tests/` e verificar coverage >= 80% antes de considerar completa
5. Ao finalizar, atualizar este documento (ver lembrete no final)

---

## Legenda

| Simbolo  | Significado                                                 |
| -------- | ----------------------------------------------------------- |
| `[BE]`   | Tarefa de backend (Python/Flask/SQLite)                     |
| `[FE]`   | Tarefa de frontend (React/TypeScript)                       |
| `[DB]`   | Migracao / schema de banco de dados                         |
| `[INFRA]`| Infraestrutura (Docker, CI/CD, deploy)                      |

---

## Indice de Historias

0. ~~S0 — Migracoes de Banco de Dados~~ [CONCLUIDA]
1. ~~S1 — Ritmo de Gastos~~ [CONCLUIDA]
2. ~~S2 — Patrimonio e Resultado Parcial~~ [CONCLUIDA]
3. ~~S3 — Proximas Despesas~~ [CONCLUIDA]
4. ~~S4 — Recorrencias~~ [CONCLUIDA]
5. ~~S5 — Receitas~~ [CONCLUIDA]
6. ~~S6 — Fluxo de Caixa~~ [CONCLUIDA]
7. ~~S7 — Faturas~~ [CONCLUIDA]
8. ~~S8 — Categorias e Automacoes~~ [CONCLUIDA]
9. ~~S9 — Projecao Patrimonial~~ [CONCLUIDA]
10. ~~S10 — Otimizacao de Schema e Indices~~ [CONCLUIDA]
11. [S11 — Docker e Containerizacao](#s11--docker-e-containerizacao) **<-- PROXIMA**
12. [S12 — Onboarding de Primeiro Uso](#s12--onboarding-de-primeiro-uso)
13. [S13 — Integridade de Dados e Gaps](#s13--integridade-de-dados-e-gaps)
14. [S14 — Backfill Refinado](#s14--backfill-refinado)
15. [S15 — Metas de Consumo](#s15--metas-de-consumo)
16. [S16 — Transicao Mes/Ciclo Fatura](#s16--transicao-mesciclo-fatura)

---

## S0 — Migrações de Banco de Dados

**Branch:** `feat/db-migrations`

**Descrição:** Consolida todas as alterações de schema necessárias para o roadmap inteiro. Deve ser mergeada em `main` **antes** do início de qualquer outra história, eliminando conflitos de migration entre branches paralelas.

> **⚠️ Bloqueante global:** S1–S9 só podem ser iniciadas após o merge desta branch.

---

### Tasks

As tasks abaixo são **todas independentes entre si** e podem ser desenvolvidas em paralelo na mesma branch por um único dev em sequência, ou por múltiplos devs em sub-branches.

```
T0.1 [DB] 🟡 — Criar tabela accounts_snapshot
```

Necessária para: **S2 — Patrimônio**.
Adicionar em `init_db.py` (TABLES_SQL e RESET_SQL):

```sql
CREATE TABLE IF NOT EXISTS accounts_snapshot (
    id               TEXT,
    item_id          TEXT,
    name             TEXT,
    type             TEXT,
    subtype          TEXT,
    balance          REAL,
    credit_limit     REAL,
    available_credit REAL,
    due_date         TEXT,
    snapshotted_at   TEXT,
    PRIMARY KEY (id, snapshotted_at)
)
```

```
T0.2 [DB] 🟡 — Criar tabela recurrent_expenses
```

Necessária para: **S4 — Recorrências**, **S3 — Próximas Despesas**, **S9 — Projeção**.

```sql
CREATE TABLE IF NOT EXISTS recurrent_expenses (
    id              TEXT PRIMARY KEY,
    item_id         TEXT,
    description     TEXT,
    amount          REAL,
    frequency       TEXT,
    next_occurrence TEXT,
    category_id     TEXT,
    merchant_name   TEXT,
    confidence      REAL,
    source          TEXT DEFAULT 'pluggy',
    is_unavoidable  INTEGER DEFAULT 0,
    synced_at       TEXT
)
```

```
T0.3 [DB] 🟡 — Adicionar colunas de parcelas em credit_transactions
```

Necessária para: **S4 — Recorrências** (progresso de parcelas), **S7 — Faturas**, **S3 — Próximas Despesas**.

```sql
ALTER TABLE credit_transactions ADD COLUMN installment_number  INT;
ALTER TABLE credit_transactions ADD COLUMN total_installments  INT;
ALTER TABLE credit_transactions ADD COLUMN total_amount        REAL;
```

> Como SQLite não suporta `ADD COLUMN` com FK, usar script idempotente: verificar se a coluna existe antes de adicionar.

```
T0.4 [DB] 🟡 — Criar tabela income_sources
```

Necessária para: **S5 — Receitas**, **S9 — Projeção**.

```sql
CREATE TABLE IF NOT EXISTS income_sources (
    id              TEXT PRIMARY KEY,
    item_id         TEXT,
    description     TEXT,
    amount          REAL,
    frequency       TEXT,
    last_occurrence TEXT,
    confidence      REAL,
    total_m1        REAL,
    total_m3        REAL,
    total_m6        REAL,
    total_m12       REAL,
    source          TEXT DEFAULT 'pluggy',
    synced_at       TEXT
)
```

```
T0.5 [DB] 🟡 — Adicionar colunas is_open, payment_date, total_amount_paid em bills
```

Necessária para: **S7 — Faturas**.

```sql
ALTER TABLE bills ADD COLUMN is_open           INTEGER DEFAULT 1;
ALTER TABLE bills ADD COLUMN payment_date      TEXT;
ALTER TABLE bills ADD COLUMN total_amount_paid REAL;
```

```
T0.6 [DB] 🟡 — Criar tabela automation_rules
```

Necessária para: **S8 — Categorias e Automações**.

```sql
CREATE TABLE IF NOT EXISTS automation_rules (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT,
    conditions  TEXT NOT NULL,
    actions     TEXT NOT NULL,
    priority    INTEGER DEFAULT 0,
    enabled     INTEGER DEFAULT 1,
    created_at  TEXT DEFAULT (datetime('now'))
)
```

`conditions`: JSON array `[{field, operator, value}]` — campos suportados: `description`, `amount`, `operation_type`.
`actions`: JSON array `[{type, value}]` — tipos: `set_category`, `exclude`, `set_description`.

```
T0.7 [DB] 🔴 (depende de T0.1–T0.6) — Script de migration idempotente e atualização do RESET_SQL
```

Criar `scripts/migrate.py` que aplica todas as alterações de forma segura em bancos existentes (sem dados):

- Executa cada `ALTER TABLE` somente se a coluna ainda não existir (`PRAGMA table_info`).
- Executa cada `CREATE TABLE IF NOT EXISTS`.
- Atualizar lista `RESET_SQL` em `init_db.py` com as novas tabelas na ordem correta de drop (respeitar FKs).
- Adicionar chamada a `migrate.py` no `README` de setup.

---

## S1 — Ritmo de Gastos

**Branch:** `feat/spending-pace`

**Descrição:** Gráfico de linha cumulativo comparando o ritmo de gastos do mês atual vs. mês anterior, com linhas de referência (meta, médias).

**Dados necessários:**

- Transações diárias já disponíveis em `bank_transactions` e `credit_transactions`
- Meta de gastos: tabela `user_goals` (já existe)
- Média histórica: calculada via `finance_history`

---

### Tasks

```
T1.1 [BE][DB] 🔴 — Endpoint de gastos diários acumulados
```

Criar `GET /api/dashboard/spending-pace?month=YYYY-MM` retornando array `[{day, cumulative_amount, prev_month_cumulative}]`.

- Consulta `bank_transactions` + `credit_transactions` agrupando por dia do mês atual e mês anterior.
- Inclui no response: `monthly_goal` (de `user_goals` onde `category_id IS NULL`), `monthly_avg` (média dos últimos 6 meses em `finance_history`), `unavoidable_avg` (soma de recorrentes obrigatórias — a ser adicionado em S4).

```
T1.2 [FE] 🔴 (depende de T1.1) — Hook useSpendingPace
```

Criar `hooks/useSpendingPace.ts` com TanStack Query chamando o endpoint acima. Expõe: `dailySeries`, `monthlyGoal`, `monthlyAvg`, `unavoidableAvg`.

```
T1.3 [FE] 🟡 (paralelo com T1.2) — Componente SpendingPaceChart
```

Criar `components/SpendingPaceChart.tsx` usando Recharts `LineChart`.

- Duas linhas: mês atual (cor primária) e mês anterior (cinza tracejado).
- Três linhas de referência horizontais (`ReferenceLine`): meta (vermelho), média total (azul), média inevitável (laranja).
- Eixo X: dias 1–31; eixo Y: R$.

```
T1.4 [FE] 🟢 (depende de T1.2 + T1.3) — Integrar SpendingPaceChart na Overview
```

Adicionar seção "Ritmo de Gastos" na página `Overview.tsx` acima dos gráficos existentes.
Exibir delta percentual vs. mês anterior no título do card.

---

## S2 — Patrimônio e Resultado Parcial

**Branch:** `feat/net-worth-overview`

**Descrição:** KPIs de patrimônio (conta corrente + investimentos) e resultado parcial do mês com barra de meta.

**Dados necessários:**

- Saldo da conta corrente: `accounts_snapshot` (nova tabela — ver T2.1)
- Investimentos: tabela `investments` já existe
- Meta de saldo: `user_goals` (já existe)

---

### Tasks

> **Pré-requisito:** `accounts_snapshot` criada em **S0.T0.1**.

```
T2.1 [BE] 🔴 (depende de S0) — Ingerir accounts_snapshot no sync
```

Em `pluggy_api.py`, após fetch das accounts, salvar um snapshot de cada conta em `accounts_snapshot` com `snapshotted_at = datetime.now()`.
Criar `repositories/accounts_snapshot_repository.py` com método `upsert_snapshot(account)`.

```
T2.2 [BE] 🟡 (paralelo com T2.1) — Endpoint de patrimônio
```

Criar `GET /api/dashboard/net-worth` retornando:

```json
{
  "checking_balance": 12500.0,
  "investments_total": 85000.0,
  "net_worth": 97500.0,
  "history": [{"month": "2026-02", "net_worth": 95000.0}, ...]
}
```

Usa último snapshot de contas BANK + soma atual de `investments`.
Histórico de 12 meses usa `finance_history` para investimentos + snapshot mais recente de cada mês.

```
T2.3 [BE] 🟡 (paralelo com T2.1) — Endpoint de resultado parcial do mês
```

Expandir `GET /api/dashboard/data` ou criar `GET /api/dashboard/partial-result` retornando:

```json
{
  "income_so_far": 8000.0,
  "expenses_so_far": 3200.0,
  "partial_balance": 4800.0,
  "monthly_balance_goal": 5000.0,
  "goal_pct": 96.0
}
```

```
T2.4 [FE] 🟢 (depende de T2.2 + T2.3) — Componente NetWorthCard e PartialResultCard
```

- `components/NetWorthCard.tsx`: exibe patrimônio total com breakdown conta+investimentos.
- `components/PartialResultCard.tsx`: exibe resultado parcial com `ProgressBar` (barra colorida: verde se > 80% da meta, amarelo se 50–80%, vermelho se < 50%).
- Integrar em `Overview.tsx`.

---

## S3 — Próximas Despesas

**Branch:** `feat/upcoming-expenses`

**Descrição:** Card listando as próximas despesas programadas (recorrências e parcelas pendentes) dentro dos próximos 30 dias.

**Dependência:** Requer dados de recorrências (S4 deve estar ao menos com T4.1–T4.3 concluídos) e dados de parcelas (T7.1).

---

### Tasks

```
T3.1 [BE] 🔴 — Endpoint /api/dashboard/upcoming-expenses
```

Retorna lista dos próximos lançamentos previstos nos próximos 30 dias:

- Recorrentes: busca `recurrent_expenses` onde `next_occurrence` entre hoje e hoje+30d.
- Parcelas: busca `credit_transactions` onde `installment_number < total_installments` e projeta próximas datas.

```json
[
  {
    "description": "Netflix",
    "amount": 55.9,
    "due_date": "2026-03-20",
    "type": "subscription"
  },
  {
    "description": "Parcela 3/10 iPhone",
    "amount": 450.0,
    "due_date": "2026-03-18",
    "type": "installment"
  }
]
```

```
T3.2 [FE] 🟢 (depende de T3.1) — Componente UpcomingExpensesCard
```

Card com lista ordenada por data. Cada item: ícone por tipo, descrição, valor e data formatada. Exibe os 5 próximos com opção de expandir.
Integrar em `Overview.tsx`.

---

## S4 — Recorrências: Visualização e Cadastro

**Branch:** `feat/recurrences`

**Descrição:** Pipeline completo de recorrências: ingestão do Insights Recurrency, visualização de parcelas vs. contas fixas, cadastro manual.

---

> **Pré-requisitos:** `recurrent_expenses` criada em **S0.T0.2**; colunas de parcelas em **S0.T0.3**.

### Tasks

```
T4.1 [BE] 🔴 (depende de S0) — Ingerir Insights Recurrency no sync
```

Em `pluggy_api.py` (ou `services/pluggy_insights_service.py`), consumir `GET /recurrency?itemId=...` e salvar em `recurrent_expenses` com `source='pluggy'`.
Criar `repositories/recurrent_expenses_repository.py`.

```
T4.2 [BE] 🟡 (paralelo com T4.1, depende de S0) — Popular colunas de parcelas no sync
```

Atualizar `pluggy_api.py` para popular `installment_number`, `total_installments` e `total_amount` a partir de `creditCardMetadata` ao ingerir `credit_transactions`.

```
T4.3 [BE] 🟡 (paralelo com T4.1, depende de S0) — API CRUD de recorrências manuais
```

Blueprint `api/routes/recurrences_routes.py`:

- `GET /api/recurrences` — lista todas (pluggy + manual)
- `POST /api/recurrences` — cria recorrência manual
- `PUT /api/recurrences/<id>` — edita
- `DELETE /api/recurrences/<id>` — remove (só manuais)
- `PATCH /api/recurrences/<id>/toggle-unavoidable` — marca como "inevitável"

```
T4.4 [BE] 🟡 (depende de T4.1 + T4.2) — Endpoint de visão mensal de recorrências
```

`GET /api/recurrences/monthly?month=YYYY-MM` retornando:

```json
{
  "installments": {"total": 514.15, "items": [...]},
  "fixed_expenses": {"total": 257.73, "items": [...]},
  "history": [{"month": "2026-01", "installments": 480.0, "fixed": 250.0}, ...]
}
```

```
T4.5 [BE] 🟡 (depende de T4.2) — Endpoint de parcelas com progresso
```

`GET /api/recurrences/installments?month=YYYY-MM` retornando parcelas do mês com `pct_paid = installment_number / total_installments`.

```
T4.6 [FE] 🟡 (paralelo com T4.4, T4.5) — Página Recorrências: gráfico histórico
```

Em `pages/Recurrences.tsx` (nova página), adicionar `BarChart` (Recharts) com barras empilhadas: parcelas (azul) + fixas (verde) por mês. Card de totais do mês atual.

```
T4.7 [FE] 🟢 (depende de T4.5) — Card de parcelas com progress bar
```

Lista de parcelas do mês: descrição, categoria, valor, `ProgressBar` (n/total).

```
T4.8 [FE] 🟢 (depende de T4.3) — Card de contas fixas e formulário de cadastro manual
```

Lista de contas fixas com descrição, categoria, valor, data e frequência.
Formulário para adicionar recorrência manual com campos: descrição, valor, frequência (mensal/anual/semanal), próxima data, categoria, flag "inevitável".

```
T4.9 [FE] 🟢 — Registrar rota /recurrences no router
```

Adicionar entrada em `App.tsx` (ou router config) e link no menu de navegação.

---

## S5 — Receitas: Visualização e Cadastro

**Branch:** `feat/income-view`

**Descrição:** Painel de receitas recorrentes com evolução histórica e cadastro manual.

**Dados necessários:** Pluggy Insights Income + `finance_history`.

---

> **Pré-requisito:** `income_sources` criada em **S0.T0.4**.

### Tasks

```
T5.1 [BE] 🔴 (depende de S0) — Ingerir Insights Income no sync
```

Em `pluggy_api.py`, consumir `GET /income?itemId=...` e salvar em `income_sources`.
Criar `repositories/income_sources_repository.py`.

```
T5.2 [BE] 🟡 (paralelo com T5.1, depende de S0) — API CRUD de receitas manuais + histórico
```

Blueprint `api/routes/income_routes.py`:

- `GET /api/income/sources` — lista fontes de renda (pluggy + manual)
- `POST /api/income/sources` — cadastra renda manual
- `PUT /api/income/sources/<id>` / `DELETE /api/income/sources/<id>`
- `GET /api/income/history` — retorna `finance_history` com coluna `income` + breakdown de fontes por mês

```
T5.3 [FE] 🟢 (depende de T5.2) — Página Receitas
```

Nova página `pages/Income.tsx`:

- Gráfico de barras verticais (Receita por mês, últimos 12 meses) com Recharts `BarChart`.
- Linha sobre o gráfico para tendência.
- Card com fontes recorrentes detectadas: nome, valor médio, confiança, última ocorrência.
- Formulário de cadastro manual.

```
T5.4 [FE] 🟢 — Registrar rota /income no router e no menu
```

---

## S6 — Fluxo de Caixa

**Branch:** `feat/cash-flow`

**Descrição:** Análise de fluxo de caixa em janelas de 3 e 6 meses: resultado líquido, gastos por categoria, receitas — com comparativo entre períodos.

**Dados necessários:** `finance_history`, `pluggy_book_categories`.

---

### Tasks

```
T6.1 [BE] 🔴 — Endpoint /api/cash-flow
```

`GET /api/cash-flow?window=3&end_month=YYYY-MM` (window = 3 ou 6).
Retorna:

```json
{
  "current_window": {
    "months": ["2026-01", "2026-02", "2026-03"],
    "net_balance": [{"month": "...", "value": -3500.0}, ...],
    "expenses_by_category": [{"month": "...", "categories": {"Alimentação": 800, ...}}, ...],
    "income": [{"month": "...", "value": 8000.0}, ...],
    "period_total": -10488.39
  },
  "previous_window": {
    "months": ["2025-10", "2025-11", "2025-12"],
    "period_total": -10634.07,
    "delta_pct": 1.4
  }
}
```

Usa `finance_history` para net_balance e income; `pluggy_book_categories` para expenses_by_category.

```
T6.2 [FE] 🔴 (depende de T6.1) — Hook useCashFlow
```

`hooks/useCashFlow.ts` com parâmetro `window: 3 | 6` e `endMonth`.

```
T6.3 [FE] 🟡 (paralelo com T6.2) — Componente CashFlowBarChart
```

`components/CashFlowBarChart.tsx`: barras mensais (verde se positivo, vermelho se negativo) + linha tracejada do período anterior. Badge com delta % no cabeçalho.

```
T6.4 [FE] 🟡 (paralelo com T6.3) — Componente StackedCategoryChart
```

`components/StackedCategoryChart.tsx`: barras empilhadas por categoria, mês a mês. Usa mesma convenção de cores das categorias já definidas.

```
T6.5 [FE] 🟢 (depende de T6.2 + T6.3 + T6.4) — Página Fluxo de Caixa
```

Nova página `pages/CashFlow.tsx` com:

- Toggle 3 meses / 6 meses.
- Três seções: Resultado Líquido (`CashFlowBarChart`), Gastos (`StackedCategoryChart`), Receitas (`CashFlowBarChart` em modo income).
- Seletor de mês final.

```
T6.6 [FE] 🟢 — Registrar rota /cash-flow no router e no menu
```

---

## S7 — Faturas

**Branch:** `feat/bills-view`

**Descrição:** Visualização de faturas do cartão de crédito com breakdown: parcelas, recorrentes, compras avulsas.

**Dados necessários:** tabela `bills` (já existe), `credit_transactions` (com `installment_number` de T4.3).

---

> **Pré-requisitos:** colunas de bills em **S0.T0.5**; colunas de parcelas em **S0.T0.3** (via S4).

### Tasks

```
T7.1 [BE] 🔴 (depende de S0) — Atualizar sync para popular colunas novas de bills
```

Em `pluggy_api.py`, popular `is_open`, `payment_date` e `total_amount_paid` a partir de `bill.isOpen`, `bill.paymentDate`, `bill.totalAmountPaid`.
Atualizar `repositories/bill_repository.py` para incluir esses campos no upsert.

```
T7.2 [BE] 🔴 (depende de T7.1 e S4 concluída) — Endpoint /api/bills/monthly
```

`GET /api/bills/monthly?month=YYYY-MM` retorna:

```json
{
  "total": 2213.92,
  "month": "2026-02",
  "installments": 514.15,
  "recurrent": 257.73,
  "one_off": 1442.04,
  "is_open": false,
  "payment_date": "2026-03-05",
  "transactions": [...]
}
```

Classifica transações da fatura: installment (tem `installment_number`), recorrente (cruzamento com `recurrent_expenses`), avulsa (demais).

```
T7.3 [BE] 🟡 (paralelo com T7.2) — Endpoint /api/bills/history
```

`GET /api/bills/history` retorna totais por mês dos últimos 12 meses para o gráfico de linha do tempo.

```
T7.4 [FE] 🟢 (depende de T7.2 + T7.3) — Página Faturas
```

Nova página `pages/Bills.tsx`:

- `MonthNavigator` para navegar entre faturas.
- Card de resumo: total, breakdown (parcelas / recorrentes / avulsas) — layout como no mockup fornecido.
- Lista de transações da fatura com coluna de classificação.
- Mini gráfico de linha (últimos 6 meses) do valor total da fatura.

```
T7.5 [FE] 🟢 — Registrar rota /bills no router e no menu
```

---

## S8 — Categorias: Análises Avançadas e Automações

**Branch:** `feat/categories-analytics`

**Descrição:** Análises de gastos por categoria (pizza, linha, treemap hierárquico) e motor de automação por regras.

---

> **Pré-requisito:** `automation_rules` criada em **S0.T0.6**.

### Tasks

```
T8.1 [BE] 🔴 — Endpoint /api/categories/analytics
```

`GET /api/categories/analytics?month=YYYY-MM` retornando:

- `pie`: distribuição do mês atual por categoria.
- `timeline`: gastos dos últimos 12 meses por categoria (para o gráfico de linha).
- `hierarchy`: breakdown por grupo de categoria → subcategorias, com valores absolutos e %.

```
T8.2 [BE] 🟡 (depende de S0) — Motor de execução de automações
```

Criar `services/automation_service.py` com:

- `apply_rules(transaction)` — avalia condições em ordem de prioridade e executa ações.
- `run_all()` — aplica regras a todas as transações não excluídas.
  Chamado no final do sync (`pluggy_api.py`).

```
T8.3 [BE] 🟡 (paralelo com T8.2, depende de S0) — API CRUD de automações
```

Blueprint `api/routes/automation_routes.py`:

- `GET /api/automations` — lista regras
- `POST /api/automations` — cria regra
- `PUT /api/automations/<id>` — edita
- `DELETE /api/automations/<id>` — remove
- `POST /api/automations/<id>/run` — aplica regra manualmente

```
T8.4 [FE] 🔴 (depende de T8.1) — Componente CategoryTimeline (linha com filtro)
```

`components/CategoryTimeline.tsx`: Recharts `LineChart` com linhas por categoria. Checkbox list para selecionar até 6 categorias. Filtro de período.

```
T8.5 [FE] 🟡 (paralelo com T8.4) — Componente HierarchyBarChart (treemap vertical)
```

`components/HierarchyBarChart.tsx`: barras horizontais agrupadas por parent_category, subdivididas por subcategoria. Tooltip detalhado.

```
T8.6 [FE] 🟢 (depende de T8.4 + T8.5) — Página Categorias
```

Expandir (ou reformular) `pages/Categories.tsx`:

- Seção 1: `CategoryPieChart` existente (mês a mês com `MonthNavigator`).
- Seção 2: `CategoryTimeline` com seletor de categorias.
- Seção 3: `HierarchyBarChart`.

```
T8.7 [FE] 🟢 (depende de T8.3) — Página/modal de Automações
```

Interface para gerenciar regras: lista com enable/disable toggle, formulário de criação com editor de condições (add/remove linhas de condição) e ações.

---

## S9 — Projeção Patrimonial

**Branch:** `feat/patrimony-projection`

**Descrição:** Gráfico de barras projetando evolução do patrimônio com base em receitas recorrentes, contas fixas e parcelamentos pendentes.

**Dependências:** Requer S4 (recorrências) e S5 (receitas) concluídas.

---

### Tasks

```
T9.1 [BE] 🔴 — Serviço de projeção patrimonial
```

Criar `services/projection_service.py`:

- Ponto de partida: patrimônio atual (conta corrente + investimentos).
- Para cada mês futuro (próximos 12): somar receitas recorrentes (`income_sources`), subtrair contas fixas (`recurrent_expenses` onde `frequency = MONTHLY`), subtrair parcelas pendentes (de `credit_transactions` agrupadas por mês de vencimento projetado).
- Retorna série mensal de patrimônio projetado.

```
T9.2 [BE] 🟢 (depende de T9.1) — Endpoint /api/projection
```

`GET /api/projection?months=12` retornando:

```json
{
  "current_net_worth": 97500.0,
  "projection": [
    {"month": "2026-04", "net_worth": 99200.0, "income": 8000.0, "expenses": 6300.0},
    ...
  ]
}
```

```
T9.3 [FE] 🟡 (paralelo com T9.2) — Componente ProjectionChart
```

`components/ProjectionChart.tsx`: Recharts `BarChart` com barras por mês (patrimônio projetado). Linha de tendência sobreposta. Tooltip com breakdown receita/despesa.

```
T9.4 [FE] 🟢 (depende de T9.2 + T9.3) — Página Projeção
```

Nova página `pages/Projection.tsx` com:

- Card de patrimônio atual.
- `ProjectionChart` para os próximos 12 meses.
- Lista das premissas consideradas: receitas recorrentes, despesas fixas, parcelas pendentes com valor total por mês.

```
T9.5 [FE] 🟢 — Registrar rota /projection no router e no menu
```

---

## S10 — Otimizacao de Schema e Indices

**Branch:** `feat/schema-optimization`

**Descricao:** Adiciona indices nas tabelas principais (zero indices atualmente — full-table-scan em todas as queries), remove colunas mortas, consolida migrations runtime no `init_db.py`, e remove tabela denormalizada `pluggy_book_categories`. Objetivo: performance, integridade do schema e codigo mais limpo.

**Problemas identificados:**
- Zero indices em todas as tabelas — qualquer WHERE ou JOIN faz full-table-scan
- `credit_transactions.total_amount` e populada pelo sync mas NUNCA lida por nenhum repositorio/servico
- `bank_expenses`/`credit_expenses` em `finance_history` foram adicionadas via `_ensure_columns()` runtime (ALTER TABLE) em vez de estarem no CREATE TABLE do `init_db.py`
- `pluggy_book_categories` tem 24 colunas denormalizadas (m1_avg...m12_max) e a logica de insights pode usar a tabela generica `pluggy_insights`
- `bank_transactions.type` — verificar se e usado em algum calculo ou pode ser ignorado

---

### Tasks

```
T10.1 [DB] -- Adicionar indices nas tabelas principais
```

Criar `scripts/add_indexes.py` para bancos existentes e adicionar os CREATE INDEX ao `init_db.py`:

Indices necessarios (~12):
- `bank_transactions`: `(date)`, `(category_id)`, `(excluded, date)`
- `credit_transactions`: `(date)`, `(category_id)`, `(status)`, `(excluded, date)`
- `splitwise`: `(date)`, `(transaction_id)`
- `finance_history`: `(month)` (ja e PK, ok)
- `investments`: `(date)`, `(type)`
- `accounts_snapshot`: `(snapshotted_at)`
- `bills`: `(due_date)`, `(account_id)`
- `recurrent_expenses`: `(category_id)`
- `income_sources`: `(last_occurrence)`

Script deve ser idempotente (`CREATE INDEX IF NOT EXISTS`).
Validar com `EXPLAIN QUERY PLAN` nas queries mais usadas.

**Arquivos:** `init_db.py`, `scripts/add_indexes.py` (novo)

```
T10.2 [DB] -- Remover/deprecar credit_transactions.total_amount
```

1. Verificar que nenhum repositorio/servico le `total_amount` (confirmado: so e escrito em `transaction_repository.py:435`).
2. Nao remover a coluna do CREATE TABLE (SQLite nao suporta DROP COLUMN facilmente) — apenas:
   - Adicionar comentario `-- DEPRECATED: never read, kept for backward compat` no CREATE TABLE.
   - Parar de popular no upsert do `transaction_repository.py` (setar como NULL).
3. Adicionar teste que confirma que nenhum SELECT le essa coluna.

**Arquivos:** `init_db.py`, `repositories/transaction_repository.py`, `tests/repositories/test_transaction_repository.py`

```
T10.3 [DB] -- Consolidar bank_expenses/credit_expenses no CREATE TABLE
```

1. Verificar que `bank_expenses` e `credit_expenses` ja estao no CREATE TABLE de `finance_history` em `init_db.py` (confirmado: ja estao na linha 104-105).
2. Remover `_ensure_columns()` do `finance_history_repository.py` — nao e mais necessario.
3. Remover qualquer chamada a `_ensure_columns()` nos servicos.
4. Testar que o repositorio funciona sem o fallback de ALTER TABLE.

**Arquivos:** `repositories/finance_history_repository.py`, `services/finance_history_service.py`

```
T10.4 [DB] -- Remover tabela pluggy_book_categories e codigo associado
```

1. Remover CREATE TABLE de `pluggy_book_categories` do `init_db.py`.
2. Adicionar `DROP TABLE IF EXISTS pluggy_book_categories` ao `RESET_SQL`.
3. Remover `pluggy_insights_repository.py` (ou metodos que operam nessa tabela).
4. Remover chamadas em `services/pluggy_insights_service.py` que usam essa tabela.
5. Criar script `scripts/drop_book_categories.py` para bancos existentes.
6. A tabela `pluggy_insights` (generica, com coluna `data` JSON) substitui essa funcionalidade.

**Arquivos:** `init_db.py`, `repositories/pluggy_insights_repository.py`, `services/pluggy_insights_service.py`, `scripts/drop_book_categories.py` (novo)

```
T10.5 [BE] -- Auditar uso de bank_transactions.type
```

1. Grep por `\.type` e `["type"]` nos repositorios e servicos que tocam `bank_transactions`.
2. Documentar se `type` e usado em algum calculo de negocio ou apenas informativo.
3. Se apenas informativo: manter coluna, nenhuma acao. Se nao usado: marcar como deprecated.

**Arquivos:** nenhuma mudanca esperada — apenas auditoria e documentacao

**Criterios de aceite S10:**
- [x] `EXPLAIN QUERY PLAN` mostra uso de indice nas 5 queries mais frequentes
- [x] `_ensure_columns()` removido, testes passam
- [x] `pluggy_book_categories` removida do schema e codigo
- [x] `total_amount` nao e mais populada em novos upserts
- [x] `pytest tests/` passa, coverage >= 80% (89.07%)
- [x] `bank_transactions.type` auditado — coluna ativa, sem mudancas necessarias

---

## S11 — Docker e Containerizacao

**Branch:** `feat/docker`

**Descricao:** Containerizar a aplicacao para rodar em qualquer OS sem setup manual de Python/Node. Multi-stage build (Node para frontend, Python para runtime). Volume para persistencia do SQLite e `.env`.

---

### Tasks

```
T11.1 [INFRA] -- Dockerfile multi-stage
```

Criar `Dockerfile` com dois estagios:

**Stage 1 — Frontend build:**
- Base: `node:18-alpine`
- `COPY frontend/ .` → `npm ci` → `npm run build`
- Output: `static/` com assets compilados

**Stage 2 — Python runtime:**
- Base: `python:3.11-slim`
- `COPY --from=stage1 static/ static/`
- `COPY requirements.txt .` → `pip install --no-cache-dir`
- `COPY . .`
- `EXPOSE 5000`
- `CMD ["python", "app.py"]`

**Arquivos:** `Dockerfile` (novo)

```
T11.2 [INFRA] -- docker-compose.yml
```

```yaml
services:
  app:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data      # finance.db persistido
      - ./.env:/app/.env:ro   # credenciais
    environment:
      - DB_PATH=/app/data/finance.db
```

Ajustar `DB_PATH` no codigo para aceitar variavel de ambiente (fallback para `finance.db`).

**Arquivos:** `docker-compose.yml` (novo), `init_db.py`, `repositories/base_repository.py`

```
T11.3 [INFRA] -- .dockerignore
```

```
node_modules/
frontend/node_modules/
__pycache__/
*.pyc
.env
finance.db
.git/
tests/
test_scripts/
.playwright-mcp/
```

**Arquivos:** `.dockerignore` (novo)

```
T11.4 [BE] -- app.run com host configuravel
```

Em `app.py`, alterar `app.run()` para:

```python
app.run(host=os.getenv("FLASK_HOST", "127.0.0.1"), debug=True)
```

No Docker, setar `FLASK_HOST=0.0.0.0`. Localmente, mantem `127.0.0.1` por seguranca.

**Arquivos:** `app.py`

**Criterios de aceite S11:**
- [ ] `docker build -t personal-finance .` completa sem erros
- [ ] `docker compose up` sobe a aplicacao e serve o frontend
- [ ] Dados persistem entre restarts (volume montado)
- [ ] `.env` nao e copiado para a imagem (apenas montado)

---

## S12 — Onboarding de Primeiro Uso

**Branch:** `feat/onboarding`

**Descricao:** Fluxo guiado para novos usuarios: detectar se o banco esta vazio, guiar configuracao de credenciais, executar primeiro sync, e redirecionar para o dashboard quando pronto. Sem onboarding, um usuario novo ve dashboards vazios sem entender o que fazer.

**Dependencias:** S10 (schema limpo) + S11 (Docker, para garantir que o fluxo funciona from scratch)

---

### Tasks

```
T12.1 [BE] -- GET /api/onboarding/status
```

Criar `api/routes/onboarding_routes.py` e `services/onboarding_service.py`:

```python
GET /api/onboarding/status
# Retorna:
{
    "has_pluggy_items": bool,      # pluggy_items tem registros
    "has_transactions": bool,      # bank_transactions ou credit_transactions tem registros
    "has_history": bool,           # finance_history tem registros
    "is_complete": bool            # todos os acima sao True
}
```

Registrar blueprint em `app.py` em `/api/onboarding`.

**Arquivos:** `api/routes/onboarding_routes.py` (novo), `services/onboarding_service.py` (novo), `app.py`

```
T12.2 [BE] -- POST /api/onboarding/full-sync
```

Endpoint que executa o sync completo (equivalente a rodar `pluggy_api.py` programaticamente):

1. Fetch items e contas
2. Fetch transacoes (non_recent + recent)
3. Backfill finance_history
4. Retornar status de cada etapa

Reutilizar funcoes existentes de `pluggy_api.py` — extrair para funcoes chamvaveis se necessario.

**Arquivos:** `api/routes/onboarding_routes.py`, `pluggy_api.py`

```
T12.3 [BE] -- Consolidar rebuild_all_months
```

Garantir que `rebuild_all_months` em `finance_history_service.py` e acessivel via endpoint:

```
POST /api/finance-history/rebuild-all
```

Ja pode existir parcialmente — verificar e consolidar.

**Arquivos:** `api/routes/finance_history_routes.py`, `services/finance_history_service.py`

```
T12.4 [FE] -- Wizard de onboarding
```

`frontend/src/pages/Onboarding.tsx`:

Steps:
1. "Bem-vindo" — explicacao do app
2. "Credenciais" — verificar se `.env` esta configurado (GET /api/pluggy/status)
3. "Conectar" — disparar full-sync (POST /api/onboarding/full-sync) com progress bar
4. "Pronto" — resumo do que foi importado, botao para ir ao Dashboard

Polling de status durante sync (ou usar Server-Sent Events se viavel).

**Arquivos:** `frontend/src/pages/Onboarding.tsx` (novo), `frontend/src/App.tsx`

```
T12.5 [FE] -- Redirect automatico se onboarding incompleto
```

Em `App.tsx`, antes de renderizar rotas normais:
- Chamar `GET /api/onboarding/status`
- Se `is_complete === false`, redirecionar para `/onboarding`
- Se completo, renderizar normalmente

Adicionar rota `/onboarding` no router.

**Arquivos:** `frontend/src/App.tsx`

**Criterios de aceite S12:**
- [ ] Banco vazio redireciona para onboarding
- [ ] Full-sync via onboarding popula todas as tabelas
- [ ] Apos onboarding, Dashboard mostra dados
- [ ] Re-visitar /onboarding apos setup mostra "ja configurado"

---

## S13 — Integridade de Dados e Gaps

**Branch:** `feat/data-integrity`

**Descricao:** Detectar e alertar sobre gaps nos dados: dias sem transacoes (> 6 dias indica que Pluggy perdeu cobertura), meses sem finance_history, e tempo desde ultimo sync. Consequencia de parar sync por > 6 dias: a janela de 1 ano da Pluggy avanca e dados antigos sao perdidos permanentemente.

**Dependencias:** S12 (onboarding completo, banco populado)

---

### Tasks

```
T13.1 [BE] -- Servico de deteccao de gaps
```

Criar `services/data_integrity_service.py`:

```python
class DataIntegrityService:
    def check_transaction_gaps(self, days_threshold=6) -> list[dict]:
        """Detecta periodos sem transacoes bancarias > threshold dias."""
        # Query: ordenar datas de bank_transactions, calcular gaps entre datas consecutivas
        # Retornar lista de {"start": date, "end": date, "gap_days": int}

    def check_history_coverage(self) -> dict:
        """Verifica quais meses tem transacoes mas nao tem finance_history."""
        # Comparar meses em bank_transactions vs finance_history

    def get_sync_status(self) -> dict:
        """Retorna last_sync_at e dias desde ultimo sync."""
        # Ler de settings tabela
```

**Arquivos:** `services/data_integrity_service.py` (novo)

```
T13.2 [BE] -- Endpoints de relatorio e gaps
```

Criar `api/routes/data_integrity_routes.py`:

```
GET /api/data-integrity/report
# Retorna: { "transaction_gaps": [...], "history_gaps": [...], "last_sync": {...}, "alerts": [...] }
```

Alertas automaticos:
- `"warning"`: > 3 dias sem sync
- `"critical"`: > 6 dias sem sync (risco de perda de dados)
- `"info"`: meses sem finance_history

**Arquivos:** `api/routes/data_integrity_routes.py` (novo), `app.py`

```
T13.3 [BE] -- Registrar last_sync_at em settings
```

Em `pluggy_api.py`, ao final de cada sync bem-sucedido:

```python
settings_repo.upsert("last_sync_at", datetime.now().isoformat())
```

**Arquivos:** `pluggy_api.py`, `repositories/settings_repository.py`

```
T13.4 [FE] -- SyncStatusCard
```

Componente reutilizavel que mostra:
- Ultimo sync (data/hora)
- Dias desde ultimo sync (com cor: verde < 3, amarelo 3-6, vermelho > 6)
- Numero de gaps detectados
- Cobertura de meses com historico

Usar no Dashboard (topo) e em Settings.

**Arquivos:** `frontend/src/components/SyncStatusCard.tsx` (novo)

```
T13.5 [FE] -- Pagina/secao de status de dados
```

Adicionar secao em Settings ou pagina dedicada `/data-status`:
- Lista de gaps com datas
- Meses sem cobertura de historico
- Botao "Recalcular historico" (reutilizar endpoint de S14)

**Arquivos:** `frontend/src/pages/Settings.tsx` ou `frontend/src/pages/DataStatus.tsx` (novo)

**Criterios de aceite S13:**
- [ ] Gaps > 6 dias sao detectados e exibidos
- [ ] Alerta critico aparece quando sync atrasado > 6 dias
- [ ] last_sync_at e atualizado a cada sync
- [ ] SyncStatusCard visivel no Dashboard

---

## S14 — Backfill Refinado

**Branch:** `feat/backfill-refined`

**Descricao:** Evolucao do backfill para suportar multiplos anchors (snapshots de patrimonio), forward-fill de dados faltantes, e re-importacao segura que preserva dados manuais. Substitui o backfill simples por um mais robusto.

**Dependencias:** S13 (deteccao de gaps informa quais meses precisam de backfill)

---

### Tasks

```
T14.1 [BE] -- Backfill com multiplos anchors e forward-fill
```

Evoluir `backfill_from_transactions` em `finance_history_service.py`:

1. **Anchor points:** usar `accounts_snapshot` como pontos de referencia para `total_cash` e `investments` — interpolar entre snapshots para meses intermediarios.
2. **Forward-fill:** para meses sem snapshot, propagar ultimo valor conhecido de `total_cash`/`investments`.
3. **Calculo de income/expenses:** manter logica atual (soma de transacoes do mes).

**Arquivos:** `services/finance_history_service.py`

```
T14.2 [BE] -- Re-importacao segura
```

Ao recalcular um mes que ja tem dados em `finance_history`:

1. Se `meal_allowance` ou `credit_card_bill` foram definidos manualmente (via Settings), preservar esses valores.
2. Sobrescrever apenas campos calculados (`income`, `expenses`, `bank_expenses`, `credit_expenses`).
3. Flag `overwrite_manual=False` por default.

**Arquivos:** `services/finance_history_service.py`, `repositories/finance_history_repository.py`

```
T14.3 [BE] -- POST /api/finance-history/rebuild com opcoes
```

Endpoint expandido:

```
POST /api/finance-history/rebuild
Body: { "months": ["2025-01", "2025-02"], "overwrite": false }
# Se months vazio/ausente: rebuild de todos os meses disponiveis
```

Retorna relatorio detalhado: meses processados, dados preservados, erros.

**Arquivos:** `api/routes/finance_history_routes.py`

```
T14.4 [FE] -- UI de backfill em Settings
```

Em Settings, secao "Dados Historicos":
- Seletor de meses (multi-select ou range)
- Checkbox "Sobrescrever dados manuais"
- Botao "Recalcular"
- Resultado inline com detalhes

**Arquivos:** `frontend/src/pages/Settings.tsx`

**Criterios de aceite S14:**
- [ ] Backfill interpola total_cash entre snapshots
- [ ] Dados manuais (meal_allowance, credit_card_bill) preservados por default
- [ ] Rebuild de meses especificos funciona via API
- [ ] UI em Settings permite selecionar meses e recalcular

---

## S15 — Metas de Consumo

**Branch:** `feat/spending-goals`

**Descricao:** Permite ao usuario definir sua meta mensal total de gastos (e opcionalmente por categoria) atraves da pagina de Configuracoes. As metas ficam persistidas em `user_goals` e alimentam as linhas de referencia do grafico de Ritmo de Gastos (S1) e a barra de progresso do Resultado Parcial (S2).

**Dependencias:** Independente — pode ser feita a qualquer momento.

**Dados necessarios:** Tabela `user_goals` (ja existe). Categorias em `categories` (ja existe).

---

### Tasks

```
T15.1 [BE] -- API CRUD de metas de consumo
```

Criar blueprint `api/routes/goals_routes.py` e registrar em `app.py` em `/api/goals`:

- `GET /api/goals` — lista todas as metas (`category_id`, `type`, `amount`, `period`).
- `POST /api/goals` — cria ou substitui meta (`UNIQUE(category_id, type)` -> upsert).
- `PUT /api/goals/<id>` — atualiza `amount` e/ou `period`.
- `DELETE /api/goals/<id>` — remove meta.

Expandir `repositories/user_goals_repository.py` (ja existe com `get_total_monthly_goal`) com `get_all`, `upsert`, `delete`.

**Arquivos:** `api/routes/goals_routes.py` (novo), `repositories/user_goals_repository.py`, `app.py`

```
T15.2 [FE] -- Hook useGoals
```

`hooks/useGoals.ts` com TanStack Query:

- `useGoals()` — lista metas (`GET /api/goals`).
- `useSaveGoal()` — mutation para criar/atualizar (`POST` ou `PUT`).
- `useDeleteGoal()` — mutation para remover.

**Arquivos:** `frontend/src/hooks/useGoals.ts` (novo)

```
T15.3 [FE] -- Componente GoalsEditor
```

`components/GoalsEditor.tsx`:

- Campo numerico "Meta mensal total de gastos" (row com `category_id = NULL`).
- Lista expansivel de metas por categoria: seletor de categoria (dropdown com categorias existentes) + campo de valor + botao remover.
- Botao "Salvar" por linha (feedback inline de sucesso/erro).
- Sem modal — painel inline dentro da pagina de Configuracoes.

**Arquivos:** `frontend/src/components/GoalsEditor.tsx` (novo)

```
T15.4 [FE] -- Integrar GoalsEditor em Settings
```

Na pagina `pages/Settings.tsx` (ja existe), adicionar secao "Metas de Consumo" abaixo das configuracoes existentes de vale-refeicao e cartao de credito.
Exibir meta total atual como subtitulo da secao antes de abrir o editor.

**Arquivos:** `frontend/src/pages/Settings.tsx`

**Criterios de aceite S15:**
- [ ] CRUD de metas funciona via API
- [ ] GoalsEditor renderiza em Settings com categorias existentes
- [ ] Meta total e metas por categoria persistem entre sessoes
- [ ] Alimenta S1 (linha Meta) e S2 (barra de progresso)

---

## S16 — Transicao Mes/Ciclo Fatura

**Branch:** `feat/billing-cycle`

**Descricao:** Mapear transacoes de credito ao mes de fatura correto (billing_month) em vez de usar a data da transacao. Uma compra em 15/mar com close_date em 10/mar pertence a fatura de abril, nao de marco. Sem isso, o resumo financeiro mensal mostra gastos no mes errado.

**Dependencias:** S14 (backfill refinado — precisa recalcular historico com billing_month correto)

---

### Tasks

```
T16.1 [BE] -- Servico de mapeamento transacao->fatura
```

Criar `services/billing_cycle_service.py`:

```python
class BillingCycleService:
    def get_billing_month(self, transaction_date: str, close_date: str) -> str:
        """Retorna YYYY-MM da fatura a que a transacao pertence."""
        # Se transaction_date <= close_date: fatura do mes do close_date
        # Se transaction_date > close_date: fatura do mes seguinte
```

Usar `close_date` da tabela `bills` (ja populada pelo sync).

**Arquivos:** `services/billing_cycle_service.py` (novo)

```
T16.2 [DB] -- Coluna billing_month em credit_transactions
```

Adicionar coluna `billing_month TEXT` em credit_transactions no `init_db.py`.
Script `scripts/add_billing_month.py` para bancos existentes (ALTER TABLE + popular com base nas bills).

**Arquivos:** `init_db.py`, `scripts/add_billing_month.py` (novo)

```
T16.3 [BE] -- Adaptar get_credit_expenses para usar billing_month
```

Em `transaction_repository.py`, alterar queries de despesas de credito para filtrar por `billing_month` em vez de `date` quando disponivel:

```sql
-- Antes:
WHERE substr(date, 1, 7) = ?
-- Depois:
WHERE COALESCE(billing_month, substr(date, 1, 7)) = ?
```

Fallback para `date` quando `billing_month` e NULL (transacoes antigas sem mapeamento).

**Arquivos:** `repositories/transaction_repository.py`, `services/finance_summary_service.py`

```
T16.4 [BE] -- Testes de cenarios de transicao
```

Testar:
- Compra em 15/mar, close_date 10/mar -> billing_month = "2026-04"
- Compra em 05/mar, close_date 10/mar -> billing_month = "2026-03"
- Meses com 28/30/31 dias
- Transacao sem bill associada (fallback para date)

**Arquivos:** `tests/services/test_billing_cycle_service.py` (novo)

```
T16.5 [FE] -- Indicador de ciclo na UI de Faturas
```

Na pagina de Bills, mostrar:
- Close date e due date da fatura atual
- Indicador visual de qual fatura uma transacao pertence
- Filtro por billing_month (alem de por data de transacao)

**Arquivos:** `frontend/src/pages/Bills.tsx`

**Criterios de aceite S16:**
- [ ] billing_month calculado corretamente para todos os cenarios de teste
- [ ] Resumo financeiro usa billing_month para credito
- [ ] Transacoes antigas (sem billing_month) continuam funcionando via fallback
- [ ] UI mostra ciclo de fatura claramente

---

## Mapa de Dependencias (resumo)

```
S0-S9 ── CONCLUIDAS ──────────────────────────────────────────────────────────

S10 (Schema/Indices) ──┐
                       ├──> S12 (Onboarding) ──> S13 (Integridade) ──> S14 (Backfill) ──> S16 (Ciclo Fatura)
S11 (Docker) ──────────┘

S15 (Metas de Consumo) ── independente ────────────────────────────────────────

Detalhamento de tasks dentro de cada historia:

S10: T10.1 (indices) ──> T10.2..T10.5 (podem ser paralelos)
S11: T11.1 (Dockerfile) ──> T11.2 (compose) ──> T11.3 (dockerignore) | T11.4 (host config)
S12: T12.1 (status) ──> T12.2 (full-sync) ──> T12.4 (wizard FE) ──> T12.5 (redirect)
     T12.3 (rebuild endpoint) paralelo
S13: T13.1 (gaps service) ──> T13.2 (endpoints) ──> T13.4 (SyncStatusCard) ──> T13.5 (pagina)
     T13.3 (last_sync_at) paralelo
S14: T14.1 (anchors) ──> T14.2 (safe reimport) ──> T14.3 (API) ──> T14.4 (UI)
S15: T15.1 (API goals) ──> T15.2 (hook) ──> T15.4 (integrar Settings)
     T15.3 (GoalsEditor) paralelo com T15.2
S16: T16.1 (servico) ──> T16.2 (coluna DB) ──> T16.3 (adaptar queries) ──> T16.5 (UI)
     T16.4 (testes) paralelo com T16.3
```

---

## Ordem de Entrega Recomendada

| Prioridade | Historia                              | Justificativa                                                      |
| ---------- | ------------------------------------- | ------------------------------------------------------------------ |
| 1          | **S10 — Schema/Indices**              | Fundacao: performance e limpeza de schema para tudo que vem depois |
| 1          | **S11 — Docker**                      | Paralelo com S10, habilita onboarding from scratch                 |
| 1          | **S15 — Metas de Consumo**            | Independente, pode correr em paralelo com S10/S11                  |
| 2          | **S12 — Onboarding**                  | Depende de S10+S11, desbloqueia fluxo de primeiro uso              |
| 3          | **S13 — Integridade de Dados**        | Depende de S12, protege contra perda de dados por sync atrasado    |
| 4          | **S14 — Backfill Refinado**           | Depende de S13, melhora qualidade do historico financeiro           |
| 5          | **S16 — Transicao Mes/Ciclo Fatura**  | Depende de S14, corrige alocacao de despesas de credito por fatura |

---

_Documento gerado em 2026-03-13. Ultima revisao: 2026-03-21._

---

## LEMBRETE PARA O AGENTE — Atualizar este documento ao final de cada sessao

> **IMPORTANTE:** Antes de encerrar qualquer sessao de trabalho, o agente DEVE atualizar este documento:
>
> 1. **Atualizar a tabela "STATUS ATUAL"** no topo do documento:
>    - `Proxima historia a implementar` — apontar para a proxima historia pendente
>    - `Proxima task a implementar` — apontar para a proxima task dentro da historia
>    - `Historias concluidas` — adicionar a historia recem-finalizada (se aplicavel)
>    - `Branch ativa` — atualizar com a branch atual ou "main" se mergeou
>    - `Mudancas nao commitadas` — listar ou limpar
>    - `Bloqueios conhecidos` — registrar qualquer impedimento encontrado
> 2. **Atualizar "O que fazer agora"** com instrucoes claras para a proxima sessao
> 3. **Marcar tasks concluidas** dentro da historia com `[DONE]` no inicio da linha
> 4. **Marcar historia concluida** no indice com ~~strikethrough~~ e `[CONCLUIDA]`
> 5. **Atualizar `Ultima revisao`** no cabecalho com a data atual
>
> Isso garante que qualquer nova sessao do agente saiba exatamente onde continuar.
