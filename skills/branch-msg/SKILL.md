---
name: branch-msg
description: "Gera branch name e commit message com base nas mudanças locais em relação à main remota. Use quando o usuário pedir 'gera branch name', 'cria commit message', 'sugere nome de branch', 'gera branch e commit', ou variações similares."
---

# Branch & Commit Message Generator

Analisa o `git diff` em relação à `origin/main` e propõe um nome de branch e uma commit message adequados.

## Workflow

### 1. Coletar o diff

Execute os dois comandos em paralelo:

```bash
git diff origin/main --stat
git diff origin/main
```

Se o diff for vazio, informe o usuário que não há mudanças em relação a `origin/main` e encerre.

### 2. Analisar as mudanças

Leia o diff e identifique:

- **Tipo de mudança**: nova feature, bug fix, refactor, chore, test, docs, perf
- **Escopo**: qual módulo, domínio ou camada foi alterado (ex: `transactions`, `auth`, `frontend`)
- **Descrição curta**: o que foi feito em uma linha
- **Detalhes relevantes**: o que foi removido, adicionado ou alterado de forma mais específica

### 3. Gerar branch name

Siga o padrão `<type>/<short-slug>`:

- Tipo igual ao prefixo do Conventional Commits: `feat`, `fix`, `refactor`, `chore`, `test`, `docs`, `perf`
- Slug em kebab-case, máximo ~40 caracteres, sem artigos desnecessários
- Exemplos: `feat/bulk-category-update`, `fix/transaction-date-parsing`, `refactor/repository-upsert`

### 4. Gerar commit message

Siga o formato **Conventional Commits**:

```
<type>(<scope>): <short description>

<body explicando o que mudou e por quê, em inglês, máximo 3-4 linhas>
```

Regras:
- Primeira linha: máximo 72 caracteres
- Corpo: opcional, use quando houver contexto importante (o que foi removido, motivação da mudança)
- Idioma: inglês
- Tom: imperativo ("add", "remove", "replace", "expose")

### 5. Apresentar o resultado

Exiba em blocos de código para fácil cópia:

```
**Branch name:**
feat/exemplo-slug

**Commit message:**
feat(scope): short description

Body explaining what changed and why.
```

Não ofereça variações a menos que o usuário peça. Uma sugestão direta é suficiente.

## Comportamento esperado

- Analise o diff inteiro antes de concluir — não baseie a sugestão só no `--stat`
- Se o diff misturar múltiplos tipos (ex: feat + refactor), escolha o tipo dominante
- Se houver apenas mudanças de formatação/estilo, use `style` ou `chore`
- Nunca execute `git checkout`, `git commit` ou qualquer comando destrutivo
- Se o usuário pedir para aplicar (criar a branch ou commitar), confirme antes de agir
