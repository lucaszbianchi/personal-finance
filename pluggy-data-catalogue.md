# Catálogo de Dados Pluggy

> **Objetivo**: Mapear todos os dados disponíveis via Pluggy API e Insights API —
> o que já ingerimos, o que ignoramos, o que está disponível mas não usamos —
> para planejar a ingestão nas tabelas e as visualizações futuras.

---

## Índice

1. [Autenticação](#1-autenticação)
2. [Items (Conexões Bancárias)](#2-items-conexões-bancárias)
3. [Accounts (Contas)](#3-accounts-contas)
4. [Transactions (Transações)](#4-transactions-transações)
5. [Bills (Faturas)](#5-bills-faturas)
6. [Investments (Investimentos)](#6-investments-investimentos)
7. [Investment Transactions](#7-investment-transactions)
8. [Loans (Empréstimos / Crédito)](#8-loans-empréstimos--crédito)
9. [Identity (Identidade)](#9-identity-identidade)
10. [Categories (Categorias)](#10-categories-categorias)
11. [Pluggy Insights API](#11-pluggy-insights-api)
12. [Resumo: campos não utilizados com maior potencial](#12-resumo-campos-não-utilizados-com-maior-potencial)
13. [Sugestões de novas tabelas / colunas](#13-sugestões-de-novas-tabelas--colunas)

---

## Legenda de Status

| Ícone | Significado |
|-------|-------------|
| ✅ | Campo já ingerido no banco de dados |
| ⚠️ | Campo ignorado atualmente, mas disponível |
| 🆕 | Endpoint/recurso ainda não consumido |
| 💡 | Sugestão de uso para visualizações |

---

## 1. Autenticação

### `POST /auth` — Exchange de credenciais

```
POST https://api.pluggy.ai/auth
Body: { clientId, clientSecret }
Response: { apiKey }   # válido por 2 horas
```

- ✅ `apiKey` — usado em todos os requests como header `X-API-KEY`

### `POST /connect_token` — Token para o widget frontend

```
POST https://api.pluggy.ai/connect_token
Response: { accessToken, expiresAt }   # válido por 30 minutos
```

- ✅ `accessToken` — enviado ao frontend para o Pluggy Connect Widget

---

## 2. Items (Conexões Bancárias)

### `GET /items/{item_id}`

Retorna o status de uma conexão bancária específica.

| Campo | Tipo | Status | Notas |
|-------|------|--------|-------|
| `id` | string | ✅ | PK na tabela `pluggy_items` |
| `connector.name` | string | ✅ | Salvo como `connector_name` |
| `status` | string | ✅ | `UPDATED`, `UPDATING`, `LOGIN_ERROR`, etc. |
| `error` | object | ⚠️ | Detalhes de erro de conexão |
| `executionStatus` | string | ⚠️ | Status granular da última execução |
| `lastUpdatedAt` | datetime | ⚠️ | Timestamp da última sincronização bem-sucedida |
| `createdAt` | datetime | ⚠️ | Data de criação do item |
| `connector.id` | number | ⚠️ | ID do conector (banco/instituição) |
| `connector.type` | string | ⚠️ | `PERSONAL_BANK`, `BUSINESS_BANK`, etc. |
| `connector.country` | string | ⚠️ | País do conector |
| `connector.primaryColor` | string | ⚠️ | Cor da instituição (útil para UI) |
| `connector.institutionUrl` | string | ⚠️ | URL da instituição |
| `connector.imageUrl` | string | ⚠️ | Logo da instituição |
| `connector.products` | array | ⚠️ | Produtos disponíveis: `TRANSACTIONS`, `INVESTMENTS`, `IDENTITY`, `LOANS`, etc. |

💡 **Visualizações possíveis**: painel "Minhas conexões" com logo, status e última atualização de cada banco.

---

## 3. Accounts (Contas)

### `GET /accounts?itemId=...`

| Campo | Tipo | Status | Notas |
|-------|------|--------|-------|
| `id` | string | ✅ | Usado como `account_id` em transações/faturas |
| `type` | string | ✅ | `BANK` ou `CREDIT` — define rota de processamento |
| `subtype` | string | ⚠️ | `CHECKING_ACCOUNT`, `SAVINGS_ACCOUNT`, `CREDIT_CARD` |
| `name` | string | ⚠️ | Nome da conta (ex: "Conta Corrente Nubank") |
| `number` | string | ⚠️ | Número da conta ou 4 últimos dígitos do cartão |
| `balance` | number | ⚠️ | Saldo disponível / fatura em aberto |
| `currencyCode` | string | ⚠️ | Moeda (quase sempre `BRL`) |
| `owner` | string | ⚠️ | Nome do titular |
| `taxNumber` | string | ⚠️ | CPF/CNPJ do titular |
| `marketingName` | string | ⚠️ | Nome de marketing (ex: "Nubank Ultravioleta") |
| **bankData** | | | |
| `bankData.transferNumber` | string | ⚠️ | Número COMPE/Agência/Conta |
| `bankData.closingBalance` | number | ⚠️ | Saldo fechamento |
| `bankData.automaticallyInvestedBalance` | number | ⚠️ | Saldo investido automaticamente |
| `bankData.overdraftContractedLimit` | number | ⚠️ | Limite cheque especial |
| `bankData.overdraftUsedLimit` | number | ⚠️ | Cheque especial utilizado |
| `bankData.unarrangedOverdraftAmount` | number | ⚠️ | Saldo emergencial |
| **creditData** | | | |
| `creditData.minimumPayment` | number | ⚠️ | Pagamento mínimo |
| `creditData.availableCreditLimit` | number | ⚠️ | Limite disponível |
| `creditData.creditLimit` | number | ⚠️ | Limite total do cartão |
| `creditData.isLimitFlexible` | boolean | ⚠️ | Limite flexível? |
| `creditData.balanceDueDate` | date | ⚠️ | Vencimento da fatura |
| `creditData.balanceCloseDate` | date | ⚠️ | Fechamento da fatura |
| `creditData.level` | string | ⚠️ | Tier do cartão (Platinum, Gold, etc.) |
| `creditData.brand` | string | ⚠️ | Bandeira (Mastercard, Visa, Elo) |
| `creditData.status` | string | ⚠️ | `ACTIVE`, `BLOCKED`, `CANCELLED` |
| `creditData.holderType` | string | ⚠️ | `MAIN` ou `ADDITIONAL` |
| `creditData.balanceForeignCurrency` | number | ⚠️ | Saldo em moeda estrangeira |

💡 **Visualizações possíveis**:
- Painel de contas com saldo atual, limite de crédito, % utilizado
- Alerta de cheque especial utilizado
- Histórico de saldo por conta ao longo do tempo (requer snapshot periódico)

---

## 4. Transactions (Transações)

### `GET /transactions?accountId=...&from=...&to=...&pageSize=500`

#### Campos do objeto Transaction

| Campo | Tipo | Status | Notas |
|-------|------|--------|-------|
| `id` | string | ✅ | PK |
| `date` | datetime | ✅ | Data da transação (UTC ISO8601) |
| `description` | string | ✅ | Descrição normalizada |
| `descriptionRaw` | string | ⚠️ | Descrição bruta do banco |
| `amount` | number | ✅ | Valor da transação |
| `amountInAccountCurrency` | number | ✅ | Usado para crédito (moeda da conta) |
| `balance` | number | ⚠️ | Saldo pós-transação (quando disponível) |
| `currencyCode` | string | ⚠️ | Moeda |
| `category` | string | ⚠️ | Nome da categoria (Pro tier) |
| `categoryId` | string | ✅ | FK para tabela `categories` |
| `type` | string | ✅ | `DEBIT` ou `CREDIT` |
| `status` | string | ✅ | `PENDING` ou `POSTED` |
| `operationType` | string | ✅ | `PIX`, `TED`, `DOC`, `BOLETO`, `RESGATE_APLIC_FINANCEIRA`, etc. |
| `providerCode` | string | ⚠️ | Código do banco para a transação |
| `providerId` | string | ⚠️ | ID Open Finance (quando aplicável) |
| `accountId` | string | ⚠️ | Não salvo — poderia ser útil para rastrear de qual conta veio |

#### paymentData (PIX/TED/DOC)

| Campo | Tipo | Status | Notas |
|-------|------|--------|-------|
| `paymentData` | JSON | ✅ | Salvo como blob JSON inteiro |
| `paymentData.payer.name` | string | ✅ | Extraído para tabela `persons` |
| `paymentData.payer.documentNumber.value` | string | ✅ | CPF do pagador → `persons.id` |
| `paymentData.receiver.name` | string | ✅ | Extraído para tabela `persons` |
| `paymentData.receiver.documentNumber.value` | string | ✅ | CPF do recebedor |
| `paymentData.paymentMethod` | string | ⚠️ | `PIX`, `TED`, `DOC` (dentro do blob) |
| `paymentData.referenceNumber` | string | ⚠️ | ID de rastreio da transação |
| `paymentData.reason` | string | ⚠️ | Motivo informado pelo pagador |
| `paymentData.boletoMetadata` | object | ⚠️ | Dados de boleto: digitableLine, barcode, juros, multa, desconto |

#### creditCardMetadata (somente crédito)

| Campo | Tipo | Status | Notas |
|-------|------|--------|-------|
| `creditCardMetadata.installmentNumber` | number | ⚠️ | Parcela atual |
| `creditCardMetadata.totalInstallments` | number | ⚠️ | Total de parcelas |
| `creditCardMetadata.totalAmount` | number | ⚠️ | Valor total parcelado |
| `creditCardMetadata.payeeMCC` | string | ⚠️ | Merchant Category Code |
| `creditCardMetadata.cardNumber` | string | ⚠️ | Número do cartão associado |
| `creditCardMetadata.billId` | string | ⚠️ | ID da fatura (Open Finance) |

#### merchant (enriquecimento)

| Campo | Tipo | Status | Notas |
|-------|------|--------|-------|
| `merchant.name` | string | ⚠️ | Nome de exibição do estabelecimento |
| `merchant.businessName` | string | ⚠️ | Razão social |
| `merchant.cnpj` | string | ⚠️ | CNPJ do estabelecimento |
| `merchant.cnae` | string | ⚠️ | Código de atividade econômica |
| `merchant.category` | string | ⚠️ | Categoria do estabelecimento |

💡 **Visualizações possíveis**:
- Detalhamento de parcelas por transação
- Mapa de estabelecimentos mais frequentes (por `merchant.name`)
- Análise de pagamentos via boleto (multas, juros)
- Rastreio de transferências por CPF (`paymentData.payer/receiver`)

---

## 5. Bills (Faturas de Cartão)

### `GET /bills?accountId=...`

| Campo | Tipo | Status | Notas |
|-------|------|--------|-------|
| `id` | string | ✅ | PK |
| `dueDate` | date | ✅ | Vencimento |
| `totalAmount` | number | ✅ | Valor total da fatura |
| `totalAmountCurrencyCode` | string | ✅ | Moeda |
| `minimumPaymentAmount` | number | ✅ | Pagamento mínimo |
| `allowsInstallments` | boolean | ✅ | Permite parcelamento? |
| `financeCharges` | JSON | ✅ | Array de encargos (IOF, juros, etc.) salvo como blob |
| `isOpen` | boolean | ⚠️ | Se a fatura está em aberto |
| `paymentDate` | date | ⚠️ | Data de pagamento (quando paga) |
| `totalAmountPaid` | number | ⚠️ | Valor pago |

💡 **Visualizações possíveis**:
- Linha do tempo de faturas pagas vs. abertas
- Evolução do valor da fatura mês a mês
- Alertas de IOF/juros nas faturas

---

## 6. Investments (Investimentos)

### `GET /investments?itemId=...&pageSize=100`

#### Tipos suportados

| Tipo | Descrição |
|------|-----------|
| `FIXED_INCOME` | CDB, LCI, LCA, Tesouro Direto, Debentures |
| `SECURITY` | Previdência Privada (PGBL/VGBL) |
| `MUTUAL_FUND` | Fundos de Investimento |
| `EQUITY` | Ações, FIIs |
| `ETF` | ETFs |
| `COE` | Certificados de Operações Estruturadas |

#### Campos do objeto Investment

| Campo | Tipo | Status | Notas |
|-------|------|--------|-------|
| `id` | string | ✅ | PK |
| `name` | string | ✅ | Nome do ativo |
| `type` | string | ✅ | Tipo (veja tabela acima) |
| `subtype` | string | ✅ | Ex: `CDB`, `LCI`, `PGBL`, `FII` |
| `amount` | number | ✅ | Valor bruto (com impostos) |
| `balance` | number | ✅ | Valor líquido (após taxas/impostos) |
| `date` | date | ✅ | Data de referência |
| `dueDate` | date | ✅ | Vencimento |
| `issuer` | string | ✅ | Emissor do ativo |
| `rateType` | string | ✅ | Indexador: `CDI`, `SELIC`, `IPCA`, `IGPM`, `DOLAR`, etc. |
| `code` | string | ⚠️ | Código do ativo |
| `isin` | string | ⚠️ | Código ISIN internacional |
| `number` | string | ⚠️ | Número da aplicação |
| `owner` | string | ⚠️ | Titular do investimento |
| `currencyCode` | string | ⚠️ | Moeda |
| `value` | number | ⚠️ | Valor da cota/ação |
| `quantity` | number | ⚠️ | Quantidade de cotas/ações |
| `rate` | number | ⚠️ | % do indexador (ex: 110% do CDI) |
| `fixedAnnualRate` | number | ⚠️ | Taxa anual fixa (prefixados) |
| `lastMonthRate` | number | ⚠️ | Rentabilidade do último mês |
| `lastTwelveMonthsRate` | number | ⚠️ | Rentabilidade dos últimos 12 meses |
| `amountProfit` | number | ⚠️ | Lucro/prejuízo acumulado |
| `amountWithdrawal` | number | ⚠️ | Valor disponível para resgate |
| `amountOriginal` | number | ⚠️ | Valor aplicado originalmente |
| `taxes` | number | ⚠️ | IR estimado |
| `taxes2` | number | ⚠️ | IOF estimado |
| `status` | string | ⚠️ | `ACTIVE`, `PENDING`, `TOTAL_WITHDRAWAL` |
| `issueDate` | date | ⚠️ | Data de emissão |
| `metadata.taxRegime` | string | ⚠️ | Regime tributário (previdência) |
| `metadata.fundName` | string | ⚠️ | Nome do fundo subjacente |
| `metadata.insurer` | string | ⚠️ | Seguradora (previdência) |

💡 **Visualizações possíveis**:
- Breakdown do portfólio por tipo/subtipo (pizza/treemap)
- Rentabilidade mensal e anual por ativo
- Concentração por indexador (% em CDI, IPCA, etc.)
- Projeção de vencimentos (timeline de vencimento de renda fixa)
- Ganho realizado vs. IR estimado

---

## 7. Investment Transactions

### `GET /investments/{investment_id}/transactions` 🆕

Endpoint ainda **não consumido** no projeto.

| Campo | Tipo | Notas |
|-------|------|-------|
| `tradeDate` | date | Data de liquidação |
| `date` | date | Data da operação |
| `type` | string | `BUY`, `SELL`, `TAX`, `TRANSFER` |
| `quantity` | number | Quantidade de cotas |
| `value` | number | Valor unitário de aquisição |
| `amount` | number | Valor bruto da operação |
| `netAmount` | number | Valor líquido (com encargos) |
| `description` | string | Descrição |
| `agreedRate` | number | Taxa acordada (Tesouro Direto) |
| `brokerageNumber` | string | Número da nota de corretagem |
| `expenses.serviceTax` | number | ISS |
| `expenses.brokerageFee` | number | Corretagem |
| `expenses.incomeTax` | number | IR |
| `expenses.other` | number | Outros encargos |
| `expenses.stockExchangeFee` | number | Emolumentos B3 |
| `expenses.custodyFee` | number | Taxa de custódia |
| `expenses.settlementFee` | number | Taxa de liquidação |

💡 **Visualizações possíveis**:
- Histórico de aportes e resgates por ativo
- DRE de investimentos (ganhos realizados - IR - corretagem)
- Análise de custos de transação por corretora

---

## 8. Loans (Empréstimos / Crédito) 🆕

### `GET /loans?itemId=...`

Endpoint ainda **não consumido** no projeto.

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | string | PK |
| `type` | string | Tipo de crédito |
| `productName` | string | Nome do produto (ex: "Empréstimo Pessoal") |
| `contractNumber` | string | Número do contrato |
| `contractAmount` | number | Valor original contratado |
| `contractDate` | date | Data de contratação |
| `dueDate` | date | Vencimento final |
| `settlementDate` | date | Data de quitação |
| `CET` | number | Custo Efetivo Total anual (%) |
| `instalmentPeriodicity` | string | Mensal, semanal, etc. |
| `amortizationScheduled` | string | SAC, PRICE, SAM |
| `interestRates[].rate` | number | Taxa de juros |
| `interestRates[].taxType` | string | Tipo de taxa |
| `contractedFees[].name` | string | Nome da tarifa |
| `contractedFees[].amount` | number | Valor da tarifa |
| `installments.total` | number | Total de parcelas |
| `installments.paid` | number | Parcelas pagas |
| `installments.due` | number | Parcelas a vencer |
| `installments.overdue` | number | Parcelas vencidas |
| `payments.outstanding` | number | Saldo devedor atual |
| `warranties[].type` | string | Tipo de garantia |
| `warranties[].amount` | number | Valor da garantia |

💡 **Visualizações possíveis**:
- Painel de dívidas com saldo devedor e progresso de quitação
- Comparativo CET entre contratos
- Alerta de parcelas vencidas

---

## 9. Identity (Identidade) 🆕

### `GET /identity?itemId=...`

Endpoint ainda **não consumido** no projeto. Retorna dados cadastrais do titular da conta.

| Campo | Tipo | Notas |
|-------|------|-------|
| `id` | string | PK |
| `type` | string | `PERSONAL` ou `BUSINESS` |
| `fullName` | string | Nome completo |
| `document` | string | CPF ou CNPJ |
| `documentType` | string | `CPF`, `CNPJ`, `PASSPORT` |
| `birthDate` | date | Data de nascimento |
| `gender` | string | Gênero |
| `maritalStatus` | string | Estado civil |
| `nationality` | string | Nacionalidade |
| `pepPoliticallyExposedPerson` | boolean | Pessoa politicamente exposta |
| `phone` | array | Lista de telefones |
| `email` | array | Lista de e-mails |
| `address` | array | Lista de endereços (logradouro, CEP, cidade, estado) |
| `company.name` | string | Razão social (PJ) |
| `company.tradeName` | string | Nome fantasia |
| `company.cnpj` | string | CNPJ |
| `company.cnae` | string | Atividade econômica |

💡 **Uso potencial**: validação/enriquecimento do perfil do usuário no sistema.

---

## 10. Categories (Categorias)

### `GET /categories`

| Campo | Tipo | Status | Notas |
|-------|------|--------|-------|
| `id` | string | ✅ | PK (8 dígitos, hierárquico) |
| `description` | string | ✅ | Descrição em inglês |
| `descriptionTranslated` | string | ✅ | Descrição em português |
| `parentId` | string | ✅ | FK para categoria pai (null = raiz) |
| `parentDescription` | string | ✅ | Descrição do pai |

> Dados completos já ingeridos. Hierarquia de 2 níveis: categoria → subcategoria.

---

## 11. Pluggy Insights API

### Base URL: `https://insights-api.pluggy.ai`

A API de Insights fornece análises comportamentais e financeiras pré-calculadas.
Atualmente o projeto consome o endpoint `/book` via `https://api.pluggy.ai/insights/book`.

---

### 11.1 Book (Indicadores Financeiros)

### `GET /insights/book?itemId=...` (ou `POST /book?itemIds=...`)

Retorna KPIs agregados por janela temporal (M1 a M12).

#### Estrutura `book.bankAccount` e `book.creditCard`

Ambos contêm dezenas de métricas com padrão de nome:
`{métrica}_{tipo}_{janela}` (ex: `sum_transactions_debit_M1`).

| Família de métricas | Exemplo de campo | Status |
|---|---|---|
| Contagem de transações | `count_transactions_debit_M1..M12` | ✅ Salvo como blob JSON |
| Soma de transações | `sum_transactions_credit_M1..M12` | ✅ Salvo como blob JSON |
| Ratio crédito/débito | `ratio_transactions_creditdebit_M1..M12` | ⚠️ Dentro do blob, não indexado |
| Datas dos débitos | `percentage_transactions_debit_dates_1-5_M1` | ⚠️ Dentro do blob, não indexado |
| Saldo médio | `avg_balance_M1..M12` | ⚠️ Dentro do blob, não indexado |

> **Problema atual**: toda a estrutura `bankAccount`/`creditCard` é salva como JSON blob,
> o que dificulta queries analíticas. Ver sugestão de normalização em §13.

#### Estrutura `book.categories[]`

| Campo | Status | Notas |
|-------|--------|-------|
| `category` | ✅ | Nome da categoria |
| `transactionType` | ✅ | `DEBIT` ou `CREDIT` |
| `accountSubtype` | ✅ | `CHECKING_ACCOUNT` ou `CREDIT_CARD` |
| `M1.avg` / `.total` / `.min` / `.max` | ✅ | Métricas do último mês |
| `M2.*` / `M3.*` / `M6.*` / `M12.*` | ✅ | Idem para 2, 3, 6 e 12 meses |

---

### 11.2 Income Analysis 🆕

### `GET /income?itemId=...`

Análise de fontes de renda recorrente.

| Campo | Notas |
|-------|-------|
| `sources[].description` | Nome da fonte (ex: "Salário Empresa XYZ") |
| `sources[].amount` | Valor médio |
| `sources[].frequency` | `MONTHLY`, `WEEKLY`, etc. |
| `sources[].lastOccurrence` | Data do último recebimento |
| `sources[].confidence` | Score de confiança da detecção |
| `totalIncome.M1` / `M3` / `M6` / `M12` | Renda total por janela |

💡 **Visualizações possíveis**: painel de renda com fontes detectadas automaticamente + histórico.

---

### 11.3 Recurrency (Gastos Recorrentes) 🆕

### `GET /recurrency?itemId=...`

Detecção automática de cobranças recorrentes (assinaturas, serviços).

| Campo | Notas |
|-------|-------|
| `recurrent[].description` | Nome da assinatura/serviço |
| `recurrent[].amount` | Valor típico |
| `recurrent[].frequency` | `MONTHLY`, `ANNUAL`, etc. |
| `recurrent[].nextOccurrence` | Próxima cobrança estimada |
| `recurrent[].category` | Categoria Pluggy |
| `recurrent[].confidence` | Score de confiança |
| `recurrent[].merchant.name` | Estabelecimento (quando disponível) |
| `totalRecurrency.M1` / `M12` | Total de recorrentes por janela |

💡 **Visualizações possíveis**: lista de assinaturas ativas com valor, frequência e próxima cobrança.

---

## 12. Resumo: campos não utilizados com maior potencial

| Campo/Endpoint | Recurso | Potencial analítico |
|---|---|---|
| `creditCardMetadata.installmentNumber/totalInstallments` | Transactions | Rastreio de parcelamentos em aberto |
| `merchant.name / cnpj` | Transactions | Top estabelecimentos, mapa de gastos |
| `balance` (pós-transação) | Transactions | Reconstrução do saldo histórico |
| `paymentData.reason` | Transactions | Motivo do PIX (útil para categorização manual) |
| `account.balance` + snapshot diário | Accounts | Evolução de patrimônio líquido |
| `account.creditData.*` | Accounts | Utilização do limite, vencimento |
| `investment.amountProfit` / `lastTwelveMonthsRate` | Investments | Rentabilidade real por ativo |
| `investment.quantity` / `value` | Investments | Posição em cotas (fundos/ações) |
| `investment.taxes` / `taxes2` | Investments | IR/IOF estimados |
| Investment Transactions | 🆕 Endpoint | Histórico de aportes/resgates |
| Loans | 🆕 Endpoint | Saldo devedor, parcelas, CET |
| Income Analysis | 🆕 Insights | Detecção automática de renda |
| Recurrency | 🆕 Insights | Detecção automática de assinaturas |

---

## 13. Sugestões de novas tabelas / colunas

### 13.1 Expandir `bank_transactions` e `credit_transactions`

```sql
-- bank_transactions
ADD COLUMN account_id TEXT;          -- de qual conta veio
ADD COLUMN balance_after REAL;       -- saldo pós-transação
ADD COLUMN merchant_name TEXT;       -- merchant.name
ADD COLUMN merchant_cnpj TEXT;       -- merchant.cnpj
ADD COLUMN payment_reason TEXT;      -- paymentData.reason

-- credit_transactions
ADD COLUMN installment_number INT;   -- creditCardMetadata.installmentNumber
ADD COLUMN total_installments INT;   -- creditCardMetadata.totalInstallments
ADD COLUMN total_amount REAL;        -- creditCardMetadata.totalAmount
ADD COLUMN merchant_name TEXT;
ADD COLUMN merchant_cnpj TEXT;
```

### 13.2 Nova tabela `accounts_snapshot`

Snapshot diário do saldo das contas para histórico de patrimônio.

```sql
CREATE TABLE accounts_snapshot (
    id          TEXT,               -- account.id
    item_id     TEXT,               -- FK pluggy_items
    name        TEXT,
    type        TEXT,               -- BANK | CREDIT
    subtype     TEXT,               -- CHECKING_ACCOUNT | CREDIT_CARD
    balance     REAL,
    credit_limit REAL,              -- creditData.creditLimit
    available_credit REAL,          -- creditData.availableCreditLimit
    due_date    TEXT,               -- creditData.balanceDueDate
    snapshotted_at TEXT,            -- timestamp do snapshot
    PRIMARY KEY (id, snapshotted_at)
);
```

### 13.3 Expandir `investments`

```sql
ADD COLUMN quantity REAL;
ADD COLUMN value_per_unit REAL;      -- investment.value
ADD COLUMN amount_original REAL;
ADD COLUMN amount_profit REAL;
ADD COLUMN amount_withdrawal REAL;
ADD COLUMN rate REAL;                -- % do indexador
ADD COLUMN fixed_annual_rate REAL;
ADD COLUMN last_month_rate REAL;
ADD COLUMN last_twelve_months_rate REAL;
ADD COLUMN taxes REAL;               -- IR estimado
ADD COLUMN taxes2 REAL;              -- IOF estimado
ADD COLUMN status TEXT;
ADD COLUMN issue_date TEXT;
ADD COLUMN isin TEXT;
```

### 13.4 Nova tabela `investment_transactions`

```sql
CREATE TABLE investment_transactions (
    id               TEXT PRIMARY KEY,
    investment_id    TEXT,           -- FK investments
    date             TEXT,
    trade_date       TEXT,
    type             TEXT,           -- BUY | SELL | TAX | TRANSFER
    quantity         REAL,
    value            REAL,
    amount           REAL,
    net_amount       REAL,
    description      TEXT,
    agreed_rate      REAL,
    brokerage_number TEXT,
    expense_service_tax   REAL,
    expense_brokerage_fee REAL,
    expense_income_tax    REAL,
    expense_other         REAL
);
```

### 13.5 Nova tabela `loans`

```sql
CREATE TABLE loans (
    id                   TEXT PRIMARY KEY,
    item_id              TEXT,
    product_name         TEXT,
    type                 TEXT,
    contract_number      TEXT,
    contract_amount      REAL,
    contract_date        TEXT,
    due_date             TEXT,
    cet                  REAL,          -- Custo Efetivo Total anual %
    outstanding_balance  REAL,
    installments_total   INT,
    installments_paid    INT,
    installments_due     INT,
    installments_overdue INT,
    synced_at            TEXT
);
```

### 13.6 Normalizar `pluggy_book_summary`

Substituir o blob JSON por colunas indexáveis para as métricas mais usadas:

```sql
CREATE TABLE pluggy_book_kpis (
    item_id           TEXT,
    account_type      TEXT,           -- BANK_ACCOUNT | CREDIT_CARD
    window            TEXT,           -- M1 | M3 | M6 | M12
    sum_debit         REAL,
    sum_credit        REAL,
    count_debit       INT,
    count_credit      INT,
    avg_balance       REAL,
    ratio_creditdebit REAL,
    synced_at         TEXT,
    PRIMARY KEY (item_id, account_type, window, synced_at)
);
```

### 13.7 Nova tabela `recurrent_expenses` (Insights Recurrency)

```sql
CREATE TABLE recurrent_expenses (
    id              TEXT PRIMARY KEY,
    item_id         TEXT,
    description     TEXT,
    amount          REAL,
    frequency       TEXT,            -- MONTHLY | ANNUAL | WEEKLY
    next_occurrence TEXT,
    category        TEXT,
    merchant_name   TEXT,
    confidence      REAL,
    synced_at       TEXT
);
```

### 13.8 Nova tabela `income_sources` (Insights Income)

```sql
CREATE TABLE income_sources (
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
    synced_at       TEXT
);
```

---

*Documento gerado em 2026-03-13. Baseado no código do repositório e na documentação oficial da Pluggy.*
