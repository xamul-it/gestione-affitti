#!/bin/bash
# Quick test script to verify backend starts with all fixes

echo "============================================================"
echo "BACKEND STARTUP TEST"
echo "============================================================"

cd /home/htpc/test/gestione-affitti/backend

# Activate venv
source venv/bin/activate

echo ""
echo "1. Checking Python environment..."
python --version

echo ""
echo "2. Verifying critical files exist..."
FILES=(
    "modules/anagrafica_italiana/__init__.py"
    "modules/anagrafica_italiana/routes/domini.py"
    "modules/anagrafica_italiana/routes/ruoli_azienda.py"
    "modules/immobili/models/condomini.py"
    "alembic/versions/2025122601_make_nome_optional.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file NOT FOUND"
    fi
done

echo ""
echo "3. Checking router registrations..."
grep -A 7 "^ROUTERS = " modules/anagrafica_italiana/__init__.py | grep -v "^#"

echo ""
echo "4. Checking Scadenze menu removal..."
if grep -q '"id": "platform.scadenze"' app/main.py; then
    echo "   ❌ Scadenze still in menu"
else
    echo "   ✅ Scadenze removed from menu"
fi

echo ""
echo "5. Checking Condominio model..."
if grep -q 'nome = Column(String(255), nullable=True)' modules/immobili/models/condomini.py; then
    echo "   ✅ Condominio.nome is nullable"
else
    echo "   ❌ Condominio.nome is still required"
fi

echo ""
echo "============================================================"
echo "VERIFICATION COMPLETE"
echo "============================================================"
echo ""
echo "To start backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python app/main.py"
echo ""
echo "Expected in logs:"
echo "  ✅ 'Registered 6 routers' for anagrafica_italiana"
echo "  ✅ No 'platform.scadenze' in menu registration"
echo ""
echo "To test endpoints:"
echo "  curl http://localhost:8000/api/v1/anagrafica/domini/comuni/?limit=1"
echo "============================================================"
