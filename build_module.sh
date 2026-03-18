#!/usr/bin/env bash
# build_module.sh - Builds an installable ZIP for one or more modules
#
# Usage (from repo root):
#   ./build_module.sh anagrafica_italiana
#   ./build_module.sh immobili
#   ./build_module.sh affitti_lungo
#   ./build_module.sh all           # builds all modules
#
# Output: dist/<module_name>_v<version>.zip

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_MODULES="$SCRIPT_DIR/backend/modules"
FRONTEND_MODULES="$SCRIPT_DIR/frontend/src/modules"
DIST_DIR="$SCRIPT_DIR/dist"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

mkdir -p "$DIST_DIR"

build_module() {
    local MODULE_NAME="$1"
    local BACKEND_SRC="$BACKEND_MODULES/$MODULE_NAME"
    local FRONTEND_SRC="$FRONTEND_MODULES/$MODULE_NAME"

    if [ ! -d "$BACKEND_SRC" ]; then
        echo -e "${RED}Error: backend module not found: $BACKEND_SRC${NC}"
        return 1
    fi

    if [ ! -f "$BACKEND_SRC/__manifest__.py" ]; then
        echo -e "${RED}Error: missing __manifest__.py in $BACKEND_SRC${NC}"
        return 1
    fi

    # Extract version from manifest
    VERSION=$(python3 -c "
ns = {}
exec(open('$BACKEND_SRC/__manifest__.py').read(), ns)
print(ns.get('manifest', {}).get('version', 'unknown'))
" 2>/dev/null || echo "unknown")

    OUTPUT="$DIST_DIR/${MODULE_NAME}_v${VERSION}.zip"

    echo -e "${YELLOW}Building: $MODULE_NAME v$VERSION${NC}"

    # Clean up any previous build
    TMPDIR=$(mktemp -d)
    trap "rm -rf $TMPDIR" EXIT

    MODULE_ROOT="$TMPDIR/$MODULE_NAME"
    mkdir -p "$MODULE_ROOT"

    # ── Copy backend files ────────────────────────────────────────────────
    echo "  Copying backend files..."
    rsync -a \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='*.pyo' \
        --exclude='.git' \
        --exclude='venv' \
        --exclude='.env' \
        "$BACKEND_SRC/" "$MODULE_ROOT/"

    # ── Copy frontend files (if present) ─────────────────────────────────
    if [ -d "$FRONTEND_SRC" ]; then
        echo "  Copying frontend files..."
        mkdir -p "$MODULE_ROOT/frontend"
        rsync -a \
            --exclude='node_modules' \
            --exclude='.git' \
            "$FRONTEND_SRC/" "$MODULE_ROOT/frontend/"
    else
        echo -e "${YELLOW}  No frontend directory found (${FRONTEND_SRC}) — skipping${NC}"
    fi

    # ── Create ZIP ────────────────────────────────────────────────────────
    echo "  Creating ZIP..."
    (cd "$TMPDIR" && zip -r "$OUTPUT" "$MODULE_NAME" -x "*.pyc" -x "*/__pycache__/*")

    echo -e "${GREEN}  ✅ Built: dist/${MODULE_NAME}_v${VERSION}.zip${NC}"
    echo "  Size: $(du -sh "$OUTPUT" | cut -f1)"

    trap - EXIT
    rm -rf "$TMPDIR"
}

# ── Main ──────────────────────────────────────────────────────────────────────

TARGET="${1:-}"

if [ -z "$TARGET" ]; then
    echo "Usage: $0 <module_name | all>"
    echo ""
    echo "Available modules:"
    for d in "$BACKEND_MODULES"/*/; do
        name="$(basename "$d")"
        if [ -f "$d/__manifest__.py" ]; then
            echo "  - $name"
        fi
    done
    exit 1
fi

if [ "$TARGET" = "all" ]; then
    echo -e "${GREEN}Building all modules...${NC}"
    for d in "$BACKEND_MODULES"/*/; do
        name="$(basename "$d")"
        if [ -f "$d/__manifest__.py" ]; then
            build_module "$name"
        fi
    done
else
    build_module "$TARGET"
fi

echo ""
echo -e "${GREEN}Done! ZIPs are in: dist/${NC}"
ls -lh "$DIST_DIR"/*.zip 2>/dev/null || echo "  (no ZIPs yet)"
