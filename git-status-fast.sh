#!/bin/bash
# Fast git status alternative
# Usage: ./git-status-fast.sh

# Show only tracked file changes (much faster)
echo "=== Tracked Files Changed ==="
git diff --name-status

echo ""
echo "=== Staged Files ==="
git diff --cached --name-status

echo ""
echo "=== Quick Summary ==="
echo "Modified: $(git diff --name-only | wc -l | tr -d ' ') files"
echo "Staged: $(git diff --cached --name-only | wc -l | tr -d ' ') files"

