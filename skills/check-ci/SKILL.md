---
name: check-ci
description: "Verifica localmente se o pipeline de CI/CD (GitHub Actions) vai passar antes de fazer push ou criar PR. Use quando o usuário perguntar 'as actions vão passar?', 'vai passar no CI?', 'verifica o CI', 'checa as actions', 'roda os testes como no CI', ou variações similares. Executa os mesmos steps do workflow: pytest com cobertura, threshold 80% geral, threshold 90% para código novo (se branch de comparação disponível), e build do frontend."
---

# Check CI

Verifica localmente se o pipeline de CI/CD vai passar, espelhando os steps do `.github/workflows/run-tests.yml`.

## Workflow

### 1. Identificar contexto

Antes de rodar qualquer coisa, colete as informações necessárias:

```bash
git branch --show-current
git status --short
```

- Se houver mudanças não commitadas, avise o usuário que elas **serão incluídas** na checagem de cobertura.
- Anote o branch atual para usar como base no diff-cover (cobertura de código novo).

### 2. Verificar dependências

Confirme que as ferramentas necessárias estão instaladas:

```bash
which pytest coverage diff-cover 2>&1 || echo "MISSING"
```

Se alguma ferramenta estiver faltando, informe o usuário antes de prosseguir.

### 3. Executar os checks

Execute o script bundled a partir do **diretório raiz do projeto**:

```bash
bash /home/lbianchi/.claude/skills/check-ci/scripts/run_checks.sh
```

#### Flags disponíveis

| Flag | Descrição |
|------|-----------|
| `--skip-frontend` | Pula o build do frontend (útil quando só mudanças Python) |
| `--skip-tests` | Pula o pytest (útil para checar só o frontend) |
| `--skip-coverage` | Pula as checagens de threshold de cobertura |
| `--compare-branch=BRANCH` | Habilita diff-cover para checar cobertura de código novo (ex: `--compare-branch=origin/main`) |

**Exemplo com diff-cover:**
```bash
bash /home/lbianchi/.claude/skills/check-ci/scripts/run_checks.sh --compare-branch=origin/main
```

**Exemplo pulando frontend:**
```bash
bash /home/lbianchi/.claude/skills/check-ci/scripts/run_checks.sh --skip-frontend
```

### 4. Interpretar o resultado

Após a execução, analise a saída e apresente um relatório claro:

#### Se tudo passou (exit 0):
```
## ✅ CI vai passar

Todos os X checks passaram:
- ✅ pytest (N testes, sem falhas)
- ✅ Cobertura geral: XX% (mínimo: 80%)
- ✅ Frontend build
```

#### Se algo falhou (exit 1):
```
## ❌ CI vai falhar

X de Y checks falharam:

### ❌ [Nome do check que falhou]
[Trecho relevante da saída de erro]

**Como corrigir:**
[Sugestão específica baseada no erro]
```

### 5. Sugestões de correção

Se algum check falhar, ofereça ajuda imediata baseada no tipo de falha:

#### Falha de cobertura
- Mostre quais arquivos/linhas estão descobertas (`--cov-report=term-missing` já inclui isso)
- Pergunte se o usuário quer que você escreva os testes faltantes

#### Falha de pytest
- Mostre o traceback do teste que falhou
- Ofereça investigar e corrigir o problema

#### Falha de build frontend
- Mostre o erro de compilação TypeScript ou ESLint
- Ofereça corrigir os erros de tipo/lint

## Thresholds do projeto

| Check | Threshold | Quando |
|-------|-----------|--------|
| Cobertura geral | ≥ 80% | Sempre (push e PR) |
| Cobertura de código novo | ≥ 90% | Apenas em PRs (`diff-cover`) |
| Frontend build | Sem erros | Sempre |
| TypeScript | Zero erros | Sempre |

Esses valores espelham `.github/workflows/run-tests.yml` e `CLAUDE.md`.

## Comportamento esperado

- **Nunca** modifique arquivos de código para fazer os checks passarem sem consultar o usuário
- Se a cobertura estiver abaixo do threshold, **pergunte** se deve escrever os testes
- Se um teste estiver falhando por um bug real, **informe** antes de propor correção
- Sempre mostre o **número de testes** e a **porcentagem de cobertura** no relatório final

## Fluxo de decisão

```
/check-ci invocado
  ├─> Coleta branch atual + status git
  ├─> Verifica dependências (pytest, coverage, diff-cover)
  ├─> Pergunta: checar diff-cover vs branch? (se não informado)
  ├─> Roda run_checks.sh com flags adequadas
  └─> Apresenta relatório
        ├─> Tudo passou → "CI vai passar ✅"
        └─> Algo falhou → diagnóstico + oferta de ajuda
```
