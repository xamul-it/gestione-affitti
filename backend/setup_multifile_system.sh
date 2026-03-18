#!/bin/bash
# Setup script for Multi-File Document Management System
# This script installs dependencies and runs migrations for the new system

set -e  # Exit on error

echo "================================================"
echo "Multi-File Document System - Setup"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running from backend directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: Must run from backend/ directory${NC}"
    exit 1
fi

# Step 1: Check Python version
echo -e "${YELLOW}[1/6] Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "Python version: $PYTHON_VERSION"

# Step 2: Install system dependencies (for pdf2image)
echo -e "${YELLOW}[2/6] Checking system dependencies...${NC}"
if command -v apt-get &> /dev/null; then
    # Debian/Ubuntu
    echo "Detected Debian/Ubuntu system"
    if ! command -v pdftoppm &> /dev/null; then
        echo "Installing poppler-utils for PDF processing..."
        sudo apt-get update
        sudo apt-get install -y poppler-utils
    else
        echo "✓ poppler-utils already installed"
    fi
elif command -v brew &> /dev/null; then
    # macOS
    echo "Detected macOS system"
    if ! command -v pdftoppm &> /dev/null; then
        echo "Installing poppler for PDF processing..."
        brew install poppler
    else
        echo "✓ poppler already installed"
    fi
else
    echo -e "${YELLOW}Warning: Could not detect package manager. Please install poppler manually:${NC}"
    echo "  - Debian/Ubuntu: sudo apt-get install poppler-utils"
    echo "  - macOS: brew install poppler"
    echo "  - Other: See https://poppler.freedesktop.org/"
fi

# Step 3: Install Python dependencies
echo -e "${YELLOW}[3/6] Installing Python dependencies...${NC}"
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

pip install -q --upgrade pip
echo "Installing Pillow (image processing)..."
pip install -q Pillow==10.1.0
echo "Installing pdf2image (PDF conversion)..."
pip install -q pdf2image==1.16.3
echo "Installing python-Levenshtein (similarity matching)..."
pip install -q python-Levenshtein==0.25.0

# Verify installations
echo ""
echo "Verifying installations:"
python3 -c "import PIL; print('✓ Pillow installed:', PIL.__version__)" || echo -e "${RED}✗ Pillow installation failed${NC}"
python3 -c "import pdf2image; print('✓ pdf2image installed')" || echo -e "${RED}✗ pdf2image installation failed${NC}"
python3 -c "import Levenshtein; print('✓ python-Levenshtein installed')" || echo -e "${RED}✗ python-Levenshtein installation failed${NC}"

# Step 4: Run database migrations
echo ""
echo -e "${YELLOW}[4/6] Running database migrations...${NC}"
echo "This will update both public and tenant schemas"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found. Please create it first.${NC}"
    exit 1
fi

# Run public schema migrations (core)
echo "Running migrations for public schema..."
alembic upgrade head

# Run tenant schema migrations (anagrafica_italiana module)
echo "Running migrations for all tenant schemas..."
alembic -x schema=all upgrade head

echo -e "${GREEN}✓ Database migrations completed${NC}"

# Step 5: Verify tables created
echo ""
echo -e "${YELLOW}[5/6] Verifying database schema...${NC}"

# Get database URL from .env
DB_URL=$(grep DATABASE_URL .env | cut -d'=' -f2-)

if [ -n "$DB_URL" ]; then
    # Extract database name (simplified)
    DB_NAME=$(echo $DB_URL | sed 's/.*\/\([^?]*\).*/\1/')

    echo "Checking for anag_documenti_files table..."
    psql "$DB_URL" -c "\dt tenant_*.anag_documenti_files" 2>/dev/null && \
        echo -e "${GREEN}✓ DocumentoFile table exists${NC}" || \
        echo -e "${YELLOW}⚠ Could not verify table (check manually)${NC}"

    echo "Checking for parsing_multi_file_config column..."
    psql "$DB_URL" -c "\d public.anag_tipi_documento" 2>/dev/null | grep parsing_multi_file_config && \
        echo -e "${GREEN}✓ parsing_multi_file_config column exists${NC}" || \
        echo -e "${YELLOW}⚠ Could not verify column (check manually)${NC}"
else
    echo -e "${YELLOW}⚠ Could not extract database URL from .env${NC}"
fi

# Step 6: Create storage directories
echo ""
echo -e "${YELLOW}[6/6] Creating storage directories...${NC}"

# Get tenant schemas from database or use defaults
TENANT_SCHEMAS=${TENANT_SCHEMAS:-"tenant_test"}

for tenant in $TENANT_SCHEMAS; do
    echo "Creating directories for $tenant..."
    mkdir -p "storage/$tenant/documents"
    mkdir -p "storage/$tenant/temp_uploads"
    chmod 755 "storage/$tenant"
    chmod 755 "storage/$tenant/documents"
    chmod 755 "storage/$tenant/temp_uploads"
    echo -e "${GREEN}✓ Created storage/$tenant${NC}"
done

# Summary
echo ""
echo "================================================"
echo -e "${GREEN}Setup completed successfully!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Restart your FastAPI backend:"
echo "     python app/main.py"
echo ""
echo "  2. Test the new endpoints:"
echo "     POST /api/v1/anagrafica/documenti/upload-multi"
echo "     POST /api/v1/anagrafica/soggetti/find-similar"
echo "     GET  /api/v1/anagrafica/documenti/{id}/view"
echo ""
echo "  3. Check documentation:"
echo "     docs/implementation/MULTI_FILE_DOCUMENT_SYSTEM_COMPLETE.md"
echo ""
echo "================================================"
