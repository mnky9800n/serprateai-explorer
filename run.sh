#!/bin/bash
# SerpRateAI Explorer - Launch Script

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   SerpRateAI Time Series Explorer      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo

# Check for dataset updates
DATASETS_DIR="./data"
DATASETS_REPO="https://github.com/SerpRateAI/datasets.git"

if [ -d "$DATASETS_DIR/.git" ]; then
    echo -e "${YELLOW}Checking for dataset updates...${NC}"
    cd "$DATASETS_DIR"
    
    # Fetch latest without merging
    git fetch origin 2>/dev/null || true
    
    # Check if we're behind
    LOCAL=$(git rev-parse HEAD 2>/dev/null || echo "none")
    REMOTE=$(git rev-parse origin/main 2>/dev/null || git rev-parse origin/master 2>/dev/null || echo "none")
    
    if [ "$LOCAL" != "$REMOTE" ] && [ "$REMOTE" != "none" ]; then
        echo -e "${YELLOW}⚠️  Dataset updates available!${NC}"
        echo
        read -p "Would you like to update the datasets? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${GREEN}Updating datasets...${NC}"
            git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || echo "Update failed, continuing with existing data"
        else
            echo "Skipping update, using existing data."
        fi
    else
        echo -e "${GREEN}✓ Datasets are up to date${NC}"
    fi
    
    cd ..
else
    echo -e "${YELLOW}Note: data/ directory is not a git repo. Cannot check for updates.${NC}"
    echo "To enable updates, clone from: $DATASETS_REPO"
fi

echo

# Run with uv
echo -e "${GREEN}Starting Bokeh server...${NC}"
echo "Open http://localhost:5006/app in your browser"
echo

uv run bokeh serve app.py --show
