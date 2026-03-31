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

---

## Pré-requisitos

- **Docker Desktop** instalado e rodando (veja o passo a passo abaixo)
- Conta de desenvolvedor na [Pluggy](https://dashboard.pluggy.ai) (gratuita)
- Conta no [meu.pluggy.ai](https://meu.pluggy.ai) para conectar suas instituições financeiras

---

## Instalação passo a passo

### Passo 1 — Instalar o Docker (somente na primeira vez)

O app roda dentro do Docker, que é um programa que empacota tudo que é necessário para rodar o sistema sem precisar instalar Python, Node, etc. manualmente.

#### No Windows

O Docker no Windows exige o **WSL 2** (subsistema Linux embutido no Windows). Siga na ordem:

**1.1 — Ativar o WSL 2**

1. Clique no menu Iniciar, pesquise por **"PowerShell"**, clique com o botão direito e escolha **"Executar como administrador"**
2. Cole o comando abaixo e pressione Enter:
   ```
   wsl --install
   ```
3. Aguarde a instalação terminar e **reinicie o computador** quando solicitado

> Se aparecer a mensagem `WSL 2 já está instalado`, pode pular direto para o passo 1.2.

**1.2 — Instalar o Docker Desktop**

1. Acesse [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) e clique em **"Download for Windows"**
2. Execute o instalador baixado e siga os passos (pode deixar as opções padrão)
3. Ao final, **reinicie o computador** se solicitado
4. Abra o **Docker Desktop** pelo menu Iniciar e aguarde até o ícone da baleia aparecer na barra de tarefas (pode levar 1-2 minutos na primeira vez)

> O Docker precisa estar aberto e rodando sempre que você for usar o app.

#### No macOS

1. Acesse [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) e baixe a versão para Mac (escolha Apple Silicon se seu Mac for M1/M2/M3, ou Intel caso contrário)
2. Arraste o Docker para a pasta Aplicativos e abra-o
3. Aguarde o ícone da baleia aparecer na barra de menu

---

### Passo 2 — Baixar o app

**Opção A — Git (para quem já usa):**

```bash
git clone https://github.com/<seu-usuario>/personal-finance.git
cd personal-finance
```

**Opção B — ZIP (mais simples):**

1. Na página do repositório, clique em **Code → Download ZIP**
2. Extraia o arquivo ZIP em uma pasta de sua preferência (ex: `Documentos/personal-finance`)

---

### Passo 3 — Abrir o terminal na pasta do projeto

#### Windows
- Abra a pasta onde extraiu o projeto pelo Explorador de Arquivos
- Clique na barra de endereços, digite `cmd` e pressione Enter

#### macOS
- Abra a pasta no Finder
- Clique com o botão direito na pasta e escolha **"Novo Terminal na Pasta"** (ou use Spotlight para abrir o Terminal e navegue até a pasta)

---

### Passo 4 — Iniciar o app

Com o terminal aberto na pasta do projeto e o Docker Desktop rodando, execute:

```bash
docker-compose up --build
```

Aguarde — na primeira vez, o processo baixa dependências e compila o frontend React, o que pode levar **3 a 5 minutos**. Quando aparecer a mensagem `Running on http://0.0.0.0:5000`, o app está pronto.

Acesse no navegador: **http://localhost:5000**

> Nas próximas vezes, o comando `docker-compose up` (sem `--build`) sobe o app em segundos.

---

### Passo 5 — Configuração inicial (onboarding)

Ao acessar o app pela primeira vez, o assistente de configuração vai guiar você por três etapas:

**Etapa 1 — Credenciais Pluggy**

1. Acesse [dashboard.pluggy.ai](https://dashboard.pluggy.ai) e crie uma aplicação
2. Em _Customization > Connectors > Personal > Direct Connectors_, habilite o conector **MeuPluggy**
3. Cole o **Client ID** e **Client Secret** no formulário

**Etapa 2 — Conectar contas**

1. Acesse [meu.pluggy.ai](https://meu.pluggy.ai) e crie suas conexões (contas bancárias, corretoras)
2. Clique em "Conectar conta" no app e faça login com sua conta do meu.pluggy.ai
3. Repita para cada instituição que quiser importar

**Etapa 3 — Sincronização inicial**

Clique em "Sincronizar tudo" para importar até 1 ano de histórico. Isso pode levar alguns minutos.

---

### Passo 6 — Sincronizações futuras

Após a configuração inicial, use a página **Sincronizar** para atualizar os dados periodicamente. A sincronização incremental importa apenas os últimos 6 dias.

---

## Uso diário

Para usar o app, basta:

1. Abrir o **Docker Desktop** (se não estiver aberto)
2. Abrir o terminal na pasta do projeto e rodar `docker-compose up`
3. Acessar **http://localhost:5000** no navegador

Para encerrar, pressione `Ctrl+C` no terminal ou rode `docker-compose down`.

---

## Persistência dos dados

O banco de dados SQLite fica salvo em `./data/finance.db` na pasta do projeto (no seu computador, fora do Docker). Seus dados **nao sao perdidos** ao reiniciar ou atualizar o app.

```bash
# Reiniciar sem perder dados
docker-compose down
docker-compose up

# Atualizar o app (rebuild) sem perder dados
docker-compose up --build
```

---

## Problemas comuns

**"docker-compose" nao e reconhecido como comando**
- Verifique se o Docker Desktop esta aberto e rodando (icone da baleia na barra de tarefas/menu)
- Tente fechar e reabrir o terminal apos instalar o Docker

**A pagina nao abre em http://localhost:5000**
- Aguarde mais alguns segundos e recarregue — o app pode ainda estar inicializando
- Verifique se nao ha mensagens de erro no terminal

**Erro relacionado ao WSL no Windows**
- Confirme que o WSL 2 esta instalado: abra o PowerShell como administrador e execute `wsl --status`
- Se necessario, execute `wsl --update` para atualizar

---

## Desenvolvimento local (avancado)

Para rodar sem Docker, diretamente na maquina:

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

---

## Estrutura do projeto

```
personal-finance/
├── api/routes/        # Endpoints Flask (blueprints)
├── services/          # Logica de negocio
├── repositories/      # Acesso ao banco de dados (SQLite)
├── models/            # Entidades de dados
├── frontend/          # React + TypeScript (Vite)
├── tests/             # Testes unitarios
├── app.py             # Entry point Flask
├── init_db.py         # Schema do banco de dados
├── pluggy_api.py      # Integracao com a Pluggy API
└── docker-compose.yml
```
