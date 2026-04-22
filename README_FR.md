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
- Disponible en anglais et français
- Compatible avec tous les types de dispositifs d'alimentation Moonraker (GPIO, TP-Link Smartplug, Tasmota, Shelly, etc.)
- Focalisé sur l'interface web : les menus LCD ont été supprimés pour plus de simplicité

## Documentation

Pour une meilleure compréhension du fonctionnement interne d'Auto Power Off, consultez les [diagrammes de séquence](DIAGRAMS.md) qui illustrent les différents processus d'extinction et les interactions entre les composants.

## Prérequis

- Klipper avec un [contrôle GPIO d'alimentation](https://www.klipper3d.org/Config_Reference.html#output_pin) correctement configuré
- Fluidd ou Mainsail (pour l'intégration de l'interface utilisateur)
- Une imprimante 3D avec une configuration de contrôle d'alimentation

## Soutenir le développement

Si vous trouvez ce module utile, vous pouvez m'offrir un café pour soutenir son développement !

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/jayceeB1)

Votre soutien est grandement apprécié et aide à maintenir et améliorer ce projet !

## Commandes disponibles

Le module fournit les commandes GCODE suivantes :

Klipper rejette les paramètres sans `=`, utilisez donc soit la forme
`OPTION=`, soit les alias dédiés (les macros fournies dans `ui/fluidd/`
et `ui/mainsail/` les appellent automatiquement) :

- `AUTO_POWEROFF OPTION=ON` - Active globalement la fonction
- `AUTO_POWEROFF OPTION=OFF` - Désactive globalement la fonction
- `AUTO_POWEROFF OPTION=START` - Démarre manuellement le minuteur
- `AUTO_POWEROFF OPTION=CANCEL` - Annule le minuteur en cours
- `AUTO_POWEROFF OPTION=NOW` - Éteint immédiatement l'imprimante
- `AUTO_POWEROFF OPTION=STATUS` - Affiche l'état détaillé
- `AUTO_POWEROFF_DIAGNOSTIC VALUE=1` - Active le mode diagnostic (0 pour désactiver)
- `AUTO_POWEROFF_DRYRUN VALUE=1` - Active le mode simulation (0 pour désactiver)
- `AUTO_POWEROFF_RESET` - Force la réinitialisation de l'état interne du module
- `AUTO_POWEROFF_VERSION` - Affiche la version du module actuellement chargée

## Caractéristiques principales

Le module offre plusieurs fonctionnalités avancées :

- **Gestion intelligente de l'alimentation** : Éteint uniquement lorsque les températures sont sécuritaires et que l'imprimante est inactive
- **Intégration multi-interface** : Intégration complète avec les interfaces Fluidd et Mainsail
- **Support des périphériques réseau** : Fonctionne avec divers périphériques d'alimentation connectés au réseau
- **Diagnostics et dépannage** : Mode diagnostic pour des journaux détaillés et le traçage des opérations
- **Intégration Moonraker** : Exploite l'API de contrôle d'alimentation de Moonraker pour une meilleure compatibilité
- **Implémentation à typage sûr** : Gestion robuste des erreurs avec une hiérarchie d'exceptions structurée
- **Support multilingue** : Support complet des langues anglaise et française
- **Mises à jour transparentes** : S'intègre au gestionnaire de mise à jour de Moonraker pour des mises à jour faciles

Pour une liste détaillée des changements entre les versions, veuillez consulter le fichier [CHANGELOG.md](CHANGELOG.md).

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

La configuration suivante (ou similaire) sera ajoutée à votre `moonraker.conf` :

```ini
[update_manager auto_power_off]
type: git_repo
path: ~/auto_power_off    # Ce chemin peut varier selon votre installation
origin: https://github.com/JayceeB1/Klipper-Auto-Power-Off.git
primary_branch: main
install_script: scripts/install.sh
```

Note : Le script d'installation détectera ou vous demandera le chemin approprié pour votre système. Le chemin peut varier en fonction de votre compte utilisateur et de vos préférences (par exemple, `/home/utilisateur/auto_power_off`). Le script s'assurera que le chemin correct est utilisé dans votre configuration.

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

## Exemples de périphériques d'alimentation

### Prise Tasmota

Pour contrôler votre imprimante via un périphérique Tasmota, ajoutez une section `[power]` dans `moonraker.conf` :

```ini
# moonraker.conf
[power printer_plug]
type: tasmota
address: 192.168.1.xxx      # Adresse IP de votre périphérique Tasmota
# password: votre_mot_de_passe   # Décommentez si vous avez défini un mot de passe Tasmota
# output_id: 1              # Décommentez pour les Tasmota multi-relais
```

Puis référencez ce nom dans `printer.cfg` :

```ini
[auto_power_off]
power_device: printer_plug  # Doit correspondre au nom dans [power printer_plug]
idle_timeout: 600
temp_threshold: 40
auto_poweroff_enabled: True
moonraker_integration: True
moonraker_url: http://localhost:7125
```

> **Note :** La section `[power]` est un bloc de **configuration Moonraker** (à placer dans `moonraker.conf`), pas un bloc Klipper. Auto Power Off appelle l'API Moonraker pour couper l'alimentation lorsque les conditions sont remplies.

### Tasmota + Raspberry Pi — extinction séquentielle

Une configuration courante consiste à brancher le RPi et l'imprimante sur la **même** prise Tasmota. Couper l'alimentation via le module couperait le courant du RPi immédiatement (arrêt brutal).

**Approche recommandée — prises séparées :**

Branchez le RPi sur une source d'alimentation permanente (ou une seconde prise Tasmota toujours active) et l'imprimante sur la prise contrôlée par Auto Power Off. Le RPi reste actif ; seule l'imprimante perd l'alimentation.

```ini
# moonraker.conf — contrôle uniquement la prise de l'imprimante
[power printer_plug]
type: tasmota
address: 192.168.1.xxx
```

**Alternative — même prise, arrêt propre du RPi d'abord :**

Si vous devez brancher les deux sur la même prise, demandez à Moonraker d'éteindre proprement le RPi avant que la prise soit coupée :

```gcode
# Dans printer.cfg — à ajouter dans END_PRINT ou à déclencher manuellement
[gcode_macro SHUTDOWN_HOST_THEN_PRINTER]
gcode:
    AUTO_POWEROFF OPTION=START   # démarre le compte à rebours refroidissement/inactivité
    # Une fois le compte à rebours écoulé, Moonraker coupera la prise via l'API.
    # Pour arrêter proprement le RPi avant cela, ajoutez cette ligne :
    {action_call_remote_method("shutdown_machine")}
```

> `action_call_remote_method("shutdown_machine")` demande à Moonraker d'effectuer un arrêt système propre. Appelez-le avant que la prise soit coupée pour laisser le temps au RPi de s'éteindre. Il n'y a pas de délai par périphérique intégré dans Auto Power Off ; pour un délai fixe de 2 minutes avant la coupure de la prise, définissez `idle_timeout: 120` dans `[auto_power_off]` et appelez `AUTO_POWEROFF OPTION=START` à la fin de votre impression.

### Dépannage — "Repo has diverged from remote" dans le gestionnaire de mises à jour

Les versions antérieures à 2.1.0 créaient un commit git local dans `~/auto_power_off` lors de l'installation. Ce commit n'existant pas dans l'historique GitHub, le gestionnaire de mises à jour de Moonraker signale "diverged from remote" et refuse de mettre à jour.

**Correction unique :**
```bash
cd ~/auto_power_off
git fetch origin
git reset --hard origin/main
```

Ensuite, relancez le script d'installation une fois pour restaurer les fichiers locaux :
```bash
wget -O install.sh https://raw.githubusercontent.com/JayceeB1/klipper-auto-power-off/main/scripts/install.sh
chmod +x install.sh
./install.sh
```

La version 2.1.0+ ne crée jamais de commits locaux ; le problème ne se reproduira plus.

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
- Création de sauvegardes de tous les fichiers de configuration modifiés

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

## Utilisation avancée

### Extinction optionnelle (ne pas éteindre après chaque impression)

Par défaut, `AUTO_POWEROFF OPTION=START` dans `END_PRINT` entraîne l'extinction après **chaque** impression. Si vous lancez des impressions en série, vous préférerez probablement décider *avant* une impression si la machine doit s'éteindre après.

Le modèle ci-dessous (contribution de la communauté — @thaala) utilise une simple variable booléenne :

```gcode
# Dans printer.cfg

[gcode_macro POW_WANTED]
description: Drapeau : éteindre après la prochaine impression
variable_powwanted: 0
gcode:
  SET_GCODE_VARIABLE MACRO=POW_WANTED VARIABLE=powwanted VALUE=1

[gcode_macro POW_UNWANTED]
description: Effacer le drapeau et annuler le compte à rebours
gcode:
  SET_GCODE_VARIABLE MACRO=POW_WANTED VARIABLE=powwanted VALUE=0
  AUTO_POWEROFF OPTION=CANCEL

[gcode_macro POWEROFF_IF_WANTED]
description: Démarre le timer uniquement si POW_WANTED a été activé
gcode:
  {% if printer["gcode_macro POW_WANTED"].powwanted > 0 %}
    AUTO_POWEROFF OPTION=START
  {% endif %}
```

À intégrer dans vos macros d'impression :

```gcode
[gcode_macro PRINT_START]
gcode:
  POW_UNWANTED          # toujours effacer le drapeau en début d'impression
  # ... reste de votre routine de démarrage ...

[gcode_macro END_PRINT]
gcode:
  # ... votre routine de fin existante ...
  M104 S0
  M140 S0
  POWEROFF_IF_WANTED    # démarre le timer seulement si POW_WANTED a été appelé

[gcode_macro CANCEL_PRINT]
gcode:
  # ... votre routine d'annulation existante ...
  POW_UNWANTED          # annule l'extinction en cas d'annulation manuelle
```

Utilisation : avant de lancer la dernière impression de la session, exécutez `POW_WANTED` depuis la console Mainsail/Fluidd ou un bouton macro. Les autres impressions se terminent normalement sans extinction.

## Dépannage

### Problèmes courants et solutions

#### Le minuteur ne démarre pas à la fin d'une impression

Le module écoute l'événement Klipper `print_stats:complete`. Cet événement
n'est émis que lorsque `[print_stats]` (ou `[virtual_sdcard]`, qui le
déclare implicitement) marque proprement l'impression comme `complete`.
Si votre gcode de fin ou votre macro `END_PRINT` ne produit pas cette
transition, le minuteur ne démarrera pas automatiquement.

La solution la plus fiable est d'appeler `AUTO_POWEROFF OPTION=START`
explicitement à la fin de votre macro `END_PRINT` (et éventuellement de
`CANCEL_PRINT`) :

```gcode
[gcode_macro END_PRINT]
gcode:
    # ... votre routine de fin existante ...
    M104 S0
    M140 S0
    AUTO_POWEROFF OPTION=START
```

Vérifiez que le démarrage manuel fonctionne avec
`AUTO_POWEROFF OPTION=START` (ou la macro `AUTO_POWEROFF_START` /
`POWEROFF_START` selon votre UI). Si oui mais que le déclenchement
automatique reste muet, c'est que l'événement n'arrive pas au module :
le workaround `END_PRINT` est alors la bonne voie.

#### Réinitialisation de l'état du module

Si votre périphérique d'alimentation a été rallumé manuellement après une extinction automatique et que vous rencontrez des problèmes avec les commandes d'extinction suivantes, vous pouvez utiliser la commande `AUTO_POWEROFF_RESET` pour forcer une réinitialisation de l'état interne du module :

```gcode
AUTO_POWEROFF_RESET
```

Ceci est particulièrement utile lorsque :
- Le module ne détecte pas que l'imprimante a été rallumée manuellement
- Les commandes comme `AUTO_POWEROFF NOW` ne fonctionnent plus après un rallumage manuel
- Le système est dans un état incohérent après une interruption réseau ou de communication

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

1. Activez le mode diagnostic : `AUTO_POWEROFF_DIAGNOSTIC VALUE=1`
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