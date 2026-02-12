import requests
import os
import json

# Récupération du Secret
TEAMS_WEBHOOK_URL = os.environ.get("TEAMS_WEBHOOK")

def test_force_teams():
    print("--- DÉBUT DU TEST FORCE ---")
    
    if not TEAMS_WEBHOOK_URL:
        print("❌ ERREUR : Le secret TEAMS_WEBHOOK est vide ou mal configuré !")
        return

    print(f"URL trouvée (début) : {TEAMS_WEBHOOK_URL[:30]}...")

    # On tente le format le plus simple du monde pour Teams (Adaptive Card basique)
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
                            "text": "👋 CECI EST UN TEST",
                            "size": "Large",
                            "weight": "Bolder"
                        },
                        {
                            "type": "TextBlock",
                            "text": "Si tu lis ça, c'est que la connexion marche !"
                        }
                    ]
                }
            }
        ]
    }

    print("Envoi de la requête à Teams...")
    
    try:
        response = requests.post(TEAMS_WEBHOOK_URL, json=payload)
        
        # C'EST ICI QUE TOUT SE JOUE
        print(f"👉 CODE RETOUR : {response.status_code}")
        print(f"👉 RÉPONSE TEXTE : {response.text}")
        
        if response.status_code == 202:
            print("✅ SUCCÈS : Teams a accepté le message (202 Accepted). Regarde ton canal !")
        elif response.status_code == 200:
            print("✅ SUCCÈS : Message envoyé (200 OK).")
        else:
            print("❌ ÉCHEC : Teams a refusé le message.")

    except Exception as e:
        print(f"❌ CRASH : {e}")

    print("--- FIN DU TEST ---")

if __name__ == "__main__":
    test_force_teams()
