#!/usr/bin/env python3
"""
alert_system.py - Système d'alertes pour le monitoring

NIVEAU 5 : Système d'alertes automatiques
Usage: python3 alert_system.py
       python3 alert_system.py --config alerts.json
"""

import psutil
import subprocess
import json
import smtplib
import argparse
import time
import sys
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path


class AlertSystem:
    """Système de gestion des alertes"""
    
    def __init__(self, config_file='alerts.json'):
        """
        Initialise le système d'alertes
        
        Args:
            config_file: Fichier de configuration JSON
        """
        self.config = self.load_config(config_file)
        self.alert_history = []
        self.last_alert_time = {}
        self.log_file = self.config.get('log_file', 'alerts.log')
        
    def load_config(self, config_file):
        """
        Charge la configuration depuis un fichier JSON
        
        Args:
            config_file: Chemin du fichier de configuration
        
        Returns:
            Dictionnaire de configuration
        """
        default_config = {
            'thresholds': {
                'cpu': 80.0,
                'memory': 85.0,
                'disk': 90.0,
                'swap': 80.0
            },
            'check_interval': 60,
            'alert_cooldown': 300,
            'email': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'from': 'alerts@example.com',
                'to': ['admin@example.com'],
                'password': ''
            },
            'webhook': {
                'enabled': False,
                'url': '',
                'method': 'POST'
            },
            'log_file': 'alerts.log',
            'console_alerts': True
        }
        
        # Charger la config depuis le fichier si existe
        if Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    # Fusionner avec la config par défaut
                    default_config.update(user_config)
                    print(f"✅ Configuration chargée depuis {config_file}")
            except Exception as e:
                print(f"⚠️  Erreur lecture config: {e}, utilisation config par défaut")
        else:
            print(f"ℹ️  Fichier {config_file} non trouvé, utilisation config par défaut")
            # Créer un exemple de config
            self.create_example_config(config_file)
        
        return default_config
    
    def create_example_config(self, config_file):
        """Crée un fichier de configuration d'exemple"""
        example_config = {
            'thresholds': {
                'cpu': 80.0,
                'memory': 85.0,
                'disk': 90.0,
                'swap': 80.0
            },
            'check_interval': 60,
            'alert_cooldown': 300,
            'email': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'from': 'alerts@example.com',
                'to': ['admin@example.com'],
                'password': 'votre_mot_de_passe'
            },
            'webhook': {
                'enabled': False,
                'url': 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL',
                'method': 'POST'
            },
            'log_file': 'alerts.log',
            'console_alerts': True
        }
        
        try:
            with open(config_file, 'w') as f:
                json.dump(example_config, f, indent=4)
            print(f"📝 Fichier de configuration exemple créé: {config_file}")
        except Exception as e:
            print(f"⚠️  Impossible de créer le fichier config: {e}")
    
    def log_alert(self, alert_type, message, level='WARNING'):
        """
        Enregistre une alerte dans le fichier log
        
        Args:
            alert_type: Type d'alerte (CPU, MEMORY, etc.)
            message: Message d'alerte
            level: Niveau (INFO, WARNING, CRITICAL)
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] [{alert_type}] {message}\n"
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"⚠️  Erreur écriture log: {e}")
        
        # Ajouter à l'historique en mémoire
        self.alert_history.append({
            'timestamp': timestamp,
            'type': alert_type,
            'message': message,
            'level': level
        })
        
        # Garder seulement les 100 dernières alertes
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]
    
    def can_send_alert(self, alert_type):
        """
        Vérifie si on peut envoyer une alerte (cooldown)
        
        Args:
            alert_type: Type d'alerte
        
        Returns:
            True si on peut envoyer, False sinon
        """
        cooldown = self.config.get('alert_cooldown', 300)
        
        if alert_type not in self.last_alert_time:
            return True
        
        time_since_last = time.time() - self.last_alert_time[alert_type]
        return time_since_last >= cooldown
    
    def send_email_alert(self, subject, message):
        """
        Envoie une alerte par email
        
        Args:
            subject: Sujet de l'email
            message: Corps de l'email
        """
        if not self.config['email']['enabled']:
            return False
        
        try:
            # Créer le message
            msg = MIMEMultipart()
            msg['From'] = self.config['email']['from']
            msg['To'] = ', '.join(self.config['email']['to'])
            msg['Subject'] = f"🚨 ALERTE SYSTÈME - {subject}"
            
            # Corps du message
            body = f"""
Alerte système détectée !

{message}

---
Serveur: {subprocess.getoutput('hostname')}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Ce message a été généré automatiquement par le système de monitoring.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connexion au serveur SMTP
            server = smtplib.SMTP(
                self.config['email']['smtp_server'],
                self.config['email']['smtp_port']
            )
            server.starttls()
            server.login(
                self.config['email']['from'],
                self.config['email']['password']
            )
            
            # Envoyer
            server.send_message(msg)
            server.quit()
            
            print(f"📧 Email envoyé: {subject}")
            self.log_alert('EMAIL', f"Email envoyé: {subject}", 'INFO')
            return True
            
        except Exception as e:
            print(f"❌ Erreur envoi email: {e}")
            self.log_alert('EMAIL', f"Erreur envoi: {e}", 'ERROR')
            return False
    
    def send_webhook_alert(self, message):
        """
        Envoie une alerte via webhook (Slack, Discord, etc.)
        
        Args:
            message: Message à envoyer
        """
        if not self.config['webhook']['enabled']:
            return False
        
        try:
            import requests
            
            # Format pour Slack/Discord
            payload = {
                'text': f"🚨 **ALERTE SYSTÈME**\n\n{message}",
                'username': 'Network Monitor',
                'icon_emoji': ':warning:'
            }
            
            response = requests.post(
                self.config['webhook']['url'],
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"📡 Webhook envoyé avec succès")
                self.log_alert('WEBHOOK', 'Webhook envoyé', 'INFO')
                return True
            else:
                print(f"⚠️  Webhook échoué: {response.status_code}")
                return False
                
        except ImportError:
            print("⚠️  Module 'requests' non installé pour les webhooks")
            print("   pip3 install requests")
            return False
        except Exception as e:
            print(f"❌ Erreur webhook: {e}")
            return False
    
    def check_cpu(self):
        """Vérifie l'utilisation CPU"""
        cpu_percent = psutil.cpu_percent(interval=1)
        threshold = self.config['thresholds']['cpu']
        
        if cpu_percent > threshold:
            if self.can_send_alert('CPU'):
                message = f"CPU élevé: {cpu_percent:.1f}% (seuil: {threshold}%)"
                
                # Console
                if self.config['console_alerts']:
                    print(f"\n⚠️  ALERTE: {message}")
                
                # Log
                self.log_alert('CPU', message, 'WARNING')
                
                # Email
                if self.config['email']['enabled']:
                    self.send_email_alert('CPU élevé', message)
                
                # Webhook
                if self.config['webhook']['enabled']:
                    self.send_webhook_alert(message)
                
                self.last_alert_time['CPU'] = time.time()
                return True
        
        return False
    
    def check_memory(self):
        """Vérifie l'utilisation mémoire"""
        mem = psutil.virtual_memory()
        threshold = self.config['thresholds']['memory']
        
        if mem.percent > threshold:
            if self.can_send_alert('MEMORY'):
                message = f"Mémoire élevée: {mem.percent:.1f}% (seuil: {threshold}%)"
                
                if self.config['console_alerts']:
                    print(f"\n⚠️  ALERTE: {message}")
                
                self.log_alert('MEMORY', message, 'WARNING')
                
                if self.config['email']['enabled']:
                    self.send_email_alert('Mémoire élevée', message)
                
                if self.config['webhook']['enabled']:
                    self.send_webhook_alert(message)
                
                self.last_alert_time['MEMORY'] = time.time()
                return True
        
        return False
    
    def check_disk(self):
        """Vérifie l'utilisation disque"""
        disk = psutil.disk_usage('/')
        threshold = self.config['thresholds']['disk']
        
        if disk.percent > threshold:
            if self.can_send_alert('DISK'):
                message = f"Disque plein: {disk.percent:.1f}% (seuil: {threshold}%)"
                
                if self.config['console_alerts']:
                    print(f"\n⚠️  ALERTE: {message}")
                
                self.log_alert('DISK', message, 'CRITICAL')
                
                if self.config['email']['enabled']:
                    self.send_email_alert('Disque plein', message)
                
                if self.config['webhook']['enabled']:
                    self.send_webhook_alert(message)
                
                self.last_alert_time['DISK'] = time.time()
                return True
        
        return False
    
    def check_swap(self):
        """Vérifie l'utilisation SWAP"""
        swap = psutil.swap_memory()
        
        if swap.total == 0:
            return False
        
        threshold = self.config['thresholds']['swap']
        
        if swap.percent > threshold:
            if self.can_send_alert('SWAP'):
                message = f"SWAP élevé: {swap.percent:.1f}% (seuil: {threshold}%)"
                
                if self.config['console_alerts']:
                    print(f"\n⚠️  ALERTE: {message}")
                
                self.log_alert('SWAP', message, 'WARNING')
                
                if self.config['email']['enabled']:
                    self.send_email_alert('SWAP élevé', message)
                
                if self.config['webhook']['enabled']:
                    self.send_webhook_alert(message)
                
                self.last_alert_time['SWAP'] = time.time()
                return True
        
        return False
    
    def check_service_down(self, service_name):
        """
        Vérifie si un service est arrêté
        
        Args:
            service_name: Nom du service à vérifier
        """
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            is_active = result.stdout.strip() == 'active'
            
            if not is_active:
                if self.can_send_alert(f'SERVICE_{service_name}'):
                    message = f"Service {service_name} est arrêté"
                    
                    if self.config['console_alerts']:
                        print(f"\n⚠️  ALERTE: {message}")
                    
                    self.log_alert('SERVICE', message, 'CRITICAL')
                    
                    if self.config['email']['enabled']:
                        self.send_email_alert(f'Service {service_name} arrêté', message)
                    
                    if self.config['webhook']['enabled']:
                        self.send_webhook_alert(message)
                    
                    self.last_alert_time[f'SERVICE_{service_name}'] = time.time()
                    return True
            
        except Exception as e:
            print(f"⚠️  Erreur vérification service {service_name}: {e}")
        
        return False
    
    def run_checks(self):
        """Exécute toutes les vérifications"""
        alerts_triggered = []
        
        # Vérifications système
        if self.check_cpu():
            alerts_triggered.append('CPU')
        
        if self.check_memory():
            alerts_triggered.append('MEMORY')
        
        if self.check_disk():
            alerts_triggered.append('DISK')
        
        if self.check_swap():
            alerts_triggered.append('SWAP')
        
        # Vérifications services
        services_to_check = ['nginx', 'ssh', 'mysql', 'postgresql']
        for service in services_to_check:
            if self.check_service_down(service):
                alerts_triggered.append(f'SERVICE_{service}')
        
        return alerts_triggered
    
    def show_status(self):
        """Affiche le statut actuel du système"""
        print("\n" + "="*70)
        print(f"{'🔍 STATUT SYSTÈME':^70}")
        print("="*70 + "\n")
        
        # CPU
        cpu = psutil.cpu_percent(interval=1)
        cpu_threshold = self.config['thresholds']['cpu']
        cpu_status = "✅" if cpu < cpu_threshold else "⚠️"
        print(f"{cpu_status} CPU:     {cpu:5.1f}% (seuil: {cpu_threshold}%)")
        
        # Mémoire
        mem = psutil.virtual_memory()
        mem_threshold = self.config['thresholds']['memory']
        mem_status = "✅" if mem.percent < mem_threshold else "⚠️"
        print(f"{mem_status} Mémoire: {mem.percent:5.1f}% (seuil: {mem_threshold}%)")
        
        # Disque
        disk = psutil.disk_usage('/')
        disk_threshold = self.config['thresholds']['disk']
        disk_status = "✅" if disk.percent < disk_threshold else "⚠️"
        print(f"{disk_status} Disque:  {disk.percent:5.1f}% (seuil: {disk_threshold}%)")
        
        # SWAP
        swap = psutil.swap_memory()
        if swap.total > 0:
            swap_threshold = self.config['thresholds']['swap']
            swap_status = "✅" if swap.percent < swap_threshold else "⚠️"
            print(f"{swap_status} SWAP:    {swap.percent:5.1f}% (seuil: {swap_threshold}%)")
        
        print("\n" + "="*70)
    
    def monitor_loop(self):
        """Boucle de monitoring continue"""
        interval = self.config.get('check_interval', 60)
        
        print("\n🚀 Démarrage du système d'alertes")
        print(f"⏱️  Intervalle de vérification: {interval} secondes")
        print(f"📧 Email: {'Activé' if self.config['email']['enabled'] else 'Désactivé'}")
        print(f"📡 Webhook: {'Activé' if self.config['webhook']['enabled'] else 'Désactivé'}")
        print(f"📝 Log file: {self.log_file}")
        print("\n💡 Appuyez sur Ctrl+C pour arrêter\n")
        
        try:
            while True:
                # Afficher le statut
                self.show_status()
                
                # Exécuter les vérifications
                alerts = self.run_checks()
                
                if alerts:
                    print(f"\n🚨 {len(alerts)} alerte(s) déclenchée(s): {', '.join(alerts)}")
                else:
                    print(f"\n✅ Aucune alerte - Système OK")
                
                print(f"\n⏳ Prochaine vérification dans {interval}s...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n✋ Arrêt du système d'alertes...")
            print(f"📊 Total d'alertes dans cette session: {len(self.alert_history)}")
            print("👋 Au revoir!\n")
            sys.exit(0)


# Programme principal
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Système d\'alertes pour le monitoring système'
    )
    
    parser.add_argument(
        '--config', '-c',
        default='alerts.json',
        help='Fichier de configuration (défaut: alerts.json)'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Mode test: exécute une seule vérification'
    )
    
    args = parser.parse_args()
    
    # Vérifier que psutil est installé
    try:
        import psutil
    except ImportError:
        print("❌ Erreur: Le module 'psutil' n'est pas installé")
        print("\n📦 Installation:")
        print("   pip3 install psutil")
        sys.exit(1)
    
    # Créer et lancer le système d'alertes
    alert_system = AlertSystem(config_file=args.config)
    
    if args.test:
        # Mode test
        print("\n🧪 Mode test - Vérification unique\n")
        alert_system.show_status()
        alerts = alert_system.run_checks()
        
        if alerts:
            print(f"\n🚨 {len(alerts)} alerte(s) détectée(s)")
        else:
            print("\n✅ Aucune alerte - Système OK")
    else:
        # Mode monitoring continu
        alert_system.monitor_loop()