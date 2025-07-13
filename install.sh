#!/bin/bash

# execAI Installation Script
# Automated installation script for execAI CLI tool

set -e

echo "🚀 Installing execAI - CLI AI Agent for Natural Language Commands"
echo "================================================================="

# Check Python version
python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.8+ is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install package in development mode
echo "📥 Installing execAI..."
pip install -e .

# Install development dependencies (optional)
read -p "🛠️  Install development dependencies? (y/N): " install_dev
if [[ $install_dev =~ ^[Yy]$ ]]; then
    echo "📥 Installing development dependencies..."
    pip install -e .[dev]
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️  Creating .env configuration file..."
    cp env.example .env
    echo "📝 Please edit .env with your OpenAI API key and configuration"
fi

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "🔑 Next steps:"
echo "1. Edit .env file with your OpenAI API key"
echo "2. Activate the virtual environment: source venv/bin/activate"
echo "3. Test the installation: execai version"
echo ""
echo "📚 Usage examples:"
echo "   execai run \"list all files in current directory\""
echo "   execai run \"show system information\" --force"
echo "   execai schedules"
echo ""
echo "🔒 Security note: Always review commands before execution!"
echo "📖 Read the full documentation in README.md" 