import requests
import os
import json
from datetime import datetime

# --- CONFIGURATION ---
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
        return

    print(f"⚠️ Envoi alerte Teams pour {site_nom}...")

    # On utilise le format QUI MARCHE (Adaptive Card simple)
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.2",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": f"🚨 ALERTE : {site_nom} est DOWN",
                            "size": "Large",
                            "weight": "Bolder",
                            "color": "Attention"
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
        requests.post(TEAMS_WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"Erreur envoi Teams : {e}")

def verifier_sites():
    client_sites = charger_sites_depuis_fichier()
    if not client_sites:
        print("Pas de sites dans url.txt")
        return

    resultats = []
    print(f"--- Démarrage Check de {len(client_sites)} sites ---")

    for site in client_sites:
        status = "UP"
        detail = "OK"
        print(f"Test: {site['nom']}...", end="")
        
        try:
            # Timeout court (10s) pour ne pas bloquer
            r = requests.get(site['url'], headers={'User-Agent': 'MonitorScript'}, timeout=10)
            
            if r.status_code != 200:
                status = "DOWN"
                detail = f"Erreur HTTP {r.status_code}"
                print(f" ❌ DOWN ({detail})")
                envoyer_notif_teams(site['nom'], site['url'], detail)
            else:
                print(" ✅ OK")
                
        except Exception as e:
            status = "DOWN"
            detail = str(e)
            print(f" ❌ CRASH ({detail})")
            envoyer_notif_teams(site['nom'], site['url'], detail)

        # On enregistre tout pour le futur Dashboard Streamlit
        resultats.append({
            "nom": site["nom"],
            "url": site["url"],
            "status": status,
            "detail": detail,
            "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    # Sauvegarde du fichier JSON
    with open("etat_sites.json", "w") as f:
        json.dump(resultats, f, indent=4)
    print("--- Terminé et Sauvegardé ---")

if __name__ == "__main__":
    verifier_sites()
