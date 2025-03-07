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

## Installation

### Installation automatique (Recommandée)

1. Téléchargez le script d'installation :
   ```bash
   wget -O install_auto_power_off.sh https://raw.githubusercontent.com/JayceeB1/klipper-auto-power-off/main/scripts/install_auto_power_off.sh
   ```

2. Rendez-le exécutable :
   ```bash
   chmod +x install_auto_power_off.sh
   ```

3. Exécutez le script :
   ```bash
   # Exécuter avec la langue par défaut (Anglais)
   ./install_auto_power_off.sh

   # Ou spécifier une langue
   ./install_auto_power_off.sh --fr  # Français
   ./install_auto_power_off.sh --en  # Anglais
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

4. Redémarrez Klipper :
   ```bash
   sudo systemctl restart klipper
   ```

## Désinstallation

Si vous avez besoin de désinstaller le module Auto Power Off, suivez ces étapes:

1. Supprimez les fichiers du module:
   ```bash
   # Supprimer le module Python principal
   rm ~/klipper/klippy/extras/auto_power_off.py
   
   # Supprimer le répertoire des traductions
   rm -rf ~/klipper/klippy/extras/auto_power_off_langs
   
   # Supprimer les fichiers de configuration UI (selon votre interface)
   rm ~/printer_data/config/fluidd/auto_power_off*.cfg
   rm ~/printer_data/config/mainsail/auto_power_off*.cfg
   
   # Supprimer le fichier de persistance de langue
   rm ~/printer_data/config/auto_power_off_language.conf
   ```

2. Modifiez votre fichier printer.cfg pour supprimer toute la section [auto_power_off] et les lignes d'inclusion associées.

   ```
   [auto_power_off]
   idle_timeout: 600
   temp_threshold: 40
   ...

   [include fluidd/auto_power_off.cfg]
   [include mainsail/auto_power_off.cfg]
   ```

3. Redémarrez Klipper:

   ```bash
   sudo systemctl restart klipper
   ```



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


## Utilisation

### Interface Fluidd

Une fois installé, vous verrez un panneau "Extinction Automatique" dans votre interface Fluidd qui vous permettra de :
- Activer/désactiver la fonctionnalité d'extinction automatique
- Voir le compte à rebours et les températures actuelles
- Démarrer/annuler manuellement le minuteur d'extinction
- Éteindre immédiatement l'imprimante (avec confirmation)

### Interface Mainsail

Pour Mainsail, vous aurez accès à :
- Un ensemble de commandes GCODE pour contrôler l'extinction automatique
- Des boutons GPIO configurables pour contrôler la fonction (si vous configurez les GPIO)

### Intégration dans le G-code de fin

Pour activer l'extinction automatique uniquement pour certaines impressions, ajoutez ceci au G-code de fin de votre trancheur :

```
AUTO_POWEROFF ON  ; Active l'extinction automatique
AUTO_POWEROFF START  ; Démarre le compte à rebours
```

### Commandes GCODE

Les commandes GCODE suivantes sont disponibles :

- `AUTO_POWEROFF ON` - Active globalement la fonction
- `AUTO_POWEROFF OFF` - Désactive globalement la fonction
- `AUTO_POWEROFF START` - Démarre manuellement le minuteur
- `AUTO_POWEROFF CANCEL` - Annule le minuteur en cours
- `AUTO_POWEROFF NOW` - Éteint immédiatement l'imprimante
- `AUTO_POWEROFF STATUS` - Affiche l'état détaillé
- `AUTO_POWEROFF LANGUAGE VALUE=en` - Définir la langue sur l'anglais
- `AUTO_POWEROFF LANGUAGE VALUE=fr` -  Définir la langue sur le français
- `AUTO_POWEROFF DIAGNOSTIC VALUE=1` - Activer le mode diagnostic pour le dépannage (0 pour désactiver)
- `AUTO_POWEROFF DRYRUN VALUE=1` - Activer le mode simulation qui simule l'extinction (0 pour désactiver)

## Intégration avec Moonraker (Avancé)

Auto Power Off peut fonctionner en tandem avec le module Power de Moonraker pour offrir un contrôle d'alimentation complet :

- **Auto Power Off** gère l'extinction basée sur la température et le délai d'inactivité après une impression
- **Moonraker Power** peut gérer l'allumage avant l'impression et prendre en charge différents types de dispositifs d'alimentation

Cette intégration vous permet de :
- Utiliser les broches GPIO du SBC ou différents types de prises intelligentes
- Allumer automatiquement l'imprimante lorsqu'une impression est lancée
- Redémarrer automatiquement Klipper après la mise sous tension
- Maintenir la protection contre l'extinction pendant l'impression

### Configuration

1. **Configurez le module Power dans `moonraker.conf`**:

   ```ini
   [power printer]
   type: gpio                     # Type de dispositif: gpio, tplink_smartplug, tasmota, etc.
   pin: gpio27                    # Pour GPIO uniquement: broche à utiliser
   # address: 192.168.1.123       # Pour les appareils réseau: adresse IP
   off_when_shutdown: True
   initial_state: off
   on_when_job_queued: True       # Allumer quand une impression est lancée
   locked_while_printing: True    # Empêche l'extinction pendant l'impression
   restart_klipper_when_powered: True
   restart_delay: 3
   ```

   > **Note importante**: Dans les versions récentes de Moonraker, l'option `off_when_job_complete` n'est plus disponible. Le module Auto Power Off prend en charge cette fonctionnalité, ce qui permet une extinction intelligente basée sur les températures et l'inactivité.

2. **Activez l'intégration dans `printer.cfg`**:

   ```ini
   [auto_power_off]
   idle_timeout: 600              # Temps d'inactivité en secondes
   temp_threshold: 40             # Seuil de température en °C
   power_device: printer          # Doit correspondre au nom dans [power printer]
   moonraker_integration: True    # Activer l'intégration Moonraker
   moonraker_url: http://localhost:7125  # URL de l'API Moonraker (optionnel)
   ```

### Comportement attendu

1. Quand une impression est mise en file d'attente, Moonraker allume l'imprimante.
2. Klipper redémarre automatiquement après la mise sous tension.
3. L'imprimante ne peut pas être éteinte pendant l'impression (verrouillée).
4. Quand l'impression est terminée, Auto Power Off prend le contrôle et surveille:
   - Le délai d'inactivité configuré
   - Les températures de l'extrudeur et du lit
5. Une fois les conditions remplies, Auto Power Off éteint l'imprimante.

### Types de dispositifs pris en charge

Cette intégration fonctionne avec tous les types de dispositifs supportés par Moonraker, notamment:
- Broches GPIO des Raspberry Pi et autres SBC
- Prises intelligentes TP-Link
- Dispositifs Tasmota, Shelly, HomeSeer
- Et plusieurs autres options...

Consultez la [documentation de Moonraker](https://moonraker.readthedocs.io/en/latest/configuration/#power) pour la liste complète des options.

## Dépannage

### Problèmes courants et solutions

#### Périphérique d'alimentation non trouvé

Si vous voyez une erreur comme "Périphérique d'alimentation 'psu_control' introuvable" :

1. Assurez-vous d'avoir défini une section `[power]` dans votre configuration Klipper
2. Vérifiez que le paramètre `power_device` dans `[auto_power_off]` correspond au nom dans votre section `[power]`
3. Vérifiez que le périphérique d'alimentation est correctement configuré et fonctionnel en consultant son état dans l'interface Fluidd/Mainsail (dans l'onglet Machine)

#### Problèmes de connectivité des périphériques réseau

Si vous utilisez un périphérique d'alimentation réseau (comme une prise intelligente) et rencontrez des problèmes de connectivité :

1. Vérifiez que vous pouvez ping le périphérique depuis votre hôte Klipper
2. Assurez-vous d'avoir défini `network_device: True` et fourni la bonne `device_address`
3. Vérifiez les paramètres de pare-feu qui pourraient bloquer la communication

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

### Périphériques compatibles

Le module a été testé avec les types de périphériques d'alimentation suivants :

| Type de périphérique | Compatibilité | Notes |
|-------------|---------------|-------|
| GPIO Raspberry Pi | Excellente | Contrôle direct via les broches GPIO |
| Prises intelligentes TP-Link | Bonne | Nécessite une connectivité réseau |
| Dispositifs Tasmota | Bonne | Nécessite une connectivité réseau |
| Dispositifs Shelly | Bonne | Nécessite une connectivité réseau |
| Prises intelligentes via MQTT | Bonne | Nécessite l'intégration Moonraker |
| Cartes relais USB | Bonne | Lorsque configurées comme périphériques GPIO |

## Utilisation avancée

### Configuration des périphériques réseau

Pour les périphériques d'alimentation basés sur le réseau (comme les prises intelligentes), une configuration supplémentaire est recommandée :

```ini
[auto_power_off]
network_device: True  # Indiquer qu'il s'agit d'un périphérique réseau
device_address: 192.168.1.123  # Adresse IP de votre prise intelligente
network_test_attempts: 5  # Augmenter les tentatives pour les réseaux peu fiables
network_test_interval: 2.0  # Attendre 2 secondes entre les tentatives de connexion
dry_run_mode: False  # Mettre à True initialement pour les tests
```

Cette configuration active les tests de connectivité avant de tenter d'éteindre, améliorant la fiabilité avec les périphériques d'alimentation basés sur le réseau.

## Support linguistique

Ce module est disponible en :
- Français (ce document)
- Anglais (voir [README.md](README.md))

### Ajouter de nouvelles langues

Le module prend désormais en charge les traductions via des fichiers de langue externes. Pour ajouter une nouvelle langue :

1. Créez un nouveau fichier JSON dans le répertoire `auto_power_off_langs` nommé d'après le code de langue (par exemple, `de.json` pour l'allemand)
2. Copiez la structure d'un fichier de langue existant et traduisez tous les messages
3. Ajoutez le nouveau code de langue à la liste de validation dans la méthode `_configure_language`
4. La nouvelle langue sera disponible en utilisant `language: de` dans la configuration ou via une commande GCODE


## Licence

Ce projet est sous licence GPL-3.0 - consultez le fichier [LICENSE](LICENSE) pour plus de détails.

## Remerciements

- Inspiré par le plugin PSU Control d'OctoPrint
- Merci aux équipes de développement de Klipper, Fluidd et Mainsail