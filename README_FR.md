# Klipper Auto Power Off

Un module Klipper qui éteint automatiquement votre imprimante 3D après une impression terminée, une fois qu'elle a refroidi et est restée inactive pendant une période spécifiée.

![Panneau Auto Power Off](images/auto_power_off_panel.png)

## Soutenir le développement

Si vous trouvez ce module utile, vous pouvez m'offrir un café pour soutenir son développement !

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/jayceeb1)

Votre soutien est grandement apprécié et aide à maintenir et améliorer ce projet !


## Fonctionnalités

- Extinction automatique de votre imprimante après les impressions terminées
- Délai d'inactivité configurable (par défaut : 10 minutes)
- Seuil de température configurable (par défaut : 40°C)
- Intégration avec Fluidd et Mainsail pour un contrôle facile via l'interface utilisateur
- Surveillance de l'état des températures de la buse et du lit
- Contrôle manuel avec des commandes GCODE
- Fonctionne avec n'importe quel périphérique d'alimentation contrôlé par GPIO

## Prérequis

- Klipper avec un [contrôle GPIO d'alimentation](https://www.klipper3d.org/Config_Reference.html#output_pin) correctement configuré
- Fluidd ou Mainsail (pour l'intégration de l'interface utilisateur)
- Une imprimante 3D avec une configuration de contrôle d'alimentation

## Installation

### Installation automatique (Recommandée)

1. Téléchargez le script d'installation :
   ```bash
   # Version française
   wget -O install_auto_power_off_fr.sh https://raw.githubusercontent.com/JayceeB1/klipper-auto-power-off/main/scripts/install_auto_power_off_fr.sh
   
   # Version anglaise
   wget -O install_auto_power_off.sh https://raw.githubusercontent.com/JayceeB1/klipper-auto-power-off/main/scripts/install_auto_power_off.sh
   ```

2. Rendez-le exécutable :
   ```bash
   chmod +x install_auto_power_off_fr.sh
   # ou
   chmod +x install_auto_power_off.sh
   ```

3. Exécutez le script :
   ```bash
   ./install_auto_power_off_fr.sh
   # ou
   ./install_auto_power_off.sh
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

## Configuration

Les paramètres suivants peuvent être configurés dans la section `[auto_power_off]` :

| Paramètre | Défaut | Description |
|-----------|---------|-------------|
| `idle_timeout` | 600 | Temps en secondes à attendre avant l'extinction (après une impression terminée) |
| `temp_threshold` | 40 | Température en °C en dessous de laquelle il est sûr d'éteindre |
| `power_device` | psu_control | Nom de votre périphérique d'alimentation (doit correspondre à la section [power]) |
| `auto_poweroff_enabled` | False | Active l'extinction automatique par défaut au démarrage |

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
- Un menu dans l'interface pour accéder aux fonctions d'extinction
- Des boutons configurables pour contrôler la fonction (si vous configurez les GPIO)

### Commandes GCODE

Les commandes GCODE suivantes sont disponibles :

- `AUTO_POWEROFF ON` - Active globalement la fonction
- `AUTO_POWEROFF OFF` - Désactive globalement la fonction
- `AUTO_POWEROFF START` - Démarre manuellement le minuteur
- `AUTO_POWEROFF CANCEL` - Annule le minuteur en cours
- `AUTO_POWEROFF NOW` - Éteint immédiatement l'imprimante
- `AUTO_POWEROFF STATUS` - Affiche l'état détaillé

### Intégration dans le G-code de fin

Pour activer l'extinction automatique uniquement pour certaines impressions, ajoutez ceci au G-code de fin de votre trancheur :

```
AUTO_POWEROFF ON  ; Active l'extinction automatique
AUTO_POWEROFF START  ; Démarre le compte à rebours
```

## Dépannage

Si vous rencontrez des problèmes :

1. Vérifiez les logs de Klipper :
   ```bash
   tail -f /tmp/klippy.log
   ```

2. Vérifiez que votre contrôle d'alimentation fonctionne :
   ```
   QUERY_POWER psu_control  # Remplacez par le nom de votre périphérique d'alimentation
   ```

3. Vérifiez l'état du module d'extinction automatique :
   ```
   AUTO_POWEROFF STATUS
   ```

4. Assurez-vous que votre configuration correspond à la configuration d'alimentation de votre imprimante.

## Support linguistique

Ce module est disponible en :
- Français (ce document)
- Anglais (voir [README.md](README.md))

## Licence

Ce projet est sous licence GPL-3.0 - consultez le fichier [LICENSE](LICENSE) pour plus de détails.

## Remerciements

- Inspiré par le plugin PSU Control d'OctoPrint
- Merci aux équipes de développement de Klipper, Fluidd et Mainsail
