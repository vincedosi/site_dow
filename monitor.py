import requests
import smtplib
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- CONFIGURATION (Via GitHub Secrets) ---
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
EMAIL_TO = EMAIL_USER 
# On ajoute le serveur et le port (ex: ssl0.ovh.net)
SMTP_SERVER = os.environ.get("SMTP_SERVER")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 465)) # 465 par défaut, 587 pour Outlook

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

    subject = f"🚨 ALERTE: {site_nom} est DOWN"
    body = f"Le site {site_nom} ({site_url}) est hors ligne.\nErreur : {erreur_msg}\nHeure : {datetime.now().strftime('%H:%M')}"

    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Gestion automatique SSL (465) ou STARTTLS (587)
        if SMTP_PORT == 587:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls() # Sécurité pour Outlook/Office365
        else:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) # Sécurité pour OVH/Autres
            
        with server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
            print(f"📧 Mail envoyé via {SMTP_SERVER}")
            
    except Exception as e:
        print(f"❌ Erreur mail : {e}")
