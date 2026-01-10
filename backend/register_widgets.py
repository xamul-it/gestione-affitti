#!/usr/bin/env python3
"""
Script per registrare i widget dei moduli manualmente
"""
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
print("🔐 Login...")
response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "changeme123"
})
token = response.json()['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
print(f"✅ Token obtained")

# Anagrafica widgets
print("\n📊 Registering anagrafica widgets...")
widgets = [
    {
        "widget_id": "anagrafica_stats",
        "module_id": "anagrafica_italiana",
        "name": "Statistiche Anagrafica",
        "description": "Statistiche sui soggetti anagrafici",
        "widget_type": "stats_card",
        "default_config": {"show_chart": True},
        "order_index": 1
    }
]
for widget in widgets:
    r = requests.post(f'{BASE_URL}/platform/dashboard/widgets/register', json=widget, headers=headers)
    print(f"   {widget['name']}: {r.status_code}")

# Immobili widgets
print("\n📊 Registering immobili widgets...")
widgets = [
    {
        "widget_id": "immobili_stats",
        "module_id": "immobili",
        "name": "Statistiche Immobili",
        "description": "Panoramica unità immobiliari",
        "widget_type": "stats_card",
        "default_config": {},
        "order_index": 2
    }
]
for widget in widgets:
    r = requests.post(f'{BASE_URL}/platform/dashboard/widgets/register', json=widget, headers=headers)
    print(f"   {widget['name']}: {r.status_code}")

# Affitti lungo widgets
print("\n📊 Registering affitti_lungo widgets...")
widgets = [
    {
        "widget_id": "contratti_attivi",
        "module_id": "affitti_lungo",
        "name": "Contratti Attivi",
        "description": "Lista contratti attivi",
        "widget_type": "list",
        "default_config": {},
        "order_index": 3
    },
    {
        "widget_id": "incassi_mese",
        "module_id": "affitti_lungo",
        "name": "Incassi del Mese",
        "description": "Riepilogo incassi mensili",
        "widget_type": "chart",
        "default_config": {},
        "order_index": 4
    }
]
for widget in widgets:
    r = requests.post(f'{BASE_URL}/platform/dashboard/widgets/register', json=widget, headers=headers)
    print(f"   {widget['name']}: {r.status_code}")

# Affitti brevi widgets
print("\n📊 Registering affitti_brevi widgets...")
widgets = [
    {
        "widget_id": "affitti_brevi_calendar",
        "module_id": "affitti_brevi",
        "name": "Calendario Prenotazioni",
        "description": "Vista calendario prenotazioni brevi",
        "widget_type": "calendar",
        "default_config": {},
        "order_index": 5
    },
    {
        "widget_id": "affitti_brevi_scadenze",
        "module_id": "affitti_brevi",
        "name": "Scadenze Prossime",
        "description": "Scadenze comunicazioni e tasse",
        "widget_type": "list",
        "default_config": {},
        "order_index": 6
    }
]
for widget in widgets:
    r = requests.post(f'{BASE_URL}/platform/dashboard/widgets/register', json=widget, headers=headers)
    print(f"   {widget['name']}: {r.status_code}")

print("\n✅ Widget registration completed!")

# Verify
print("\n🔍 Verifying widgets...")
r = requests.get(f'{BASE_URL}/platform/dashboard/available-widgets', headers=headers)
if r.status_code == 200:
    widgets = r.json()
    print(f"Total available widgets: {len(widgets)}")
    for widget in widgets:
        print(f"  - {widget['name']} ({widget['widget_id']})")
else:
    print(f"Error: {r.status_code}")
