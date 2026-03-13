#!/usr/bin/env bash
# run_checks.sh — Espelha os steps do .github/workflows/run-tests.yml localmente
# Uso: bash scripts/run_checks.sh [--skip-frontend] [--skip-tests] [--skip-coverage]
# Saída: exit 0 se tudo passou, exit 1 se algum step falhou

set -euo pipefail

# Ativa venv do projeto se existir
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
fi

SKIP_FRONTEND=false
SKIP_TESTS=false
SKIP_COVERAGE=false
COMPARE_BRANCH=""

for arg in "$@"; do
  case $arg in
    --skip-frontend)  SKIP_FRONTEND=true ;;
    --skip-tests)     SKIP_TESTS=true ;;
    --skip-coverage)  SKIP_COVERAGE=true ;;
    --compare-branch=*) COMPARE_BRANCH="${arg#*=}" ;;
  esac
done

PASS=0
FAIL=0
RESULTS=()

run_step() {
  local name="$1"
  shift
  echo ""
  echo "▶ $name"
  if "$@" 2>&1; then
    echo "✅ $name"
    RESULTS+=("PASS|$name")
    ((PASS++)) || true
  else
    echo "❌ $name"
    RESULTS+=("FAIL|$name")
    ((FAIL++)) || true
  fi
}

# ── Step 1: Python tests + coverage ──────────────────────────────────────────
if [ "$SKIP_TESTS" = false ]; then
  run_step "pytest (tests/ com cobertura)" \
    pytest tests/ \
      --cov=services --cov=repositories --cov=utils \
      --cov-report=xml --cov-report=term-missing \
      -q
fi

# ── Step 2: Cobertura geral ≥ 80% ────────────────────────────────────────────
if [ "$SKIP_COVERAGE" = false ] && [ "$SKIP_TESTS" = false ]; then
  run_step "Cobertura geral ≥ 80%" \
    coverage report --fail-under=80 --include="services/*,repositories/*,utils/*"
fi

# ── Step 3: Cobertura de código novo ≥ 90% (apenas se branch informada) ──────
if [ -n "$COMPARE_BRANCH" ] && [ "$SKIP_COVERAGE" = false ] && [ "$SKIP_TESTS" = false ]; then
  run_step "Cobertura de código novo ≥ 90% (vs $COMPARE_BRANCH)" \
    diff-cover coverage.xml \
      --compare-branch="$COMPARE_BRANCH" \
      --fail-under=90
fi

# ── Step 4: Frontend build ───────────────────────────────────────────────────
if [ "$SKIP_FRONTEND" = false ] && [ -d "frontend" ]; then
  if [ ! -d "frontend/node_modules" ]; then
    echo "⚠  node_modules ausente — rodando npm install..."
    (cd frontend && npm install --silent)
  fi
  run_step "Frontend build (npm run build)" \
    bash -c "cd frontend && npm run build"
fi

# ── Resumo ───────────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════"
echo "  RESULTADO: $PASS passou(aram), $FAIL falhou(aram)"
echo "════════════════════════════════════════"
for r in "${RESULTS[@]}"; do
  status="${r%%|*}"
  label="${r##*|}"
  if [ "$status" = "PASS" ]; then
    echo "  ✅  $label"
  else
    echo "  ❌  $label"
  fi
done
echo ""

[ "$FAIL" -eq 0 ]
