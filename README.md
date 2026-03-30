# Personal Finance

Sistema de gestão financeira pessoal integrado com a [Pluggy API](https://pluggy.ai) para importação automática de transações bancárias e de investimentos.

## Funcionalidades

- Dashboard com resumo mensal (receitas, despesas, saldo)
- Importação automática de transações bancárias e de cartão de crédito
- Portfólio de investimentos com histórico
- Categorização e automações de categorização
- Histórico financeiro mensal e projeções
- Ritmo de gastos diário (spending pace)
- Gestão de recorrências e parcelas

## Pré-requisitos

- [Docker](https://www.docker.com/) e Docker Compose
- Conta de desenvolvedor na [Pluggy](https://dashboard.pluggy.ai) (gratuita)
- Conta no [meu.pluggy.ai](https://meu.pluggy.ai) para conectar suas instituições financeiras

## Instalação e uso

### 1. Obter o código

**Opção A — Git:**
```bash
git clone https://github.com/<seu-usuario>/personal-finance.git
cd personal-finance
```

**Opção B — ZIP:**

Clique em **Code → Download ZIP** na página do repositório, extraia o arquivo e abra um terminal na pasta extraída.

### 2. Subir o container

```bash
docker-compose up --build
```

O app ficará disponível em `http://localhost:5000`.

Na primeira vez, a build do frontend React leva alguns minutos.

### 3. Configuração inicial (onboarding)

Ao acessar o app pela primeira vez, o assistente de configuração vai guiar você por três etapas:

**Etapa 1 — Credenciais Pluggy**

1. Acesse [dashboard.pluggy.ai](https://dashboard.pluggy.ai) e crie uma aplicação
2. Em *Customization > Connectors > Personal > Direct Connectors*, habilite o conector **MeuPluggy**
3. Cole o **Client ID** e **Client Secret** no formulário

**Etapa 2 — Conectar contas**

1. Acesse [meu.pluggy.ai](https://meu.pluggy.ai) e crie suas conexões (contas bancárias, corretoras)
2. Clique em "Conectar conta" no app e faça login com sua conta do meu.pluggy.ai
3. Repita para cada instituição que quiser importar

**Etapa 3 — Sincronização inicial**

Clique em "Sincronizar tudo" para importar até 1 ano de histórico. Isso pode levar alguns minutos.

### 4. Sincronizações futuras

Após a configuração inicial, use a página **Sincronizar** para atualizar os dados periodicamente. A sincronização incremental importa apenas os últimos 6 dias.

## Persistência dos dados

O banco de dados SQLite fica salvo em `./data/finance.db` no host. O diretório `data/` é montado como volume no container, então seus dados sobrevivem a reinicializações e rebuilds.

```bash
# Reiniciar sem perder dados
docker-compose down
docker-compose up

# Rebuild da imagem (atualização do código) sem perder dados
docker-compose up --build
```

## Desenvolvimento local

```bash
# Backend (Python 3.11+)
pip install -r requirements.txt
python app.py

# Frontend (Node 18+), em outro terminal
cd frontend
npm install
npm run dev
```

O frontend de desenvolvimento roda em `http://localhost:5173` com proxy para o backend em `http://localhost:5000`.

### Testes

```bash
pytest tests/ --cov=services --cov=repositories --cov=utils --cov-report=term-missing
```

## Estrutura do projeto

```
personal-finance/
├── api/routes/        # Endpoints Flask (blueprints)
├── services/          # Lógica de negócio
├── repositories/      # Acesso ao banco de dados (SQLite)
├── models/            # Entidades de dados
├── frontend/          # React + TypeScript (Vite)
├── tests/             # Testes unitários
├── app.py             # Entry point Flask
├── init_db.py         # Schema do banco de dados
├── pluggy_api.py      # Integração com a Pluggy API
└── docker-compose.yml
```
