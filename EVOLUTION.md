# 📈 Mon guide d'évolution du projet

Dans ce document, je décris comment je vais faire évoluer mon projet pas à pas.

## 🎯 Niveaux de progression

### NIVEAU 1 : Les bases

**Ce que j'ai :**
- Un script Python (~50 lignes)
- Un script PowerShell équivalent
- La possibilité de vérifier si un service est actif

**Fichiers :**
```bash
python/check_service.py
powershell/check_service.ps1
```

**Ce que j'ai appris :**
- Exécuter des commandes système
- Gérer les paramètres en ligne de commande
- Afficher des résultats formatés
- Gérer les erreurs basiques

**Complexité estimée :** baseline

---

### NIVEAU 2 : Vérifier plusieurs services

**Objectif :** Vérifier plusieurs services d'un coup.

**Nouveau fichier :**
```python
# python/check_multiple.py
# usage: python3 check_multiple.py nginx ssh mysql
```

**Ce que je vais apprendre :**
- Gérer plusieurs paramètres
- Utiliser des boucles et des listes
- Afficher des tableaux

**Complexité estimée :** +30 lignes

---

### NIVEAU 3 : Monitoring basique

**Objectif :** Surveiller CPU, RAM, disque.

**Nouveau fichier :**
```python
# python/monitor.py
# usage: python3 monitor.py
```

**Nouvelle dépendance :**
```bash
pip3 install psutil
```

**Ce que je vais apprendre :**
- Lire les informations système
- Faire une boucle pour le monitoring temps réel
- Rafraîchir l'affichage

**Complexité estimée :** +50 lignes

---

### NIVEAU 4 : Générer des rapports

**Objectif :** Créer un rapport HTML avec les infos collectées.

**Nouveau fichier :**
```python
# python/report.py
# usage: python3 report.py
```

**Ce que je vais apprendre :**
- Générer du HTML
- Sauvegarder des fichiers
- Formater les données

**Complexité estimée :** +60 lignes

---

### NIVEAU 5 : Système d'alertes

**Objectif :** Envoyer une alerte si CPU > 80%.

**Fichier à modifier :**
```python
# python/monitor.py (ajout d'alertes)
```

**Ce que je vais apprendre :**
- Gérer les conditions et les seuils
- Créer des logs système
- Envoyer des notifications

**Complexité estimée :** +40 lignes

---

### NIVEAU 6 : Configuration automatique

**Objectif :** Installer et configurer automatiquement des services.

**Nouveau fichier :**
```bash
# python/configure.py
# usage: sudo python3 configure.py nginx install
```

**Ce que je vais apprendre :**
- Exécuter des commandes avec sudo
- Modifier des fichiers de configuration
- Gérer les permissions

**Complexité estimée :** +100 lignes

---

## 🛠️ Idées d'améliorations (par niveau)

### Niveau 1 (actuel)
- Ajouter la vérification du port en plus du service
- Afficher depuis combien de temps le service est actif
- Vérifier si le service est activé au démarrage

### Niveau 2
- Exporter les résultats en JSON
- Trier les services par statut
- Afficher en couleur (vert/rouge)

### Niveau 3
- Historique des mesures
- Graphiques en mode texte (barres ASCII)
- Prédiction de tendances (simple)

### Niveau 4
- Rapports PDF en plus du HTML
- Graphiques avec matplotlib
- Comparaison avec des rapports précédents

### Niveau 5
- Alertes par email
- Alertes Slack / Discord
- Log des alertes dans un fichier

### Niveau 6
- Interface web pour la configuration
- Sauvegarde de la config avant modification
- Templates de configuration par environnement
