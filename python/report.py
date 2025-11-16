#!/usr/bin/env python3
"""
report.py - Générer un rapport HTML des ressources système

NIVEAU 4 : Génération de rapports
Usage: python3 report.py
       python3 report.py --output mon-rapport.html
"""

import psutil
import subprocess
import socket
import argparse
from datetime import datetime


def check_service(service_name):
    """
    Vérifie si un service est actif
    
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
    except:
        return False


def format_bytes(bytes_value):
    """Convertit les octets en format lisible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def collect_system_info():
    """
    Collecte toutes les informations système
    
    Returns:
        Dictionnaire avec toutes les infos
    """
    # Informations de base
    hostname = socket.gethostname()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    
    # Mémoire
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    # Disque
    disk = psutil.disk_usage('/')
    
    # Réseau
    net = psutil.net_io_counters()
    
    # Services à vérifier
    services = ['nginx', 'apache2', 'ssh', 'mysql', 'postgresql', 'docker']
    services_status = {}
    for service in services:
        services_status[service] = check_service(service)
    
    return {
        'hostname': hostname,
        'timestamp': timestamp,
        'cpu': {
            'percent': cpu_percent,
            'count': cpu_count,
            'freq': cpu_freq.current if cpu_freq else 0
        },
        'memory': {
            'total': mem.total,
            'used': mem.used,
            'available': mem.available,
            'percent': mem.percent
        },
        'swap': {
            'total': swap.total,
            'used': swap.used,
            'percent': swap.percent
        },
        'disk': {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        },
        'network': {
            'bytes_sent': net.bytes_sent,
            'bytes_recv': net.bytes_recv,
            'packets_sent': net.packets_sent,
            'packets_recv': net.packets_recv
        },
        'services': services_status
    }


def get_status_class(percent):
    """Retourne la classe CSS selon le pourcentage"""
    if percent < 50:
        return 'good'
    elif percent < 80:
        return 'warning'
    else:
        return 'danger'


def generate_html_report(data, output_file='rapport.html'):
    """
    Génère un rapport HTML
    
    Args:
        data: Dictionnaire avec les données système
        output_file: Nom du fichier de sortie
    """
    
    # Générer les lignes de services
    services_rows = ""
    for service, is_active in data['services'].items():
        status_class = 'service-active' if is_active else 'service-inactive'
        status_text = '✅ Actif' if is_active else '❌ Inactif'
        
        services_rows += f"""
        <tr>
            <td>{service}</td>
            <td class="{status_class}">{status_text}</td>
        </tr>
        """
    
    # Template HTML complet
    html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport Système - {data['hostname']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 40px;
            background: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            border-left: 5px solid #667eea;
        }}
        
        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
        }}
        
        .card h3 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.2em;
        }}
        
        .stat {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        
        .stat:last-child {{
            border-bottom: none;
        }}
        
        .stat-label {{
            font-weight: 600;
            color: #666;
        }}
        
        .stat-value {{
            color: #333;
            font-weight: 500;
        }}
        
        .progress {{
            width: 100%;
            height: 25px;
            background: #e9ecef;
            border-radius: 12px;
            overflow: hidden;
            margin: 10px 0;
        }}
        
        .progress-bar {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 0.9em;
            transition: width 0.3s;
        }}
        
        .progress-bar.good {{
            background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
        }}
        
        .progress-bar.warning {{
            background: linear-gradient(90deg, #ffc107 0%, #fd7e14 100%);
        }}
        
        .progress-bar.danger {{
            background: linear-gradient(90deg, #dc3545 0%, #c82333 100%);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
        }}
        
        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 15px;
            border-bottom: 1px solid #eee;
        }}
        
        tr:last-child td {{
            border-bottom: none;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .service-active {{
            color: #28a745;
            font-weight: 600;
        }}
        
        .service-inactive {{
            color: #dc3545;
            font-weight: 600;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px 40px;
            text-align: center;
            color: #666;
            border-top: 1px solid #dee2e6;
        }}
        
        .alert {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 10px;
            padding: 15px 20px;
            margin: 20px 0;
            color: #856404;
        }}
        
        .alert.danger {{
            background: #f8d7da;
            border-color: #dc3545;
            color: #721c24;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- En-tête -->
        <div class="header">
            <h1>🖥️ Rapport Système</h1>
            <p><strong>Serveur:</strong> {data['hostname']}</p>
            <p><strong>Généré le:</strong> {data['timestamp']}</p>
        </div>
        
        <div class="content">
            <!-- Alertes -->
            {_generate_alerts(data)}
            
            <!-- Section Ressources Système -->
            <div class="section">
                <h2>💻 Ressources Système</h2>
                <div class="grid">
                    <!-- CPU -->
                    <div class="card">
                        <h3>Processeur</h3>
                        <div class="stat">
                            <span class="stat-label">Utilisation</span>
                            <span class="stat-value">{data['cpu']['percent']:.1f}%</span>
                        </div>
                        <div class="progress">
                            <div class="progress-bar {get_status_class(data['cpu']['percent'])}" 
                                 style="width: {data['cpu']['percent']}%">
                                {data['cpu']['percent']:.1f}%
                            </div>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Cœurs</span>
                            <span class="stat-value">{data['cpu']['count']}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Fréquence</span>
                            <span class="stat-value">{data['cpu']['freq']:.0f} MHz</span>
                        </div>
                    </div>
                    
                    <!-- Mémoire -->
                    <div class="card">
                        <h3>Mémoire RAM</h3>
                        <div class="stat">
                            <span class="stat-label">Utilisation</span>
                            <span class="stat-value">{data['memory']['percent']:.1f}%</span>
                        </div>
                        <div class="progress">
                            <div class="progress-bar {get_status_class(data['memory']['percent'])}" 
                                 style="width: {data['memory']['percent']}%">
                                {data['memory']['percent']:.1f}%
                            </div>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Total</span>
                            <span class="stat-value">{format_bytes(data['memory']['total'])}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Utilisée</span>
                            <span class="stat-value">{format_bytes(data['memory']['used'])}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Disponible</span>
                            <span class="stat-value">{format_bytes(data['memory']['available'])}</span>
                        </div>
                    </div>
                    
                    <!-- Disque -->
                    <div class="card">
                        <h3>Disque</h3>
                        <div class="stat">
                            <span class="stat-label">Utilisation</span>
                            <span class="stat-value">{data['disk']['percent']:.1f}%</span>
                        </div>
                        <div class="progress">
                            <div class="progress-bar {get_status_class(data['disk']['percent'])}" 
                                 style="width: {data['disk']['percent']}%">
                                {data['disk']['percent']:.1f}%
                            </div>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Total</span>
                            <span class="stat-value">{format_bytes(data['disk']['total'])}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Utilisé</span>
                            <span class="stat-value">{format_bytes(data['disk']['used'])}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Libre</span>
                            <span class="stat-value">{format_bytes(data['disk']['free'])}</span>
                        </div>
                    </div>
                    
                    <!-- Réseau -->
                    <div class="card">
                        <h3>Réseau</h3>
                        <div class="stat">
                            <span class="stat-label">Données envoyées</span>
                            <span class="stat-value">{format_bytes(data['network']['bytes_sent'])}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Données reçues</span>
                            <span class="stat-value">{format_bytes(data['network']['bytes_recv'])}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Paquets envoyés</span>
                            <span class="stat-value">{data['network']['packets_sent']:,}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Paquets reçus</span>
                            <span class="stat-value">{data['network']['packets_recv']:,}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Section Services -->
            <div class="section">
                <h2>🌐 État des Services</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Service</th>
                            <th>Statut</th>
                        </tr>
                    </thead>
                    <tbody>
                        {services_rows}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Pied de page -->
        <div class="footer">
            <p>📊 Rapport généré automatiquement par Network Monitor</p>
            <p>© 2025 - Niveau 4 : Génération de rapports</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Écrire le fichier HTML
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✅ Rapport généré avec succès !")
        print(f"📁 Fichier: {output_file}")
        print(f"🌐 Ouvrir avec: xdg-open {output_file}\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la génération du rapport: {e}\n")
        return False


def _generate_alerts(data):
    """Génère les alertes HTML si nécessaire"""
    alerts = []
    
    if data['cpu']['percent'] > 80:
        alerts.append(f"⚠️ CPU élevé: {data['cpu']['percent']:.1f}%")
    
    if data['memory']['percent'] > 85:
        alerts.append(f"⚠️ Mémoire élevée: {data['memory']['percent']:.1f}%")
    
    if data['disk']['percent'] > 90:
        alerts.append(f"⚠️ Disque presque plein: {data['disk']['percent']:.1f}%")
    
    if not alerts:
        return ""
    
    alert_class = "danger" if any(p > 90 for p in [data['cpu']['percent'], 
                                                     data['memory']['percent'], 
                                                     data['disk']['percent']]) else "alert"
    
    alerts_html = "<div class='{}'><strong>Alertes détectées:</strong><ul>".format(alert_class)
    for alert in alerts:
        alerts_html += f"<li>{alert}</li>"
    alerts_html += "</ul></div>"
    
    return alerts_html


# Programme principal
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Générer un rapport HTML des ressources système'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='rapport.html',
        help='Nom du fichier de sortie (défaut: rapport.html)'
    )
    
    args = parser.parse_args()
    
    # Vérifier que psutil est installé
    try:
        import psutil
    except ImportError:
        print("❌ Erreur: Le module 'psutil' n'est pas installé")
        print("\n📦 Installation:")
        print("   pip3 install psutil")
        exit(1)
    
    print("\n🔍 Collecte des informations système...")
    data = collect_system_info()
    
    print("📊 Génération du rapport HTML...")
    generate_html_report(data, args.output)