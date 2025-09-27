#!/bin/bash

# Security Setup Script for Competitor Analysis System
# This script installs and configures security tools for secret detection

set -e

echo "🔒 Setting up security tools for the project..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ] && [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Install gitleaks
echo "📦 Installing gitleaks..."

# Detect OS and install gitleaks accordingly
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command -v brew &> /dev/null; then
        brew install gitleaks
    else
        echo "⚠️  Homebrew not found. Please install gitleaks manually:"
        echo "   Download from: https://github.com/gitleaks/gitleaks/releases"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v apt-get &> /dev/null; then
        # Ubuntu/Debian
        echo "Installing gitleaks for Ubuntu/Debian..."
        wget -O gitleaks.tar.gz https://github.com/gitleaks/gitleaks/releases/latest/download/gitleaks_8.18.4_linux_x64.tar.gz
        tar -xzf gitleaks.tar.gz
        sudo mv gitleaks /usr/local/bin/
        rm gitleaks.tar.gz
    elif command -v yum &> /dev/null; then
        # RHEL/CentOS
        echo "Installing gitleaks for RHEL/CentOS..."
        wget -O gitleaks.tar.gz https://github.com/gitleaks/gitleaks/releases/latest/download/gitleaks_8.18.4_linux_x64.tar.gz
        tar -xzf gitleaks.tar.gz
        sudo mv gitleaks /usr/local/bin/
        rm gitleaks.tar.gz
    fi
else
    echo "⚠️  Unsupported OS. Please install gitleaks manually:"
    echo "   Download from: https://github.com/gitleaks/gitleaks/releases"
fi

# Install pre-commit if Python is available
if command -v python3 &> /dev/null; then
    echo "📦 Installing pre-commit..."
    if [ -f "venv/bin/activate" ]; then
        # Use existing virtual environment
        source venv/bin/activate
        pip install pre-commit detect-secrets
    else
        # Install globally or create venv
        pip3 install --user pre-commit detect-secrets
    fi

    # Install pre-commit hooks
    echo "🔧 Installing pre-commit hooks..."
    pre-commit install

    # Create initial secrets baseline
    echo "📝 Creating secrets baseline..."
    detect-secrets scan --baseline .secrets.baseline

else
    echo "⚠️  Python3 not found. Pre-commit hooks not installed."
    echo "   Please install Python3 and run: pip install pre-commit detect-secrets"
fi

# Run initial security scan
echo "🔍 Running initial security scan..."

if command -v gitleaks &> /dev/null; then
    echo "Running gitleaks scan..."
    gitleaks detect --config .gitleaks.toml --source . --report-format json --report-path gitleaks-report.json --verbose || {
        echo "⚠️  Gitleaks found potential secrets. Check gitleaks-report.json"
        echo "   Review and update .gitleaks.toml if these are false positives"
    }
else
    echo "⚠️  Gitleaks not available. Please install manually."
fi

# Create git hooks directory if it doesn't exist
mkdir -p .git/hooks

# Create a commit-msg hook for additional checking
cat > .git/hooks/commit-msg << 'EOF'
#!/bin/bash
# Additional commit message security check

# Check if commit message contains potential secrets
if grep -qiE "(password|secret|key|token|api_key)" "$1"; then
    echo "⚠️  WARNING: Commit message may contain sensitive information"
    echo "Please review your commit message and ensure no secrets are included"
    exit 1
fi

# Check for common secret patterns in commit message
if grep -qE "(sk-[a-zA-Z0-9]{48}|xoxb-[a-zA-Z0-9-]{72})" "$1"; then
    echo "❌ ERROR: Commit message contains what appears to be a secret"
    echo "Please remove sensitive information from your commit message"
    exit 1
fi
EOF

chmod +x .git/hooks/commit-msg

echo "✅ Security setup complete!"
echo ""
echo "🔒 Security measures installed:"
echo "   • Gitleaks - Secret detection in code"
echo "   • Pre-commit hooks - Automatic scanning before commits"
echo "   • Secrets baseline - Whitelist for known false positives"
echo "   • Enhanced .gitignore - Prevents accidental secret commits"
echo "   • GitHub Actions - Continuous security scanning"
echo "   • Commit message validation - Additional protection"
echo ""
echo "💡 Next steps:"
echo "   1. Review .gitleaks.toml configuration"
echo "   2. Check gitleaks-report.json for any findings"
echo "   3. Add your API keys to backend/.env (already gitignored)"
echo "   4. Run 'gitleaks detect' before pushing to remote"
echo ""
echo "🚀 Ready to commit securely!"
