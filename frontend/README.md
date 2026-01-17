# Personal Finance Frontend

Frontend React + TypeScript para o sistema de gestão financeira pessoal.

## Tecnologias

- **React 18** - Framework principal
- **TypeScript** - Tipagem estática
- **Vite** - Build tool e dev server
- **React Router** - Roteamento
- **TanStack Query** - Gerenciamento de estado server
- **Tailwind CSS** - Framework de estilos
- **Lucide React** - Biblioteca de ícones
- **Axios** - Cliente HTTP

## Estrutura do Projeto

```
src/
├── components/          # Componentes reutilizáveis
│   └── Layout/         # Componentes de layout
├── hooks/              # Custom hooks
├── pages/              # Páginas da aplicação
├── services/           # Serviços de API
├── types/              # Tipos TypeScript
├── utils/              # Funções utilitárias
└── main.tsx            # Ponto de entrada
```

## Scripts Disponíveis

```bash
# Desenvolvimento
npm run dev

# Build para produção
npm run build

# Preview da build
npm run preview

# Linting
npm run lint

# Type checking
npm run type-check
```

## Configuração de Desenvolvimento

1. Instalar dependências:
```bash
npm install
```

2. Iniciar o servidor de desenvolvimento:
```bash
npm run dev
```

3. O frontend estará disponível em `http://localhost:3000`

## Proxy de API

O Vite está configurado para fazer proxy das requisições `/api` para `http://localhost:5000`, onde roda o backend Flask.

## Funcionalidades Implementadas

- [x] Dashboard com métricas financeiras
- [x] Listagem de transações com filtros
- [x] Gerenciamento de categorias
- [x] Resumo financeiro com breakdown
- [x] Layout responsivo
- [x] Integração com API backend
- [ ] Formulários para CRUD
- [ ] Gráficos interativos
- [ ] Módulo de investimentos
- [ ] Configurações de usuário

## Padrões de Código

- Componentes funcionais com hooks
- TypeScript strict mode habilitado
- ESLint para linting
- Prettier para formatação
- Convenção de nomenclatura em camelCase
- Props interfaces tipadas
- Custom hooks para lógica reutilizável

## Performance

- Lazy loading de componentes
- React Query para cache de dados
- Otimização de re-renders
- Code splitting por rotas
- Tailwind CSS purge para CSS otimizado