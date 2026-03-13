#!/bin/bash
# Script to fetch and checkout a PR, then generate diff against base branch
# Usage: ./fetch_pr_diff.sh <pr_number> <base_branch>

set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <pr_number> <base_branch>"
    echo "Example: $0 73 main"
    exit 1
fi

PR_NUMBER=$1
BASE_BRANCH=$2
PR_BRANCH="pr-${PR_NUMBER}"

# Store current branch to return to it later if needed
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Check if PR branch already exists and delete it
if git show-ref --verify --quiet "refs/heads/${PR_BRANCH}"; then
    echo "Branch ${PR_BRANCH} already exists. Switching to ${BASE_BRANCH} and deleting old branch..."
    git checkout "${BASE_BRANCH}" 2>/dev/null || git checkout -b "${BASE_BRANCH}" "origin/${BASE_BRANCH}"
    git branch -D "${PR_BRANCH}"
fi

echo "Fetching PR #${PR_NUMBER}..."
git fetch origin "pull/${PR_NUMBER}/head:${PR_BRANCH}"

echo "Checking out PR branch: ${PR_BRANCH}..."
git checkout "${PR_BRANCH}"

echo ""
echo "==================== PR DIFF ===================="
echo "Comparing ${BASE_BRANCH}..${PR_BRANCH}"
echo "================================================"
echo ""

git diff "${BASE_BRANCH}..${PR_BRANCH}"
