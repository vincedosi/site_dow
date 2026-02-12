import requests
import smtplib
import os
import json
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- CONFIGURATION EMAIL ---
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
EMAIL_TO = EMAIL_USER 

def charger_sites_depuis_fichier():
    """Lit le fichier url.txt et retourne une liste de sites"""
    sites = []
    nom_fichier = "url.txt"
    
    if not os.path.exists(nom_fichier):
        print(f"⚠️ Erreur : Le fichier {nom_fichier} est introuvable !")
        return []

    try:
        with open(nom_fichier, "r", encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()
                # On ignore les lignes vides ou celles qui commencent par #
                if not ligne or ligne.startswith("#"):
                    continue
                
                # On sépare le Nom et l'URL par la virgule
                parties = ligne.split(",")
                
                if len(parties) >= 2:
                    nom = parties[0].strip()
                    url = parties[1].strip()
                    sites.append({"nom": nom, "url": url})
                else:
                    print(f"⚠️ Ligne mal formatée ignorée : {ligne}")
    except Exception as e:
        print(f"Erreur de lecture du fichier : {e}")
        
    return sites

def envoyer_alerte(site_nom, site_url, erreur_msg):
    if not EMAIL_USER or not EMAIL_PASS:
        print("⚠️ Pas d'identifiants Email. Alerte ignorée.")
        return

    subject = f"🚨 ALERTE: {site_nom} est DOWN"
    body = f"Le site {site_nom} ({site_url}) est hors ligne.\nErreur : {erreur_msg}\nHeure : {datetime.now().strftime('%H:%M')}"

    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
            print(f"📧 Mail envoyé pour {site_nom}")
    except Exception as e:
        print(f"❌ Erreur mail : {e}")

def verifier_sites():
    # 1. On charge la liste depuis le fichier texte
    client_sites = charger_sites_depuis_fichier()
    
    if not client_sites:
        print("Aucun site à tester. Vérifie ton fichier url.txt")
        return

    resultats = []
    print(f"--- Check de {len(client_sites)} sites... ---")

    for site in client_sites:
        status = "UP"
        detail = "OK"
        print(f"Test: {site['nom']}")
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (MonitorScript)'}
            response = requests.get(site['url'], headers=headers, timeout=10)
            
            if response.status_code != 200:
                status = "DOWN"
                detail = f"Erreur {response.status_code}"
                envoyer_alerte(site['nom'], site['url'], detail)
            
        except Exception as e:
            status = "DOWN"
            detail = str(e)
            envoyer_alerte(site['nom'], site['url'], detail)

        resultats.append({
            "nom": site["nom"],
            "url": site["url"],
            "status": status,
            "detail": detail,
            "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    # Sauvegarde JSON
    with open("etat_sites.json", "w") as f:
        json.dump(resultats, f, indent=4)
    print("--- Terminé ---")

if __name__ == "__main__":
    verifier_sites()
