#!/usr/bin/env python3
"""
check_service.py - Vérifier si un service est actif

NIVEAU 1 : Script ultra-simple pour débuter
Usage: python3 check_service.py nginx
"""

import subprocess
import sys

def check_service(service_name):
    """
    Vérifie si un service systemd est actif
    
    Args:
        service_name: Nom du service (ex: nginx, ssh, apache2)
    
    Returns:
        True si actif, False sinon
    """
    try:
        # Exécuter la commande systemctl
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,  # Capturer la sortie
            text=True             # Résultat en texte
        )
        
        # Vérifier si la sortie est "active"
        return result.stdout.strip() == 'active'
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


# Programme principal
if __name__ == "__main__":
    # Vérifier qu'on a un argument
    if len(sys.argv) < 2:
        print("Usage: python3 check_service.py <nom_service>")
        print("Exemple: python3 check_service.py nginx")
        sys.exit(1)
    
    # Récupérer le nom du service
    service = sys.argv[1]
    
    # Vérifier le service
    print(f"\n🔍 Vérification du service '{service}'...")
    
    if check_service(service):
        print(f"✅ Le service {service} est ACTIF\n")
        result = subprocess.run(
        ['systemctl', 'status', service],
        capture_output=True,
        text=True
        )
        print(result.stdout)
    else:
        print(f"❌ Le service {service} est INACTIF\n")
