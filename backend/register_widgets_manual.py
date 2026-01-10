#!/usr/bin/env python3
"""
Script per registrare manualmente i widget dei moduli.
Utile quando il backend non riesce a auto-registrarli durante lo startup.
"""
import requests
import sys

API_BASE = "http://localhost:8000/api/v1"

# Widget per ogni modulo
WIDGETS_BY_MODULE = {
    "anagrafica_italiana": [
        {
            "id": "anagrafica_italiana.stats_soggetti",
            "title": "Statistiche Anagrafiche",
            "component": "StatsSoggettiWidget",
            "description": "Panoramica generale delle anagrafiche (persone fisiche e giuridiche)",
            "default_width": 3,
            "default_height": 3,
            "category": "stats",
            "required_permission": "soggetto.view"
        },
    ],
    "immobili": [
        {
            "id": "immobili.stats",
            "title": "Statistiche Immobili",
            "component": "ImmobiliStatsWidget",
            "description": "Panoramica generale delle unità immobiliari, proprietari e condomini",
            "default_width": 6,
            "default_height": 4,
            "category": "stats",
            "required_permission": "immobile.view"
        },
        {
            "id": "immobili.certificati_scadenza",
            "title": "Certificati in Scadenza",
            "component": "CertificatiScadenzaWidget",
            "description": "Monitoraggio certificati energetici in scadenza o scaduti",
            "default_width": 6,
            "default_height": 4,
            "category": "alerts",
            "required_permission": "certificato_energetico.view"
        },
    ],
    "affitti_lungo": [
        # Aggiungi qui i widget di affitti_lungo se ne hai
    ]
}

def register_widgets():
    """Registra i widget per tutti i moduli"""
    print("🚀 Registrazione widget...")
    print()

    total_success = 0
    total_failed = 0

    for module_id, widgets in WIDGETS_BY_MODULE.items():
        if not widgets:
            print(f"⏭️  Modulo '{module_id}': nessun widget da registrare")
            continue

        print(f"📦 Modulo '{module_id}': registrazione {len(widgets)} widget...")

        try:
            response = requests.post(
                f"{API_BASE}/platform/dashboard/register-widgets",
                json={
                    "module_id": module_id,
                    "widgets": widgets
                },
                timeout=30.0
            )

            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Registrati {result['widgets_registered']} widget")
                print(f"   ℹ️  Rimossi {result['widgets_deleted']} widget precedenti")
                total_success += result['widgets_registered']
            else:
                print(f"   ❌ Errore HTTP {response.status_code}: {response.text}")
                total_failed += len(widgets)

        except Exception as e:
            print(f"   ❌ Errore: {e}")
            total_failed += len(widgets)

        print()

    print("=" * 60)
    print(f"✅ Widget registrati con successo: {total_success}")
    print(f"❌ Widget falliti: {total_failed}")
    print("=" * 60)

    return total_failed == 0

if __name__ == "__main__":
    success = register_widgets()
    sys.exit(0 if success else 1)
