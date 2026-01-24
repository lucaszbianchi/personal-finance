# Personal Finance Management System

Sistema completo de gestão financeira pessoal com backend em Python/Flask e frontend em React/TypeScript.

## Estrutura do Projeto

```
personal-finance/
├── frontend/               # Frontend React + TypeScript
├── api/                   # Rotas da API Flask
├── models/                # Modelos de dados
├── repositories/          # Camada de acesso aos dados
├── services/             # Lógica de negócio
├── static/               # Frontend atual (HTML/JS)
├── tests/                # Testes unitários
├── app.py                # Aplicação Flask principal
├── pluggy_api.py         # Sincronização de dados
└── finance.db            # Banco SQLite
```

## Tecnologias

### Backend
- **Python 3.8+** - Linguagem principal
- **Flask** - Framework web
- **SQLite** - Banco de dados
- **Pluggy API** - Integração bancária
- **Splitwise** - Gestão de gastos compartilhados

### Frontend Novo (React)
- **React 18** - Framework frontend
- **TypeScript** - Tipagem estática
- **Vite** - Build tool
- **Tailwind CSS** - Framework de estilos
- **TanStack Query** - Gerenciamento de estado

### Frontend Atual (Mantido)
- **HTML/CSS/JavaScript** - Interface atual
- **Bootstrap** - Framework CSS
- **Chart.js** - Gráficos

## Configuração de Desenvolvimento

### 1. Configurar Backend

1. Instalar dependências Python:
```bash
pip install -r requirements.txt
```

2. Configurar variáveis de ambiente:
```bash
cp .env.example .env
# Editar .env com suas credenciais da Pluggy
```

3. Iniciar o backend:
```bash
python app.py
```

### 2. Configurar Frontend React

1. Instalar dependências do Node.js:
```bash
npm run setup
```

2. Iniciar o frontend:
```bash
npm run frontend:dev
```

### 3. Desenvolvimento Simultâneo

Para rodar backend e frontend simultaneamente:
```bash
npm run dev
```

## Scripts Disponíveis

### Gerais
- `npm run dev` - Roda backend e frontend simultaneamente
- `npm run setup` - Instala dependências do frontend

### Backend
- `npm run backend:dev` - Inicia servidor Flask
- `npm run backend:sync` - Sincroniza dados da Pluggy

### Frontend React
- `npm run frontend:dev` - Servidor de desenvolvimento
- `npm run frontend:build` - Build para produção
- `npm run frontend:preview` - Preview da build

## API Endpoints

### Transações
- `GET /api/transactions` - Listar transações
- `POST /api/transactions` - Criar transação
- `PUT /api/transactions/{id}` - Atualizar transação
- `DELETE /api/transactions/{id}` - Deletar transação

### Categorias
- `GET /api/categories` - Listar categorias
- `POST /api/categories` - Criar categoria

### Resumo Financeiro
- `GET /api/summary/finance` - Resumo financeiro
- `GET /api/dashboard` - Dados do dashboard

### Importação
- `POST /api/import/sync` - Sincronizar dados bancários

## Funcionalidades

### ✅ Implementado
- Dashboard com métricas financeiras
- Gestão de transações bancárias e cartão
- Sistema de categorização
- Integração com Splitwise
- Resumos e relatórios financeiros
- Interface web responsiva

### 🚧 Em Desenvolvimento (React)
- Interface React moderna
- Gráficos interativos
- Filtros avançados
- Formulários otimizados
- Performance melhorada

### 📋 Roadmap
- Módulo de investimentos completo
- Projeções financeiras
- Relatórios em PDF
- Aplicativo mobile
- Dashboard executivo

## Arquitetura

O sistema segue uma arquitetura em camadas:

1. **Camada de Apresentação**: Frontend React/HTML
2. **Camada de API**: Flask com blueprints
3. **Camada de Serviço**: Lógica de negócio
4. **Camada de Repositório**: Acesso aos dados
5. **Camada de Dados**: SQLite com thread safety

### Padrões Utilizados
- Repository Pattern para acesso aos dados
- Service Layer para lógica de negócio
- Dependency Injection nos serviços
- Upsert inteligente para sincronização

## Dados e Integrações

### Pluggy API
- Sincronização automática de dados bancários
- Suporte a múltiplas instituições
- Histórico de até 1 ano

### Splitwise
- Importação de gastos compartilhados
- Matching automático com transações
- Controle de liquidação

## Testing

```bash
# Executar todos os testes
python -m unittest discover tests

# Testes específicos
python -m unittest tests.repositories
python -m unittest tests.services
```

## Deployment

### Desenvolvimento
O sistema roda localmente com Flask dev server e Vite dev server.

### Produção (Planejado)
- Docker containerization
- PostgreSQL/MySQL
- Nginx reverse proxy
- CI/CD pipeline

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Licença

Este projeto é de uso pessoal e educacional.