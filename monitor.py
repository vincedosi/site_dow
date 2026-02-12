import requests
import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- CONFIGURATION SERVEUR (Via GitHub Secrets) ---
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
SMTP_SERVER = os.environ.get("SMTP_SERVER")
# On force la conversion en entier pour le port, avec 465 par défaut
try:
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))
except ValueError:
    SMTP_PORT = 465

def charger_emails_depuis_fichier():
    """Lit le fichier mail.txt pour trouver les destinataires"""
    emails = []
    nom_fichier = "mail.txt"
    
    # Si le fichier existe, on le lit
    if os.path.exists(nom_fichier):
        with open(nom_fichier, "r", encoding="utf-8") as f:
            for ligne in f:
                email = ligne.strip()
                # On garde l'email s'il n'est pas vide et ne commence pas par #
                if email and not email.startswith("#"):
                    emails.append(email)
    
    # SÉCURITÉ : Si la liste est vide ou le fichier absent, on s'envoie le mail à soi-même (l'expéditeur)
    if not emails and EMAIL_USER:
        print("⚠️ Fichier mail.txt vide ou absent. Envoi à l'expéditeur par défaut.")
        return [EMAIL_USER]
        
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

def envoyer_alerte(site_nom, site_url, erreur_msg):
    if not EMAIL_USER or not EMAIL_PASS or not SMTP_SERVER:
        print("⚠️ Config Email incomplète. Alerte ignorée.")
        return

    # On récupère la liste des gens à prévenir
    destinataires = charger_emails_depuis_fichier()

    subject = f"🚨 ALERTE: {site_nom} est DOWN"
    body = f"Le site {site_nom} ({site_url}) est hors ligne.\nErreur : {erreur_msg}\nHeure : {datetime.now().strftime('%H:%M')}"

    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    # On joint les emails par une virgule pour l'en-tête "A"
    msg['To'] = ", ".join(destinataires)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Gestion automatique SSL (465) ou STARTTLS (587)
        if SMTP_PORT == 587:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
            
        with server:
            server.login(EMAIL_USER, EMAIL_PASS)
            # send_message gère l'envoi à la liste présente dans msg['To']
            server.send_message(msg)
            print(f"📧 Mail envoyé à {len(destinataires)} destinataires via {SMTP_SERVER}")
            
    except Exception as e:
        print(f"❌ Erreur envoi mail : {e}")

def verifier_sites():
    client_sites = charger_sites_depuis_fichier()
    if not client_sites: return

    resultats = []
    print(f"--- Démarrage Check ---")

    for site in client_sites:
        status = "UP"
        detail = "OK"
        
        try:
            r = requests.get(site['url'], headers={'User-Agent': 'MonitorScript'}, timeout=10)
            if r.status_code != 200:
                status = "DOWN"
                detail = f"Erreur {r.status_code}"
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

    with open("etat_sites.json", "w") as f:
        json.dump(resultats, f, indent=4)

if __name__ == "__main__":
    verifier_sites()
