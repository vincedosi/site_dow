import requests
import os
import json
from datetime import datetime

# --- CONFIGURATION API BREVO ---
API_KEY = os.environ.get("BREVO_KEY")
SENDER_EMAIL = "alerte@mon-monitor.com" # Tu peux mettre n'importe quoi ici, ex: no-reply@ton-domaine.com
SENDER_NAME = "🤖 Bot Monitor"

def charger_emails_depuis_fichier():
    """Lit le fichier mail.txt"""
    emails = []
    if os.path.exists("mail.txt"):
        with open("mail.txt", "r", encoding="utf-8") as f:
            for ligne in f:
                email = ligne.strip()
                if email and not email.startswith("#"):
                    emails.append(email)
    
    if not emails:
        print("⚠️ Fichier mail.txt vide !")
        return []
    return emails

def charger_sites_depuis_fichier():
    sites = []
    if os.path.exists("url.txt"):
        with open("url.txt", "r", encoding="utf-8") as f:
            for ligne in f:
                parts = ligne.strip().split(",")
                if len(parts) >= 2 and not ligne.startswith("#"):
                    sites.append({"nom": parts[0].strip(), "url": parts[1].strip()})
    return sites

def envoyer_alerte_api(site_nom, site_url, erreur_msg):
    if not API_KEY:
        print("⚠️ Clé API Brevo manquante. Alerte ignorée.")
        return

    destinataires = charger_emails_depuis_fichier()
    if not destinataires: return

    # On prépare la liste des destinataires au format Brevo
    to_list = [{"email": email} for email in destinataires]

    url_api = "https://api.brevo.com/v3/smtp/email"
    
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": to_list,
        "subject": f"🚨 ALERTE: {site_nom} est DOWN",
        "htmlContent": f"""
        <html><body>
            <h2>⚠️ Problème détecté</h2>
            <p>Le site <b>{site_nom}</b> ({site_url}) ne répond plus.</p>
            <p><b>Erreur :</b> {erreur_msg}</p>
            <p><i>Check effectué à {datetime.now().strftime('%H:%M')}</i></p>
        </body></html>
        """
    }
    
    headers = {
        "accept": "application/json",
        "api-key": API_KEY,
        "content-type": "application/json"
    }

    try:
        response = requests.post(url_api, json=payload, headers=headers)
        if response.status_code == 201:
            print(f"✅ Alerte envoyée avec succès à {len(destinataires)} personnes.")
        else:
            print(f"❌ Erreur API Brevo: {response.text}")
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")

def verifier_sites():
    client_sites = charger_sites_depuis_fichier()
    if not client_sites: return

    resultats = []
    print(f"--- Démarrage Check (Mode API) ---")

    for site in client_sites:
        status = "UP"
        detail = "OK"
        print(f"Test: {site['nom']}")
        
        try:
            r = requests.get(site['url'], headers={'User-Agent': 'MonitorScript'}, timeout=10)
            if r.status_code != 200:
                status = "DOWN"
                detail = f"Erreur {r.status_code}"
                envoyer_alerte_api(site['nom'], site['url'], detail)
        except Exception as e:
            status = "DOWN"
            detail = str(e)
            envoyer_alerte_api(site['nom'], site['url'], detail)

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
