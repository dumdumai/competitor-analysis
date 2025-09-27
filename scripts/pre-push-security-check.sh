#!/bin/bash

# Pre-push security check script
# Run this before pushing to remote repository

set -e

echo "🔒 Running pre-push security checks..."

# Check if gitleaks is installed
if ! command -v gitleaks &> /dev/null; then
    echo "❌ Gitleaks not found. Please install it first:"
    echo "   Run: ./scripts/setup-security.sh"
    exit 1
fi

# Run gitleaks scan
echo "🔍 Scanning for secrets with gitleaks..."
if gitleaks detect --config .gitleaks.toml --source . --verbose; then
    echo "✅ No secrets detected by gitleaks"
else
    echo "❌ Secrets detected! Please review and fix before pushing."
    echo "   Check the output above for details"
    echo "   If these are false positives, update .gitleaks.toml"
    exit 1
fi

# Check for common secret patterns manually
echo "🔍 Checking for common secret patterns..."

# Define patterns to check
declare -a patterns=(
    "sk-[a-zA-Z0-9]{48}"           # OpenAI API keys
    "xoxb-[a-zA-Z0-9-]{72}"        # Slack bot tokens
    "AKIA[0-9A-Z]{16}"             # AWS access keys
    "mongodb(\+srv)?://[^:]+:[^@]+@[^/]+"  # MongoDB connection strings
    "postgres(ql)?://[^:]+:[^@]+@[^/]+"    # PostgreSQL connection strings
    "redis://[^:]*:[^@]+@[^/]+"    # Redis connection strings
)

secret_found=false

for pattern in "${patterns[@]}"; do
    # Only scan files that would be committed (not gitignored)
    if git ls-files | xargs grep -E "$pattern" 2>/dev/null; then
        echo "❌ Found potential secret matching pattern: $pattern"
        secret_found=true
    fi
done

if [ "$secret_found" = true ]; then
    echo "❌ Potential secrets found! Please review and fix before pushing."
    exit 1
fi

# Check environment files are not being committed
echo "🔍 Checking for environment files..."
if git diff --cached --name-only | grep -E "\.(env|tfvars)$|credentials$|config$" 2>/dev/null; then
    echo "❌ Environment files or credentials detected in staging area!"
    echo "   Please unstage these files before committing:"
    git diff --cached --name-only | grep -E "\.(env|tfvars)$|credentials$|config$"
    exit 1
fi

echo "✅ All security checks passed!"
echo "🚀 Safe to push to remote repository"
