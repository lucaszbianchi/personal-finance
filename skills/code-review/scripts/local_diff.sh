#!/bin/bash
# Script to generate diff from local branch against base branch
# Usage: ./local_diff.sh <base_branch>

set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <base_branch>"
    echo "Example: $0 main"
    exit 1
fi

BASE_BRANCH=$1

# Get current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository"
    exit 1
fi

# Check if base branch exists
if ! git rev-parse --verify "${BASE_BRANCH}" > /dev/null 2>&1; then
    echo "Error: Base branch '${BASE_BRANCH}' does not exist"
    echo "Available branches:"
    git branch -a
    exit 1
fi

echo "Current branch: ${CURRENT_BRANCH}"
echo "Base branch: ${BASE_BRANCH}"
echo ""
echo "==================== LOCAL DIFF ===================="
echo "Comparing ${BASE_BRANCH}..${CURRENT_BRANCH} (including uncommitted changes)"
echo "===================================================="
echo ""

# Generate diff including uncommitted changes
# This compares the base branch with the current working tree
git diff "${BASE_BRANCH}..."
