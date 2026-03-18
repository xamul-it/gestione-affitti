#!/usr/bin/env python3
"""
Quick Import Test for Multi-File Document System
Verifies that all new modules, models, services can be imported correctly.
"""

import sys
from pathlib import Path

# Colors for output
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color

def test_import(module_name, description):
    """Test import of a module"""
    try:
        exec(f"import {module_name}")
        print(f"{GREEN}✓{NC} {description}: {module_name}")
        return True
    except ImportError as e:
        print(f"{RED}✗{NC} {description}: {module_name}")
        print(f"  Error: {e}")
        return False

def test_from_import(from_module, import_items, description):
    """Test from...import statement"""
    try:
        exec(f"from {from_module} import {import_items}")
        print(f"{GREEN}✓{NC} {description}: from {from_module} import {import_items}")
        return True
    except ImportError as e:
        print(f"{RED}✗{NC} {description}")
        print(f"  Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Multi-File Document System - Import Verification")
    print("=" * 60)
    print()

    results = []

    # Test Python dependencies
    print(f"{YELLOW}[1/5] Testing Python Dependencies...{NC}")
    results.append(test_import("PIL", "Pillow (image processing)"))
    results.append(test_import("pdf2image", "pdf2image (PDF conversion)"))
    results.append(test_import("Levenshtein", "python-Levenshtein (similarity)"))
    print()

    # Test core services
    print(f"{YELLOW}[2/5] Testing Core Services...{NC}")
    results.append(test_from_import(
        "app.core.file_normalization",
        "FileNormalizationService, file_normalization",
        "File Normalization Service"
    ))
    results.append(test_from_import(
        "app.core.file_storage",
        "file_storage",
        "File Storage Service"
    ))
    results.append(test_from_import(
        "app.core.platform_services.document_parsing_service",
        "DocumentParsingService",
        "Document Parsing Service"
    ))
    print()

    # Test models
    print(f"{YELLOW}[3/5] Testing Models...{NC}")
    results.append(test_from_import(
        "modules.anagrafica_italiana.models",
        "Documento, DocumentoFile",
        "Documento & DocumentoFile models"
    ))
    results.append(test_from_import(
        "modules.anagrafica_italiana.models.documento_file",
        "DocumentoFile",
        "DocumentoFile model (direct)"
    ))
    print()

    # Test schemas
    print(f"{YELLOW}[4/5] Testing Schemas...{NC}")
    results.append(test_from_import(
        "modules.anagrafica_italiana.schemas",
        "FindSimilarRequest",
        "FindSimilarRequest schema"
    ))
    results.append(test_from_import(
        "modules.anagrafica_italiana.schemas.similarity_matching",
        "FindSimilarRequest",
        "FindSimilarRequest (direct)"
    ))
    print()

    # Test services
    print(f"{YELLOW}[5/5] Testing Module Services...{NC}")
    results.append(test_from_import(
        "modules.anagrafica_italiana.services.similarity_matching_service",
        "SimilarityMatchingService",
        "Similarity Matching Service"
    ))
    results.append(test_from_import(
        "modules.anagrafica_italiana.services.document_service",
        "DocumentService",
        "Document Service"
    ))
    print()

    # Summary
    print("=" * 60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"{GREEN}✓ All imports successful! ({passed}/{total}){NC}")
        print()
        print("System is ready for use.")
        return 0
    else:
        print(f"{RED}✗ Some imports failed ({passed}/{total}){NC}")
        print()
        print("Please check:")
        print("  1. All dependencies installed: pip install -r requirements.txt")
        print("  2. Running from backend/ directory")
        print("  3. PYTHONPATH includes modules directory")
        return 1

if __name__ == "__main__":
    # Add modules to Python path
    backend_dir = Path(__file__).parent
    modules_dir = backend_dir / "modules"
    if modules_dir not in sys.path:
        sys.path.insert(0, str(modules_dir))

    sys.exit(main())
