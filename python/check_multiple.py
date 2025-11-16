#!/usr/bin/env python3
"""
check_multiple.py - Vérifier plusieurs services d'un coup

NIVEAU 2 : Gestion de plusieurs services
Usage: python3 check_multiple.py nginx ssh mysql
       python3 check_multiple.py --all
"""

import subprocess
import sys

def check_service(service_name):
    """
    Vérifie si un service systemd est actif
    
    Args:
        service_name: Nom du service
    
    Returns:
        True si actif, False sinon
    """
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() == 'active'
    except Exception:
        return False


def check_service_enabled(service_name):
    """
    Vérifie si un service est activé au démarrage
    
    Args:
        service_name: Nom du service
    
    Returns:
        True si enabled, False sinon
    """
    try:
        result = subprocess.run(
            ['systemctl', 'is-enabled', service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() == 'enabled'
    except Exception:
        return False


def display_results(services):
    """
    Affiche les résultats sous forme de tableau
    
    Args:
        services: Liste des noms de services à vérifier
    """
    print("\n" + "="*60)
    print("           🔍 VÉRIFICATION DES SERVICES")
    print("="*60 + "\n")
    
    # En-tête du tableau
    print(f"{'Service':<15} {'Statut':<15} {'Démarrage auto':<15}")
    print("-"*60)
    
    # Statistiques
    active_count = 0
    inactive_count = 0
    
    # Vérifier chaque service
    for service in services:
        is_active = check_service(service)
        is_enabled = check_service_enabled(service)
        
        # Statut avec emoji
        status = "✅ Actif" if is_active else "❌ Inactif"
        enabled = "🟢 Oui" if is_enabled else "🔴 Non"
        
        # Afficher la ligne
        print(f"{service:<15} {status:<15} {enabled:<15}")
        
        # Compter
        if is_active:
            active_count += 1
        else:
            inactive_count += 1
    
    # Résumé
    print("-"*60)
    print(f"\n📊 Résumé: {active_count} actif(s) | {inactive_count} inactif(s)\n")
    print("="*60 + "\n")


# Services par défaut pour l'option --all
DEFAULT_SERVICES = [
    'nginx',
    'apache2',
    'ssh',
    'mysql',
    'postgresql',
    'docker',
    'cron'
]


# Programme principal
if __name__ == "__main__":
    # Vérifier qu'on a des arguments
    if len(sys.argv) < 2:
        print("Usage: python3 check_multiple.py <service1> <service2> ...")
        print("       python3 check_multiple.py --all")
        print("\nExemples:")
        print("  python3 check_multiple.py nginx ssh mysql")
        print("  python3 check_multiple.py --all")
        sys.exit(1)
    
    # Option --all : vérifier tous les services par défaut
    if sys.argv[1] == '--all':
        services_to_check = DEFAULT_SERVICES
        print("🔍 Vérification de tous les services par défaut...")
    else:
        # Récupérer les services depuis les arguments
        services_to_check = sys.argv[1:]
        print(f"🔍 Vérification de {len(services_to_check)} service(s)...")
    
    # Afficher les résultats
    display_results(services_to_check)