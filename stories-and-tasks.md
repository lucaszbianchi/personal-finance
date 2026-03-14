# Stories & Tasks — Personal Finance Roadmap

> **Tech Lead:** Documento de planejamento para as features solicitadas.
> **Data:** 2026-03-13 · **Última revisão:** 2026-03-13
> **Convenção de branches:** `feat/<slug-da-história>`

---

## Legenda

| Símbolo | Significado                                                 |
| ------- | ----------------------------------------------------------- |
| 🔴      | Bloqueante — deve ser concluída antes de tasks dependentes  |
| 🟡      | Pode ser feita em paralelo com tasks sem dependência        |
| 🟢      | Independente, pode ser feita a qualquer momento na história |
| `[BE]`  | Tarefa de backend (Python/Flask/SQLite)                     |
| `[FE]`  | Tarefa de frontend (React/TypeScript)                       |
| `[DB]`  | Migração / schema de banco de dados                         |

---

## Índice de Histórias

0. [S0 — Migrações de Banco de Dados ⚠️ pré-requisito global](#s0--migrações-de-banco-de-dados)
1. [S1 — Ritmo de Gastos (Visão Geral)](#s1--ritmo-de-gastos)
2. [S2 — Patrimônio e Resultado Parcial (Visão Geral)](#s2--patrimônio-e-resultado-parcial)
3. [S3 — Próximas Despesas (Visão Geral)](#s3--próximas-despesas)
4. [S4 — Recorrências: Visualização e Cadastro](#s4--recorrências-visualização-e-cadastro)
5. [S5 — Receitas: Visualização e Cadastro](#s5--receitas-visualização-e-cadastro)
6. [S6 — Fluxo de Caixa](#s6--fluxo-de-caixa)
7. [S7 — Faturas (Cartão de Crédito)](#s7--faturas)
8. [S8 — Categorias: Análises Avançadas e Automações](#s8--categorias-análises-avançadas-e-automações)
9. [S9 — Projeção Patrimonial](#s9--projeção-patrimonial)
10. [S10 — Metas de Consumo](#s10--metas-de-consumo)
11. [S11 — Backfill de Histórico Financeiro](#s11--backfill-de-histórico-financeiro)

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

## S10 — Metas de Consumo

**Branch:** `feat/spending-goals`

**Descrição:** Permite ao usuário definir sua meta mensal total de gastos (e opcionalmente por categoria) através da página de Configurações. As metas ficam persistidas em `user_goals` e alimentam as linhas de referência do gráfico de Ritmo de Gastos (S1) e a barra de progresso do Resultado Parcial (S2).

**Dados necessários:** Tabela `user_goals` (já existe). Categorias em `categories` (já existe).

---

### Tasks

```
T10.1 [BE] 🔴 — API CRUD de metas de consumo
```

Criar blueprint `api/routes/goals_routes.py` e registrar em `app.py` em `/api/goals`:

- `GET /api/goals` — lista todas as metas (`category_id`, `type`, `amount`, `period`).
- `POST /api/goals` — cria ou substitui meta (`UNIQUE(category_id, type)` → upsert).
- `PUT /api/goals/<id>` — atualiza `amount` e/ou `period`.
- `DELETE /api/goals/<id>` — remove meta.

Criar `repositories/user_goals_repository.py` com os métodos completos (já existe o arquivo com `get_total_monthly_goal`; expandir com `get_all`, `upsert`, `delete`).

```
T10.2 [FE] 🔴 (depende de T10.1) — Hook useGoals
```

`hooks/useGoals.ts` com TanStack Query:

- `useGoals()` — lista metas (`GET /api/goals`).
- `useSaveGoal()` — mutation para criar/atualizar (`POST` ou `PUT`).
- `useDeleteGoal()` — mutation para remover.

```
T10.3 [FE] 🟡 (paralelo com T10.2) — Componente GoalsEditor
```

`components/GoalsEditor.tsx`:

- Campo numérico "Meta mensal total de gastos" (row com `category_id = NULL`).
- Lista expansível de metas por categoria: seletor de categoria (dropdown com categorias existentes) + campo de valor + botão remover.
- Botão "Salvar" por linha (feedback inline de sucesso/erro).
- Sem modal — painel inline dentro da página de Configurações.

```
T10.4 [FE] 🟢 (depende de T10.2 + T10.3) — Integrar GoalsEditor em Settings
```

Na página `pages/Settings.tsx` (já existe), adicionar seção "Metas de Consumo" abaixo das configurações existentes de vale-refeição e cartão de crédito.
Exibir meta total atual como subtítulo da seção antes de abrir o editor.

---

## S11 — Backfill de Histórico Financeiro

**Branch:** `feat/history-backfill`

**Descrição:** Garante que `finance_history` esteja completo para todos os meses com transações disponíveis nas tabelas `bank_transactions` e `credit_transactions`. O backfill é executado automaticamente ao final de cada sincronização, preenchendo apenas meses que ainda não têm `income` e `expenses` registrados. Também expõe um endpoint de trigger manual para uso via Configurações.

**Motivação:** `finance_history` é pré-requisito para `monthly_avg` no gráfico de Ritmo de Gastos (S1), para o histórico de patrimônio (S2) e para o Fluxo de Caixa (S6). O sync atual só popula o mês corrente; meses históricos ficam sem registro mesmo com dados disponíveis.

---

### Tasks

```
T11.1 [BE] 🔴 — Método backfill em FinanceHistoryService
```

Adicionar `backfill_from_transactions(overwrite: bool = False) -> dict` em `services/finance_history_service.py`:

1. Descobrir meses disponíveis: `SELECT DISTINCT substr(date,1,7) FROM bank_transactions UNION SELECT DISTINCT substr(date,1,7) FROM credit_transactions ORDER BY 1`.
2. Para cada mês descoberto: se `overwrite=False`, pular meses que já têm `income IS NOT NULL AND expenses IS NOT NULL` em `finance_history`.
3. Chamar `update_finance_history_from_sync(month)` (método já existente) para cada mês pendente.
4. Retornar `{"backfilled": [...meses processados...], "skipped": [...meses já existentes...]}`.

```
T11.2 [BE] 🟡 (paralelo com T11.1) — Chamar backfill ao final do sync
```

Em `pluggy_api.py`, após todas as demais atualizações de `finance_history`, adicionar chamada:

```python
fh_service.backfill_from_transactions(overwrite=False)
```

Assim cada sync futuro preenche automaticamente quaisquer lacunas históricas sem sobrescrever dados já existentes.

```
T11.3 [BE] 🟡 (paralelo com T11.1) — Endpoint de trigger manual
```

Adicionar em `api/routes/settings_routes.py`:

```
POST /api/settings/backfill-history
```

Body opcional: `{"overwrite": false}`.
Retorna o dict de resultado do backfill (`backfilled`, `skipped`, contagens).
Útil para popular o banco na primeira execução sem precisar disparar um sync completo.

```
T11.4 [FE] 🟢 (depende de T11.3) — Botão "Recalcular histórico" em Settings
```

Na página `pages/Settings.tsx`, adicionar seção "Dados Históricos" com:

- Botão "Recalcular histórico financeiro" que chama `POST /api/settings/backfill-history`.
- Feedback após execução: "X meses recalculados, Y meses mantidos" (usa o dict de retorno).
- Spinner durante a chamada; desabilitar botão para evitar duplo clique.

---

## Mapa de Dependências (resumo)

```
S0 (todas as migrações) ──────────────────────────────────────────────────────┐
  ├── T0.1 (accounts_snapshot) ──▶ S2.T2.1 (sync snapshot)                   │
  │                              └▶ S2.T2.2 (net worth endpoint)              │
  │                                                                            │
  ├── T0.2 (recurrent_expenses) ─▶ S4.T4.1 (sync recurrency)                 │
  │                              └▶ S4.T4.3 (API CRUD)                        │
  │                                                                            │
  ├── T0.3 (installment cols)   ─▶ S4.T4.2 (popular parcelas no sync)        │
  │                              └▶ S7.T7.1 (sync bills novas colunas)        │
  │                                                                            │
  ├── T0.4 (income_sources)     ─▶ S5.T5.1 (sync income)                     │
  │                              └▶ S5.T5.2 (API income)                      │
  │                                                                            │
  ├── T0.5 (bills cols)         ─▶ S7.T7.1 (sync bills)                      │
  │                                                                            │
  └── T0.6 (automation_rules)   ─▶ S8.T8.2 (motor automações)               │
                                 └▶ S8.T8.3 (API CRUD automações)            │
                                                                              ▼
                              S4 + S5 concluídas ──▶ S9 (projeção)
                              S4 + S7 concluídas ──▶ S3 (próximas despesas)

S10 (metas de consumo) ── independente ──────────────────────────────────────
  ├── T10.1 (API goals) ──▶ T10.2 (hook useGoals)
  │                       └▶ T10.4 (integrar em Settings)
  └── T10.3 (GoalsEditor) ─▶ T10.4
  Alimenta: S1 (linha Meta no gráfico), S2 (barra de meta no resultado parcial)

S11 (backfill de histórico) ── independente ─────────────────────────────────
  ├── T11.1 (backfill service) ──▶ T11.2 (chamar no sync)
  │                              └▶ T11.3 (endpoint manual)
  └── T11.3 ──▶ T11.4 (botão em Settings)
  Alimenta: S1 (monthly_avg), S2 (histórico patrimônio), S6 (fluxo de caixa)
```

---

## Ordem de Entrega Recomendada

| Prioridade | História                        | Justificativa                                                                  |
| ---------- | ------------------------------- | ------------------------------------------------------------------------------ |
| 0          | **S0 — Migrações**              | **Bloqueante global** — deve ser mergeada antes de tudo                        |
| 1          | **S11 — Backfill de Histórico** | Desbloqueia `monthly_avg` em S1 e histórico em S2/S6; independente de S0       |
| 1          | **S10 — Metas de Consumo**      | Desbloqueia linha de meta em S1 e barra de progresso em S2; independente de S0 |
| 2          | **S4 — Recorrências**           | Base para S3, S7 e S9                                                          |
| 3          | **S7 — Faturas**                | Depende de S0 + S4                                                             |
| 3          | **S5 — Receitas**               | Independente, corre em paralelo com S7                                         |
| 4          | **S2 — Patrimônio**             | Requer accounts_snapshot + investments sincronizados                           |
| 4          | **S1 — Ritmo de Gastos**        | Completo apenas com S10 + S11 finalizadas                                      |
| 5          | **S6 — Fluxo de Caixa**         | Requer boa cobertura de `finance_history` (garantida por S11)                  |
| 5          | **S8 — Categorias**             | Independente, corre em paralelo com S6                                         |
| 6          | **S3 — Próximas Despesas**      | Depende de S4 e S7 completos                                                   |
| 7          | **S9 — Projeção**               | Depende de S4 + S5 completos                                                   |

---

_Documento gerado em 2026-03-13._
