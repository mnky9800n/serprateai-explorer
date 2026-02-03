#!/bin/bash
# SerpRateAI Explorer - Launch Script

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   SerpRateAI Time Series Explorer      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo

# Dataset repo
DATASETS_DIR="./data"
DATASETS_REPO="https://github.com/SerpRateAI/datasets.git"

# Clone datasets if not present
if [ ! -d "$DATASETS_DIR" ]; then
    echo -e "${YELLOW}Datasets not found. Cloning from GitHub...${NC}"
    git clone "$DATASETS_REPO" "$DATASETS_DIR"
    echo -e "${GREEN}✓ Datasets downloaded${NC}"
    echo
fi

# Check for dataset updates
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
        
        # Show what's new
        echo -e "${BLUE}New commits:${NC}"
        git log --oneline HEAD..origin/main 2>/dev/null || git log --oneline HEAD..origin/master 2>/dev/null || true
        echo
        
        read -p "Would you like to update the datasets? [Y/n] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            echo -e "${GREEN}Updating datasets...${NC}"
            git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || echo "Update failed, continuing with existing data"
            echo -e "${GREEN}✓ Datasets updated${NC}"
        else
            echo "Skipping update, using existing data."
        fi
    else
        echo -e "${GREEN}✓ Datasets are up to date${NC}"
    fi
    
    cd ..
else
    echo -e "${RED}Warning: data/ exists but is not a git repo.${NC}"
    echo -e "${YELLOW}To enable updates, remove data/ and re-run this script.${NC}"
fi

echo

# Run with uv
echo -e "${GREEN}Starting Bokeh server...${NC}"
echo "Open http://localhost:5006/app in your browser"
echo

uv run bokeh serve app.py --show
