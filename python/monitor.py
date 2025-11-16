#!/usr/bin/env python3
"""
monitor.py - Surveiller les ressources système en temps réel

NIVEAU 3 : Monitoring basique (CPU, RAM, Disque)
Usage: python3 monitor.py
       python3 monitor.py --interval 5
"""

import psutil
import time
import os
import sys
import argparse
from datetime import datetime


def clear_screen():
    """Efface l'écran du terminal"""
    os.system('clear' if os.name == 'posix' else 'cls')


def format_bytes(bytes_value):
    """
    Convertit les octets en format lisible (KB, MB, GB, etc.)
    
    Args:
        bytes_value: Nombre d'octets
    
    Returns:
        Chaîne formatée (ex: "1.5 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def draw_bar(percentage, width=40):
    """
    Dessine une barre de progression en ASCII
    
    Args:
        percentage: Pourcentage (0-100)
        width: Largeur de la barre
    
    Returns:
        Chaîne représentant la barre
    """
    filled = int((percentage / 100) * width)
    empty = width - filled
    
    # Choisir la couleur selon le niveau
    if percentage < 50:
        color = '\033[92m'  # Vert
    elif percentage < 80:
        color = '\033[93m'  # Jaune
    else:
        color = '\033[91m'  # Rouge
    
    reset = '\033[0m'
    
    bar = color + '█' * filled + reset + '░' * empty
    return f"[{bar}] {percentage:.1f}%"


def get_cpu_info():
    """
    Récupère les informations CPU
    
    Returns:
        Dictionnaire avec les infos CPU
    """
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    
    return {
        'percent': cpu_percent,
        'count': cpu_count,
        'freq': cpu_freq.current if cpu_freq else 0
    }


def get_memory_info():
    """
    Récupère les informations mémoire
    
    Returns:
        Dictionnaire avec les infos mémoire
    """
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    return {
        'total': mem.total,
        'available': mem.available,
        'used': mem.used,
        'percent': mem.percent,
        'swap_total': swap.total,
        'swap_used': swap.used,
        'swap_percent': swap.percent
    }


def get_disk_info():
    """
    Récupère les informations disque
    
    Returns:
        Dictionnaire avec les infos disque
    """
    disk = psutil.disk_usage('/')
    
    return {
        'total': disk.total,
        'used': disk.used,
        'free': disk.free,
        'percent': disk.percent
    }


def get_network_info():
    """
    Récupère les informations réseau
    
    Returns:
        Dictionnaire avec les infos réseau
    """
    net = psutil.net_io_counters()
    
    return {
        'bytes_sent': net.bytes_sent,
        'bytes_recv': net.bytes_recv,
        'packets_sent': net.packets_sent,
        'packets_recv': net.packets_recv
    }


def display_dashboard(cpu, memory, disk, network):
    """
    Affiche le tableau de bord complet
    
    Args:
        cpu: Infos CPU
        memory: Infos mémoire
        disk: Infos disque
        network: Infos réseau
    """
    clear_screen()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # En-tête
    print("\n" + "="*70)
    print(f"{'🖥️  MONITORING SYSTÈME':^70}")
    print(f"{'Mise à jour: ' + timestamp:^70}")
    print("="*70 + "\n")
    
    # Section CPU
    print("💻 CPU")
    print("-"*70)
    print(f"  Utilisation:  {draw_bar(cpu['percent'])}")
    print(f"  Cœurs:        {cpu['count']}")
    print(f"  Fréquence:    {cpu['freq']:.0f} MHz")
    
    # Section Mémoire
    print("\n💾 MÉMOIRE")
    print("-"*70)
    print(f"  RAM:          {draw_bar(memory['percent'])}")
    print(f"  Utilisée:     {format_bytes(memory['used'])} / {format_bytes(memory['total'])}")
    print(f"  Disponible:   {format_bytes(memory['available'])}")
    
    if memory['swap_total'] > 0:
        print(f"  SWAP:         {draw_bar(memory['swap_percent'])}")
        print(f"                {format_bytes(memory['swap_used'])} / {format_bytes(memory['swap_total'])}")
    
    # Section Disque
    print("\n💿 DISQUE")
    print("-"*70)
    print(f"  Utilisation:  {draw_bar(disk['percent'])}")
    print(f"  Utilisé:      {format_bytes(disk['used'])} / {format_bytes(disk['total'])}")
    print(f"  Libre:        {format_bytes(disk['free'])}")
    
    # Section Réseau
    print("\n🌐 RÉSEAU")
    print("-"*70)
    print(f"  Envoyé:       {format_bytes(network['bytes_sent'])}")
    print(f"  Reçu:         {format_bytes(network['bytes_recv'])}")
    print(f"  Paquets ↑:    {network['packets_sent']:,}")
    print(f"  Paquets ↓:    {network['packets_recv']:,}")
    
    # Alertes
    alerts = []
    if cpu['percent'] > 80:
        alerts.append("⚠️  CPU élevé")
    if memory['percent'] > 85:
        alerts.append("⚠️  Mémoire élevée")
    if disk['percent'] > 90:
        alerts.append("⚠️  Disque presque plein")
    
    if alerts:
        print("\n🚨 ALERTES")
        print("-"*70)
        for alert in alerts:
            print(f"  {alert}")
    
    # Pied de page
    print("\n" + "="*70)
    print("  Ctrl+C pour quitter")
    print("="*70)


def monitor(interval=3):
    """
    Boucle principale de monitoring
    
    Args:
        interval: Intervalle de rafraîchissement en secondes
    """
    print(f"\n🚀 Démarrage du monitoring (intervalle: {interval}s)")
    print("💡 Appuyez sur Ctrl+C pour arrêter\n")
    
    time.sleep(2)
    
    try:
        while True:
            # Collecter les données
            cpu = get_cpu_info()
            memory = get_memory_info()
            disk = get_disk_info()
            network = get_network_info()
            
            # Afficher le tableau de bord
            display_dashboard(cpu, memory, disk, network)
            
            # Attendre avant le prochain rafraîchissement
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n✋ Arrêt du monitoring...")
        print("👋 Au revoir!\n")
        sys.exit(0)


# Programme principal
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Monitoring des ressources système en temps réel'
    )
    
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=3,
        help='Intervalle de rafraîchissement en secondes (défaut: 3)'
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
    
    # Lancer le monitoring
    monitor(interval=args.interval)