# Klipper Auto Power Off

Un module Klipper qui éteint automatiquement votre imprimante 3D après une impression terminée, une fois qu'elle a refroidi et est restée inactive pendant une période spécifiée.

![Panneau Auto Power Off](images/auto_power_off_panel.png)

## Fonctionnalités

- Extinction automatique de votre imprimante après les impressions terminées
- Délai d'inactivité configurable (par défaut : 10 minutes)
- Seuil de température configurable (par défaut : 40°C)
- Intégration avec Fluidd et Mainsail pour un contrôle facile via l'interface utilisateur
- Surveillance de l'état des températures de la buse et du lit
- Contrôle manuel avec des commandes GCODE
- Fonctionne avec n'importe quel périphérique d'alimentation contrôlé par GPIO
- Compatible avec tous les types de dispositifs d'alimentation Moonraker (GPIO, TP-Link Smartplug, Tasmota, Shelly, etc.)
- Focalisé sur l'interface web : les menus LCD ont été supprimés pour plus de simplicité
- **Nouveau** - Gestion d'erreurs améliorée et capacités de diagnostic
- **Nouveau** - Support amélioré des périphériques réseau avec test de connexion robuste
- **Nouveau** - Implémentation à typage sûr avec exceptions structurées
- **Nouveau** - Correction des mises à jour automatiques via le gestionnaire de mise à jour Moonraker

## Prérequis

- Klipper avec un [contrôle GPIO d'alimentation](https://www.klipper3d.org/Config_Reference.html#output_pin) correctement configuré
- Fluidd ou Mainsail (pour l'intégration de l'interface utilisateur)
- Une imprimante 3D avec une configuration de contrôle d'alimentation

## Soutenir le développement

Si vous trouvez ce module utile, vous pouvez m'offrir un café pour soutenir son développement !

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/jayceeB1)

Votre soutien est grandement apprécié et aide à maintenir et améliorer ce projet !

## Mise à jour importante

À partir de la dernière version, Auto Power Off fonctionne principalement via l'API de contrôle d'alimentation de Moonraker. Le module est maintenant configuré par défaut pour utiliser l'intégration Moonraker, offrant une meilleure compatibilité avec différents types de périphériques d'alimentation.

### Changements clés
- L'intégration Moonraker est maintenant activée par défaut
- La configuration nécessite que votre périphérique soit correctement configuré dans la configuration de Moonraker
- Fiabilité et compatibilité améliorées avec les périphériques d'alimentation réseau
- Les entrées du menu LCD ont été supprimées pour se concentrer sur l'intégration de l'interface web
- **Nouveau** - Code à typage sûr et structuré avec gestion d'erreurs améliorée
- **Nouveau** - Meilleurs outils de diagnostic pour le dépannage
- **Nouveau** - Intégration améliorée du système de mise à jour avec meilleure gestion des erreurs

## Installation

### Installation automatique (Recommandée)

1. Téléchargez le script d'installation :
   ```bash
   wget -O install.sh https://raw.githubusercontent.com/JayceeB1/klipper-auto-power-off/main/scripts/install.sh
   ```

2. Rendez-le exécutable :
   ```bash
   chmod +x install.sh
   ```

3. Exécutez le script :
   ```bash
   # Exécuter avec la langue par défaut (Anglais)
   ./install.sh

   # Ou spécifier une langue
   ./install.sh --fr  # Français
   ./install.sh --en  # Anglais
   ```

4. Suivez les instructions à l'écran.

### Installation manuelle

1. Copiez le script `auto_power_off.py` dans votre répertoire d'extras Klipper :
   ```bash
   cp src/auto_power_off.py ~/klipper/klippy/extras/
   ```

2. Copiez le fichier du panneau Fluidd ou Mainsail :
   
   **Pour Fluidd :**
   ```bash
   mkdir -p ~/printer_data/config/fluidd/
   # Version française
   cp ui/fluidd/auto_power_off_fr.cfg ~/printer_data/config/fluidd/auto_power_off.cfg
   # Version anglaise
   cp ui/fluidd/auto_power_off.cfg ~/printer_data/config/fluidd/
   ```
   
   **Pour Mainsail :**
   ```bash
   mkdir -p ~/printer_data/config/mainsail/
   # Version française
   cp ui/mainsail/auto_power_off_fr.cfg ~/printer_data/config/mainsail/
   cp ui/mainsail/auto_power_off_panel_fr.cfg ~/printer_data/config/mainsail/
   # Version anglaise
   cp ui/mainsail/auto_power_off.cfg ~/printer_data/config/mainsail/
   cp ui/mainsail/auto_power_off_panel.cfg ~/printer_data/config/mainsail/
   ```

3. Ajoutez ce qui suit à votre fichier `printer.cfg` :
   ```
   [auto_power_off]
   idle_timeout: 600     # Temps d'inactivité en secondes avant extinction (10 minutes)
   temp_threshold: 40    # Seuil de température en °C (imprimante considérée comme refroidie)
   power_device: psu_control  # Nom de votre périphérique d'alimentation (doit correspondre à la section [power])
   auto_poweroff_enabled: True  # Active l'extinction automatique par défaut au démarrage

   # Pour Fluidd :
   [include fluidd/auto_power_off.cfg]
   
   # Pour Mainsail :
   [include mainsail/auto_power_off.cfg]
   ```

4. Ajoutez ce qui suit à votre fichier `moonraker.conf` :
   ```
   [update_manager auto_power_off]
   type: git_repo
   path: ~/auto_power_off
   origin: https://github.com/JayceeB1/Klipper-Auto-Power-Off.git
   primary_branch: main
   install_script: scripts/install.sh
   ```

5. Redémarrez Klipper :
   ```bash
   sudo systemctl restart klipper
   ```

## Mise à jour automatique avec Moonraker

Auto Power Off prend désormais en charge les mises à jour automatiques via le gestionnaire de mise à jour de Moonraker. Cela vous permet de mettre à jour le module directement depuis l'interface Fluidd ou Mainsail, comme les autres composants de votre firmware d'imprimante 3D.

### Configuration automatique pendant l'installation

Lors de l'exécution du script d'installation, vous serez invité à ajouter la configuration du gestionnaire de mise à jour à votre fichier `moonraker.conf`. Cette configuration :

1. Crée un dépôt Git local pour les fichiers du module
2. Ajoute la configuration du gestionnaire de mise à jour à `moonraker.conf`
3. Configure le dépôt pour suivre les mises à jour du projet principal

### Résolution des problèmes de gestionnaire de mise à jour

Si vous rencontrez des erreurs comme "Failed to detect repo url" ou "Invalid path" avec le gestionnaire de mise à jour, suivez ces étapes :

1. Exécutez à nouveau le script d'installation :
   ```bash
   wget -O install.sh https://raw.githubusercontent.com/JayceeB1/klipper-auto-power-off/main/scripts/install.sh
   chmod +x install.sh
   ./install.sh
   ```

2. Choisissez "o" lorsqu'on vous demande d'ajouter la configuration du gestionnaire de mise à jour
3. Le script amélioré nettoiera les anciennes configurations et configurera correctement le dépôt git

### Configuration manuelle pour les installations existantes

Si vous disposez d'une installation existante et souhaitez ajouter la prise en charge du gestionnaire de mise à jour :

1. Exécutez à nouveau le script d'installation :
   ```bash
   wget -O install.sh https://raw.githubusercontent.com/JayceeB1/klipper-auto-power-off/main/scripts/install.sh
   chmod +x install.sh
   ./install.sh
   ```

2. Choisissez "o" lorsqu'on vous demande d'ajouter la configuration du gestionnaire de mise à jour
3. Vous pouvez spécifier un chemin personnalisé pour le dépôt local si nécessaire

### Configuration du gestionnaire de mise à jour

La configuration suivante sera ajoutée à votre `moonraker.conf` :

```ini
[update_manager auto_power_off]
type: git_repo
path: ~/auto_power_off
origin: https://github.com/JayceeB1/Klipper-Auto-Power-Off.git
primary_branch: main
install_script: scripts/install.sh
```

### Mise à jour via Fluidd/Mainsail

Une fois configuré, vous pouvez mettre à jour Auto Power Off directement depuis l'interface Fluidd ou Mainsail :

1. Accédez à l'onglet "Machine" ou "Système"
2. Recherchez "Auto Power Off" dans la section des mises à jour
3. Cliquez sur "Mettre à jour" lorsqu'une nouvelle version est disponible

Les mises à jour seront appliquées automatiquement et Klipper sera redémarré pour charger le module mis à jour.


## Configuration

Les paramètres suivants peuvent être configurés dans la section `[auto_power_off]` :

| Paramètre | Défaut | Description |
|-----------|---------|-------------|
| `idle_timeout` | 600 | Temps en secondes à attendre avant l'extinction (après une impression terminée) |
| `temp_threshold` | 40 | Température en °C en dessous de laquelle il est sûr d'éteindre. Par défaut, surveille à la fois l'extrudeur et le lit chauffant, et utilise la température la plus élevée pour comparaison |
| `monitor_hotend` | True | Surveiller la température de l'extrudeur pour l'extinction |
| `monitor_bed` | True | Surveiller la température du lit chauffant pour l'extinction |
| `monitor_chamber` | False | Surveiller la température de la chambre pour l'extinction (si disponible) |
| `power_device` | psu_control | Nom de votre périphérique d'alimentation (doit correspondre à la section [power]) |
| `auto_poweroff_enabled` | False | Active l'extinction automatique par défaut au démarrage |
| `language` | auto | Langue pour les messages : 'en' pour l'anglais, 'fr' pour le français, 'auto' pour auto-détection |
| `moonraker_integration` | True | Active l'intégration avec le contrôle d'alimentation de Moonraker |
| `moonraker_url` | http://localhost:7125 | URL pour l'API Moonraker |
| `diagnostic_mode` | False | Active la journalisation détaillée pour résoudre les problèmes d'extinction |
| `power_off_retries` | 3 | Nombre de tentatives de nouvelle connexion lors de l'utilisation de l'API Moonraker |
| `power_off_retry_delay` | 2 | Délai en secondes entre les tentatives |
| `dry_run_mode` | False | Simule l'extinction sans réellement éteindre l'imprimante (pour les tests) |
| `network_device` | False | Indique si le périphérique d'alimentation est sur le réseau |
| `device_address` | None | Adresse IP ou nom d'hôte du périphérique réseau |
| `network_test_attempts` | 3 | Nombre de tentatives pour tester la connectivité du périphérique réseau |
| `network_test_interval` | 1.0 | Intervalle en secondes entre les tentatives de test de connectivité réseau |

## Nouvelles fonctionnalités dans la v2.0.3

### Fonctionnalité de mise à jour automatique améliorée

La dernière version apporte des améliorations significatives au système de mise à jour :

- Correction des problèmes avec l'intégration du gestionnaire de mise à jour
- Meilleure gestion des erreurs pour la configuration du dépôt
- Initialisation améliorée du dépôt Git
- Suivi amélioré des fichiers pour éviter les erreurs "fichiers non suivis"
- Possibilité de spécifier des chemins de dépôt personnalisés
- Nettoyage automatique des configurations anciennes ou incorrectes

### Gestion d'erreurs améliorée

Le module propose désormais une gestion d'erreurs robuste avec une hiérarchie d'exceptions structurée :

- Meilleure communication des erreurs pour les problèmes de connectivité réseau
- Distinction claire entre les différents types d'erreurs (périphérique, API Moonraker, réseau)
- Journalisation améliorée des diagnostics pour le dépannage

### Implémentation à typage sûr

- Annotations de type complètes pour une meilleure maintenabilité du code
- Énumérations pour les états et méthodes pour une meilleure fiabilité
- API propre pour l'intégration avec l'écosystème Klipper

### Support avancé des périphériques réseau

- Tests complets des périphériques réseau avant les tentatives d'extinction
- Mécanisme de nouvelle tentative configurable pour les environnements réseau peu fiables
- Amélioration du fallback vers des méthodes directes lorsque les périphériques réseau sont injoignables

### Diagnostics améliorés

- Mode de diagnostic amélioré avec journalisation détaillée
- Meilleure communication des capacités des périphériques
- Informations d'état claires à travers l'interface utilisateur

### Améliorations du support multilingue

- Détection et persistance de la langue plus robustes
- Meilleure gestion du chargement des traductions
- Messages d'erreur plus clairs en français et en anglais

## Désinstallation

Pour désinstaller complètement le module Auto Power Off, un script de désinstallation est maintenant disponible :

### Désinstallation automatique

1. Téléchargez le script de désinstallation :
   ```bash
   wget -O uninstall.sh https://raw.githubusercontent.com/JayceeB1/Klipper-Auto-Power-Off/main/scripts/uninstall.sh
   ```

2. Rendez-le exécutable :
   ```bash
   chmod +x uninstall.sh
   ```

3. Exécutez le script :
   ```bash
   # Exécuter avec la langue par défaut (Anglais)
   ./uninstall.sh

   # Ou spécifier une langue
   ./uninstall.sh --fr  # Français
   ./uninstall.sh --en  # Anglais
   ```

4. Suivez les instructions à l'écran.

Le script effectuera automatiquement les actions suivantes :
- Suppression du module Python et des fichiers de traduction
- Suppression des fichiers de configuration pour Fluidd et Mainsail
- Nettoyage des modifications dans printer.cfg
- Suppression de la configuration du gestionnaire de mise à jour dans moonraker.conf
- Suppression du dépôt Git local créé pour les mises à jour

### Options avancées

- `--force` : Exécute la désinstallation sans demander de confirmation
- `--fr` ou `--en` : Spécifie la langue des messages (français ou anglais)

### Désinstallation manuelle

Si vous préférez désinstaller manuellement, voici les étapes à suivre :

1. Supprimez le module Python :
   ```bash
   rm ~/klipper/klippy/extras/auto_power_off.py
   rm -r ~/klipper/klippy/extras/auto_power_off_langs
   ```

2. Supprimez les fichiers de configuration :
   ```bash
   # Pour Fluidd
   rm ~/printer_data/config/fluidd/auto_power_off*.cfg
   
   # Pour Mainsail
   rm ~/printer_data/config/mainsail/auto_power_off*.cfg
   rm ~/printer_data/config/mainsail/auto_power_off_panel*.cfg
   ```

3. Modifiez votre fichier `printer.cfg` pour supprimer les sections concernant Auto Power Off.

4. Modifiez votre fichier `moonraker.conf` pour supprimer la section `[update_manager auto_power_off]`.

5. Supprimez le dépôt Git local (généralement `~/auto_power_off`).

6. Redémarrez Klipper et Moonraker :
   ```bash
   sudo systemctl restart klipper
   sudo systemctl restart moonraker
   ```

## Dépannage

### Problèmes courants et solutions

#### Problèmes de gestionnaire de mise à jour

Si vous voyez des erreurs comme "Failed to detect repo url" ou "Invalid path" dans votre gestionnaire de mise à jour :

1. Téléchargez et exécutez le script d'installation amélioré
2. Choisissez "o" lorsqu'on vous demande de mettre à jour la configuration Moonraker
3. Le script configurera correctement le dépôt git et corrigera les problèmes de configuration

#### Implémentation basée sur CURL

Le module Auto Power Off utilise la commande CURL pour les communications avec l'API Moonraker plutôt que des bibliothèques Python comme requests ou urllib. Cela améliore la compatibilité et la fiabilité, évitant les problèmes de dépendances externes.

Si vous rencontrez des problèmes de communication avec Moonraker, vérifiez que la commande CURL est disponible sur votre système :
```bash
which curl
```

Si CURL n'est pas installé, vous pouvez l'installer avec :
```bash
sudo apt-get install curl
```

#### Test avec le mode simulation

Pour tester en toute sécurité la fonctionnalité d'extinction automatique sans réellement éteindre votre imprimante :

1. Activez le mode simulation dans votre configuration : `dry_run_mode: True`
2. Ou utilisez la commande GCODE : `AUTO_POWEROFF DRYRUN VALUE=1`
3. Cela simulera l'extinction et journalisera toutes les actions sans réellement éteindre l'imprimante

### Diagnostics détaillés des capacités du périphérique

Pour comprendre quelles capacités votre périphérique d'alimentation possède :

1. Activez le mode diagnostic : `AUTO_POWEROFF DIAGNOSTIC VALUE=1`
2. Vérifiez les logs avec : `tail -f /tmp/klippy.log | grep -i auto_power_off`
3. Les logs montreront quelles méthodes sont disponibles pour votre périphérique
4. Cela aide à résoudre pourquoi l'extinction pourrait ne pas fonctionner

## Pour les développeurs

### Structure du code

Le code refactorisé utilise désormais une architecture plus maintenable :

- Hiérarchie d'exceptions structurée pour une meilleure gestion des erreurs
- Annotations de type pour un meilleur support IDE et sécurité du code
- Énumérations pour les états et méthodes pour une meilleure structure du code
- Séparation claire des préoccupations dans le code

### Contribution

Avant de soumettre des pull requests, assurez-vous de :

1. Suivre le style de codage à typage sûr
2. Maintenir la compatibilité ascendante
3. Mettre à jour la documentation pour toute nouvelle fonctionnalité
4. Tester les modifications avec diverses configurations

## Licence

Ce projet est sous licence GPL-3.0 - consultez le fichier [LICENSE](LICENSE) pour plus de détails.

## Remerciements

- Inspiré par le plugin PSU Control d'OctoPrint
- Merci aux équipes de développement de Klipper, Fluidd et Mainsail