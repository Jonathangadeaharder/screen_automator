#!/bin/bash
# Screen Automator Framework - Quick Start Setup Script
# This script sets up the development environment with all framework features

set -e  # Exit on error

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                        ║"
echo "║     Screen Automator Framework - Quick Start Setup                    ║"
echo "║                                                                        ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Step 1: Checking Poetry installation...${NC}"
if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}Poetry not found. Installing Poetry...${NC}"
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
    echo -e "${GREEN}✓ Poetry installed${NC}"
else
    echo -e "${GREEN}✓ Poetry already installed${NC}"
fi

echo ""
echo -e "${BLUE}Step 2: Installing dependencies...${NC}"
poetry install --with dev
echo -e "${GREEN}✓ Dependencies installed${NC}"

echo ""
echo -e "${BLUE}Step 3: Installing pre-commit hooks...${NC}"
poetry run pre-commit install
echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"

echo ""
echo -e "${BLUE}Step 4: Creating example data files...${NC}"
PYTHONPATH=$(pwd) poetry run python examples/framework_demo.py > /dev/null 2>&1
echo -e "${GREEN}✓ Example data files created${NC}"

echo ""
echo -e "${BLUE}Step 5: Running code quality checks...${NC}"
echo "  - Checking code format..."
poetry run black . --check --quiet && echo -e "    ${GREEN}✓ Code is formatted${NC}" || echo -e "    ${YELLOW}⚠ Run 'poetry run black .' to format${NC}"

echo "  - Checking import order..."
poetry run isort . --check-only --quiet && echo -e "    ${GREEN}✓ Imports are sorted${NC}" || echo -e "    ${YELLOW}⚠ Run 'poetry run isort .' to sort${NC}"

echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                        ║"
echo "║     ✓ Setup Complete!                                                 ║"
echo "║                                                                        ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

echo -e "${GREEN}Framework features enabled:${NC}"
echo "  ✓ Auto-waiting and actionability"
echo "  ✓ Expectations API"
echo "  ✓ Page Object Model"
echo "  ✓ Data-driven testing"
echo "  ✓ Code quality tools"
echo "  ✓ Pre-commit hooks"
echo ""

echo -e "${BLUE}Next steps:${NC}"
echo ""
echo "  1. Read the Framework Guide:"
echo "     ${YELLOW}cat FRAMEWORK_GUIDE.md${NC}"
echo ""
echo "  2. Review the examples:"
echo "     ${YELLOW}cat examples/framework_demo.py${NC}"
echo "     ${YELLOW}cat examples/integration_example.py${NC}"
echo ""
echo "  3. Try the basic example:"
echo "     ${YELLOW}PYTHONPATH=. poetry run python -c \"
from src.actionability import AutoWaiter
print('✓ Auto-waiting module loaded')
from src.expectations import expect
print('✓ Expectations module loaded')
from src.page_objects import BasePage
print('✓ Page objects module loaded')
from src.data_driven import DataProvider
print('✓ Data-driven module loaded')
print('')
print('All framework modules working!')
\"${NC}"
echo ""
echo "  4. Start using framework features:"
echo "     ${YELLOW}# In your code:
from src.actionability import SmartAutomator
from src.expectations import expect
${NC}"
echo ""
echo "  5. Run tests:"
echo "     ${YELLOW}poetry run pytest${NC}"
echo ""
echo "  6. Format and check code:"
echo "     ${YELLOW}poetry run black .${NC}"
echo "     ${YELLOW}poetry run isort .${NC}"
echo "     ${YELLOW}poetry run flake8 .${NC}"
echo ""

echo -e "${GREEN}Happy automating! 🚀${NC}"
echo ""
