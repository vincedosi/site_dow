import requests
import os
import json
from datetime import datetime

# --- CONFIGURATION (Via GitHub Secrets) ---
TEAMS_WEBHOOK_URL = os.environ.get("TEAMS_WEBHOOK")

def charger_sites_depuis_fichier():
    sites = []
    if os.path.exists("url.txt"):
        with open("url.txt", "r", encoding="utf-8") as f:
            for ligne in f:
                parts = ligne.strip().split(",")
                if len(parts) >= 2 and not ligne.startswith("#"):
                    sites.append({"nom": parts[0].strip(), "url": parts[1].strip()})
    return sites

def envoyer_notif_teams(site_nom, site_url, erreur_msg):
    if not TEAMS_WEBHOOK_URL:
        print("⚠️ Pas d'URL Teams configurée.")
        return

    # Format ADAPTIVE CARD (Pour les nouveaux Workflows Teams)
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "msteams": {"width": "Full"},
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": f"🚨 ALERTE : {site_nom} est DOWN",
                            "size": "Large",
                            "weight": "Bolder",
                            "color": "Attention",
                            "wrap": True
                        },
                        {
                            "type": "FactSet",
                            "facts": [
                                {"title": "Heure", "value": datetime.now().strftime('%H:%M')},
                                {"title": "URL", "value": site_url},
                                {"title": "Erreur", "value": erreur_msg}
                            ]
                        }
                    ],
                    "actions": [
                        {
                            "type": "Action.OpenUrl",
                            "title": "Ouvrir le site",
                            "url": site_url
                        }
                    ]
                }
            }
        ]
    }

    try:
        response = requests.post(TEAMS_WEBHOOK_URL, json=payload)
        # Les Workflows renvoient souvent 202 Accepted
        if response.status_code in [200, 202]:
            print(f"✅ Notif Teams envoyée pour {site_nom}")
        else:
            print(f"❌ Erreur Teams ({response.status_code}) : {response.text}")
    except Exception as e:
        print(f"❌ Erreur de connexion Teams : {e}")

def verifier_sites():
    client_sites = charger_sites_depuis_fichier()
    if not client_sites: return

    resultats = []
    print(f"--- Démarrage Check ---")

    for site in client_sites:
        status = "UP"
        detail = "OK"
        print(f"Test: {site['nom']}")
        
        try:
            r = requests.get(site['url'], headers={'User-Agent': 'MonitorScript'}, timeout=10)
            if r.status_code != 200:
                status = "DOWN"
                detail = f"Erreur {r.status_code}"
                envoyer_notif_teams(site['nom'], site['url'], detail)
        except Exception as e:
            status = "DOWN"
            detail = str(e)
            envoyer_notif_teams(site['nom'], site['url'], detail)

        resultats.append({
            "nom": site["nom"],
            "url": site["url"],
            "status": status,
            "detail": detail,
            "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    with open("etat_sites.json", "w") as f:
        json.dump(resultats, f, indent=4)

if __name__ == "__main__":
    verifier_sites()
