#!/usr/bin/env python3
"""
Script per registrare i menu dei moduli manualmente
"""
import requests
import json

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

# Platform menu
print("\n📋 Registering platform menu...")
platform_menu = {
    "module_id": "platform",
    "items": [
        {"id": "dashboard", "label": "Dashboard", "path": "/", "icon": "dashboard", "order_index": 0},
        {"id": "admin", "label": "Amministrazione", "path": "#", "icon": "settings", "order_index": 100},
        {"id": "admin.users", "label": "Utenti", "path": "/admin/users", "parent_id": "admin", "order_index": 1},
        {"id": "admin.roles", "label": "Ruoli", "path": "/admin/roles", "parent_id": "admin", "order_index": 2}
    ]
}
r = requests.post(f'{BASE_URL}/platform/menu/register', json=platform_menu, headers=headers)
print(f"   Status: {r.status_code} - Registered: {r.json().get('items_registered', 0)} items")

# Anagrafica menu
print("\n📋 Registering anagrafica menu...")
anagrafica_menu = {
    "module_id": "anagrafica_italiana",
    "items": [
        {"id": "anagrafica", "label": "Anagrafica", "path": "#", "icon": "users", "order_index": 10},
        {"id": "anagrafica.soggetti", "label": "Soggetti", "path": "/anagrafica/soggetti", "parent_id": "anagrafica", "order_index": 1},
        {"id": "anagrafica.persone_fisiche", "label": "Persone Fisiche", "path": "/anagrafica/persone-fisiche", "parent_id": "anagrafica", "order_index": 2},
        {"id": "anagrafica.persone_giuridiche", "label": "Persone Giuridiche", "path": "/anagrafica/persone-giuridiche", "parent_id": "anagrafica", "order_index": 3},
        {"id": "anagrafica.ruoli_azienda", "label": "Ruoli Azienda", "path": "/anagrafica/ruoli-azienda", "parent_id": "anagrafica", "order_index": 4},
        {"id": "anagrafica.domini", "label": "Domini", "path": "#", "parent_id": "anagrafica", "order_index": 90},
        {"id": "anagrafica.domini.comuni", "label": "Comuni", "path": "/anagrafica/domini/comuni", "parent_id": "anagrafica.domini", "order_index": 1},
        {"id": "anagrafica.domini.ruoli_tipi", "label": "Tipi Ruoli Azienda", "path": "/anagrafica/domini/ruoli-azienda-tipi", "parent_id": "anagrafica.domini", "order_index": 2}
    ]
}
r = requests.post(f'{BASE_URL}/platform/menu/register', json=anagrafica_menu, headers=headers)
print(f"   Status: {r.status_code} - Registered: {r.json().get('items_registered', 0)} items")

# Immobili menu
print("\n📋 Registering immobili menu...")
immobili_menu = {
    "module_id": "immobili",
    "items": [
        {"id": "immobili", "label": "Immobili", "path": "#", "icon": "building", "order_index": 20},
        {"id": "immobili.unita", "label": "Unità Immobiliari", "path": "/immobili/unita", "parent_id": "immobili", "order_index": 1}
    ]
}
r = requests.post(f'{BASE_URL}/platform/menu/register', json=immobili_menu, headers=headers)
print(f"   Status: {r.status_code} - Registered: {r.json().get('items_registered', 0)} items")

# Affitti lungo menu
print("\n📋 Registering affitti_lungo menu...")
affitti_menu = {
    "module_id": "affitti_lungo",
    "items": [
        {"id": "affitti", "label": "Affitti Lungo", "path": "#", "icon": "file-contract", "order_index": 30},
        {"id": "affitti.contratti", "label": "Contratti", "path": "/affitti/contratti", "parent_id": "affitti", "order_index": 1}
    ]
}
r = requests.post(f'{BASE_URL}/platform/menu/register', json=affitti_menu, headers=headers)
print(f"   Status: {r.status_code} - Registered: {r.json().get('items_registered', 0)} items")

# Affitti brevi menu
print("\n📋 Registering affitti_brevi menu...")
affitti_brevi_menu = {
    "module_id": "affitti_brevi",
    "items": [
        {"id": "affitti_brevi", "label": "Affitti Brevi", "path": "#", "icon": "calendar", "order_index": 35},
        {"id": "affitti_brevi.prenotazioni", "label": "Prenotazioni", "path": "/affitti-brevi/prenotazioni", "parent_id": "affitti_brevi", "order_index": 1},
        {"id": "affitti_brevi.calendario", "label": "Calendario", "path": "/affitti-brevi/calendario", "parent_id": "affitti_brevi", "order_index": 2},
        {"id": "affitti_brevi.scadenze", "label": "Scadenze", "path": "/affitti-brevi/scadenze", "parent_id": "affitti_brevi", "order_index": 3}
    ]
}
r = requests.post(f'{BASE_URL}/platform/menu/register', json=affitti_brevi_menu, headers=headers)
print(f"   Status: {r.status_code} - Registered: {r.json().get('items_registered', 0)} items")

print("\n✅ Menu registration completed!")

# Verify
print("\n🔍 Verifying menu items...")
r = requests.get(f'{BASE_URL}/platform/menu/', headers=headers)
menu = r.json()
print(f"Total menu items: {len(menu)}")
for item in menu[:5]:
    print(f"  - {item['label']} ({item['id']})")
