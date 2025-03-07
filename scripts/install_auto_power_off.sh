#!/bin/bash
# Unified installation script for Klipper Auto Power Off module
# Usage: bash install_auto_power_off.sh

# Set default language to English
DEFAULT_LANG="en"
LANG_CHOICE="$DEFAULT_LANG"

# Colors for messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Repository information
REPO_URL="https://raw.githubusercontent.com/JayceeB1/klipper-auto-power-off/main"

# Function to display formatted messages in the selected language
print_status() {
    if [ "$LANG_CHOICE" = "fr" ]; then
        echo -e "${BLUE}[INFO]${NC} $1"
    else
        echo -e "${BLUE}[INFO]${NC} $1"
    fi
}

print_success() {
    if [ "$LANG_CHOICE" = "fr" ]; then
        echo -e "${GREEN}[OK]${NC} $1"
    else
        echo -e "${GREEN}[OK]${NC} $1"
    fi
}

print_warning() {
    if [ "$LANG_CHOICE" = "fr" ]; then
        echo -e "${YELLOW}[ATTENTION]${NC} $1"
    else
        echo -e "${YELLOW}[WARNING]${NC} $1"
    fi
}

print_error() {
    if [ "$LANG_CHOICE" = "fr" ]; then
        echo -e "${RED}[ERREUR]${NC} $1"
    else
        echo -e "${RED}[ERROR]${NC} $1"
    fi
}

# Montre un exemple de configuration Moonraker
show_moonraker_config_example() {
    if [ "$LANG_CHOICE" = "fr" ]; then
        cat << 'EOL'
# Exemple de configuration Moonraker pour Auto Power Off
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

# Note: L'option 'off_when_job_complete' n'est plus disponible dans les versions récentes de Moonraker.
# Le module Auto Power Off s'occupe de l'extinction après une impression complète.
EOL
    else
        cat << 'EOL'
# Example Moonraker configuration for Auto Power Off
[power printer]
type: gpio                     # Device type: gpio, tplink_smartplug, tasmota, etc.
pin: gpio27                    # For GPIO only: pin to use
# address: 192.168.1.123       # For network devices: IP address
off_when_shutdown: True
initial_state: off
on_when_job_queued: True       # Power on when a print is queued
locked_while_printing: True    # Prevents power off during printing
restart_klipper_when_powered: True
restart_delay: 3

# Note: The 'off_when_job_complete' option is no longer available in recent Moonraker versions.
# The Auto Power Off module handles shutdown after a completed print.
EOL
    fi
}

# Check script arguments for language preference
for arg in "$@"; do
    case $arg in
        --fr|--french|-fr|-f)
            LANG_CHOICE="fr"
            shift
            ;;
        --en|--english|-en|-e)
            LANG_CHOICE="en"
            shift
            ;;
    esac
done

# Display language options if no argument was provided
if [ "$LANG_CHOICE" = "$DEFAULT_LANG" ] && [ $# -eq 0 ]; then
    echo "Select language / Choisir la langue:"
    echo "1) English"
    echo "2) Français"
    read -p "Choice/Choix [1-2, default=1]: " lang_num
    
    if [ "$lang_num" = "2" ]; then
        LANG_CHOICE="fr"
    fi
fi

# Set language-specific messages
if [ "$LANG_CHOICE" = "fr" ]; then
    MSG_ROOT_ERROR="Ne pas exécuter ce script en tant que root (sudo). Utilisez votre utilisateur normal."
    MSG_KLIPPER_ERROR="Le répertoire Klipper n'a pas été trouvé dans votre répertoire home."
    MSG_KLIPPER_INSTALL="Assurez-vous que Klipper est installé avant d'exécuter ce script."
    MSG_CHECK_DIRS="Vérification des répertoires nécessaires..."
    MSG_EXTRAS_CHECKED="Répertoire des extras vérifié."
    MSG_CONFIG_NOT_FOUND="Impossible de trouver automatiquement le répertoire de configuration."
    MSG_ENTER_PATH="Veuillez entrer le chemin complet vers votre répertoire de configuration Klipper:"
    MSG_DIR_NOT_EXISTS="Le répertoire n'existe pas. Installation annulée."
    MSG_CONFIG_FOUND="Répertoire de configuration trouvé:"
    MSG_UI_CHOICE="Quelle interface utilisez-vous? (1 = Fluidd, 2 = Mainsail, 3 = Les deux)"
    MSG_SETUP_FLUIDD="Configuration pour Fluidd (par défaut)..."
    MSG_SETUP_MAINSAIL="Configuration pour Mainsail..."
    MSG_SETUP_BOTH="Configuration pour Fluidd et Mainsail..."
    MSG_UI_DIRS_CREATED="Répertoires de l'interface utilisateur créés."
    MSG_DL_MODULE="Téléchargement du module Python auto_power_off.py..."
    MSG_MODULE_DOWNLOADED="Module Python téléchargé."
    MSG_CREATING_LANG_DIRS="Création des répertoires de langue..."
    MSG_LANG_DIRS_CREATED="Répertoires de langue créés."
    MSG_DL_EN_TRANS="Téléchargement des traductions anglaises..."
    MSG_EN_TRANS_DOWNLOADED="Traductions anglaises téléchargées."
    MSG_DL_FR_TRANS="Téléchargement des traductions françaises..."
    MSG_FR_TRANS_DOWNLOADED="Traductions françaises téléchargées."
    MSG_CREATE_FLUIDD="Création du panneau Fluidd..."
    MSG_FLUIDD_CREATED="Panneau Fluidd créé."
    MSG_CREATE_MAINSAIL="Création du panneau Mainsail..."
    MSG_MAINSAIL_CREATED="Panneau Mainsail créé."
    MSG_MODIFY_CFG="Modification du fichier printer.cfg..."
    MSG_CFG_NOT_FOUND="Fichier printer.cfg non trouvé à l'emplacement:"
    MSG_MANUAL_ADD="Vous devrez ajouter manuellement la configuration à votre fichier printer.cfg."
    MSG_AUTO_ADD_CFG="Voulez-vous ajouter automatiquement la configuration au fichier printer.cfg? [o/N]"
    MSG_SECTION_EXISTS="La section [auto_power_off] existe déjà dans printer.cfg."
    MSG_CHECK_UPDATE="Veuillez vérifier et mettre à jour la configuration manuellement."
    MSG_CFG_ADDED="Configuration ajoutée au fichier printer.cfg."
    MSG_CFG_NOT_ADDED="Configuration non ajoutée. Vous devrez l'ajouter manuellement."
    MSG_RESTART_KLIPPER="Voulez-vous redémarrer Klipper maintenant pour appliquer les changements? [o/N]"
    MSG_RESTARTING="Redémarrage de Klipper..."
    MSG_RESTARTED="Klipper redémarré."
    MSG_WAIT_RESTART="Patientez quelques secondes pour que Klipper redémarre complètement..."
    MSG_LOADED_SUCCESS="Le module Auto Power Off a été chargé avec succès!"
    MSG_VERIFY_FAILED="Vérification du chargement du module impossible. Veuillez vérifier les logs de Klipper."
    MSG_NOT_RESTARTED="Klipper n'a pas été redémarré. Veuillez le redémarrer manuellement pour appliquer les changements."
    MSG_RESTART_CMD="Commande pour redémarrer: sudo systemctl restart klipper"
    MSG_INSTALL_COMPLETE="Installation terminée !"
    MSG_HOW_TO_USE="=== Comment utiliser ===="
    MSG_PANEL_AVAILABLE="1. Le panneau Auto Power Off sera disponible dans l'interface Fluidd/Mainsail"
    MSG_AUTO_ACTIVATE="2. Le module s'activera automatiquement à la fin de chaque impression si configuré ainsi"
    MSG_AVAILABLE_CMDS="3. Commandes GCODE disponibles:"
    MSG_CMD_ON="   - AUTO_POWEROFF ON    - Active globalement la fonction"
    MSG_CMD_OFF="   - AUTO_POWEROFF OFF   - Désactive globalement la fonction"
    MSG_CMD_START="   - AUTO_POWEROFF START - Démarre manuellement le minuteur"
    MSG_CMD_CANCEL="   - AUTO_POWEROFF CANCEL - Annule le minuteur en cours"
    MSG_CMD_NOW="   - AUTO_POWEROFF NOW   - Éteint immédiatement l'imprimante"
    MSG_CMD_STATUS="   - AUTO_POWEROFF STATUS - Affiche l'état détaillé"
    MSG_CMD_DIAGNOSTIC="   - AUTO_POWEROFF DIAGNOSTIC VALUE=1 - Active le mode diagnostic (0 pour désactiver)"
    MSG_CHECK_LOGS="Si vous rencontrez des problèmes, vérifiez les logs de Klipper avec: tail -f /tmp/klippy.log"
    MSG_YES_CONFIRM="o"
else
    # English messages
    MSG_ROOT_ERROR="Do not run this script as root (sudo). Use your normal user."
    MSG_KLIPPER_ERROR="Klipper directory not found in your home directory."
    MSG_KLIPPER_INSTALL="Make sure Klipper is installed before running this script."
    MSG_CHECK_DIRS="Checking required directories..."
    MSG_EXTRAS_CHECKED="Extras directory checked."
    MSG_CONFIG_NOT_FOUND="Could not automatically find the configuration directory."
    MSG_ENTER_PATH="Please enter the full path to your Klipper configuration directory:"
    MSG_DIR_NOT_EXISTS="Directory does not exist. Installation canceled."
    MSG_CONFIG_FOUND="Configuration directory found:"
    MSG_UI_CHOICE="Which interface are you using? (1 = Fluidd, 2 = Mainsail, 3 = Both)"
    MSG_SETUP_FLUIDD="Setting up for Fluidd (default)..."
    MSG_SETUP_MAINSAIL="Setting up for Mainsail..."
    MSG_SETUP_BOTH="Setting up for both Fluidd and Mainsail..."
    MSG_UI_DIRS_CREATED="UI directories created."
    MSG_DL_MODULE="Downloading Python module auto_power_off.py..."
    MSG_MODULE_DOWNLOADED="Python module downloaded."
    MSG_CREATING_LANG_DIRS="Creating language directories..."
    MSG_LANG_DIRS_CREATED="Language directories created."
    MSG_DL_EN_TRANS="Downloading English translations..."
    MSG_EN_TRANS_DOWNLOADED="English translations downloaded."
    MSG_DL_FR_TRANS="Downloading French translations..."
    MSG_FR_TRANS_DOWNLOADED="French translations downloaded."
    MSG_CREATE_FLUIDD="Creating Fluidd panel..."
    MSG_FLUIDD_CREATED="Fluidd panel created."
    MSG_CREATE_MAINSAIL="Creating Mainsail panel..."
    MSG_MAINSAIL_CREATED="Mainsail panel created."
    MSG_MODIFY_CFG="Modifying printer.cfg file..."
    MSG_CFG_NOT_FOUND="printer.cfg file not found at location:"
    MSG_MANUAL_ADD="You will need to manually add the configuration to your printer.cfg file."
    MSG_AUTO_ADD_CFG="Do you want to automatically add the configuration to the printer.cfg file? [y/N]"
    MSG_SECTION_EXISTS="The [auto_power_off] section already exists in printer.cfg."
    MSG_CHECK_UPDATE="Please check and update the configuration manually."
    MSG_CFG_ADDED="Configuration added to printer.cfg file."
    MSG_CFG_NOT_ADDED="Configuration not added. You will need to add it manually."
    MSG_RESTART_KLIPPER="Do you want to restart Klipper now to apply the changes? [y/N]"
    MSG_RESTARTING="Restarting Klipper..."
    MSG_RESTARTED="Klipper restarted."
    MSG_WAIT_RESTART="Wait a few seconds for Klipper to fully restart..."
    MSG_LOADED_SUCCESS="The Auto Power Off module was loaded successfully!"
    MSG_VERIFY_FAILED="Could not verify module loading. Please check Klipper logs."
    MSG_NOT_RESTARTED="Klipper was not restarted. Please restart it manually to apply the changes."
    MSG_RESTART_CMD="Command to restart: sudo systemctl restart klipper"
    MSG_INSTALL_COMPLETE="Installation complete!"
    MSG_HOW_TO_USE="=== How to Use ===="
    MSG_PANEL_AVAILABLE="1. The Auto Power Off panel will be available in the Fluidd/Mainsail interface"
    MSG_AUTO_ACTIVATE="2. The module will automatically activate at the end of each print if configured so"
    MSG_AVAILABLE_CMDS="3. Available GCODE commands:"
    MSG_CMD_ON="   - AUTO_POWEROFF ON    - Globally enable the function"
    MSG_CMD_OFF="   - AUTO_POWEROFF OFF   - Globally disable the function"
    MSG_CMD_START="   - AUTO_POWEROFF START - Manually start the timer"
    MSG_CMD_CANCEL="   - AUTO_POWEROFF CANCEL - Cancel the current timer"
    MSG_CMD_NOW="   - AUTO_POWEROFF NOW   - Immediately power off the printer"
    MSG_CMD_STATUS="   - AUTO_POWEROFF STATUS - Display detailed status"
    MSG_CMD_DIAGNOSTIC="   - AUTO_POWEROFF DIAGNOSTIC VALUE=1 - Enable diagnostic mode (0 to disable)"
    MSG_CHECK_LOGS="If you encounter any issues, check the Klipper logs with: tail -f /tmp/klippy.log"
    MSG_YES_CONFIRM="y"
fi

# Check if script is run as root
if [ "$EUID" -eq 0 ]; then
    print_error "$MSG_ROOT_ERROR"
    exit 1
fi

# Check if Klipper is installed
if [ ! -d ~/klipper ]; then
    print_error "$MSG_KLIPPER_ERROR"
    print_error "$MSG_KLIPPER_INSTALL"
    exit 1
fi

# Create Klipper extras directory if needed
print_status "$MSG_CHECK_DIRS"
mkdir -p ~/klipper/klippy/extras
mkdir -p ~/klipper/klippy/extras/auto_power_off_langs
print_success "$MSG_EXTRAS_CHECKED"

# Auto-detect configuration path
PRINTER_CONFIG_DIR=""
POSSIBLE_PATHS=(
    "$HOME/printer_data/config" 
    "$HOME/klipper_config"
)

for path in "${POSSIBLE_PATHS[@]}"; do
    if [ -d "$path" ]; then
        PRINTER_CONFIG_DIR="$path"
        break
    fi
done

if [ -z "$PRINTER_CONFIG_DIR" ]; then
    print_error "$MSG_CONFIG_NOT_FOUND"
    echo "$MSG_ENTER_PATH"
    read -r PRINTER_CONFIG_DIR
    
    if [ ! -d "$PRINTER_CONFIG_DIR" ]; then
        print_error "$MSG_DIR_NOT_EXISTS"
        exit 1
    fi
fi

print_success "$MSG_CONFIG_FOUND $PRINTER_CONFIG_DIR"

# Detect the interface used (Fluidd or Mainsail)
UI_TYPE="fluidd"
echo "$MSG_UI_CHOICE"
read -r UI_CHOICE

case $UI_CHOICE in
    2)
        UI_TYPE="mainsail"
        print_status "$MSG_SETUP_MAINSAIL"
        ;;
    3)
        UI_TYPE="both"
        print_status "$MSG_SETUP_BOTH"
        ;;
    *)
        print_status "$MSG_SETUP_FLUIDD"
        ;;
esac

# Create directories for the UI
mkdir -p $PRINTER_CONFIG_DIR/fluidd
if [ "$UI_TYPE" = "mainsail" ] || [ "$UI_TYPE" = "both" ]; then
    mkdir -p $PRINTER_CONFIG_DIR/mainsail
fi
print_success "$MSG_UI_DIRS_CREATED"

# Download the Python module
print_status "$MSG_DL_MODULE"
wget -q -O ~/klipper/klippy/extras/auto_power_off.py "$REPO_URL/src/auto_power_off.py"
print_success "$MSG_MODULE_DOWNLOADED"

# Download translation files
print_status "$MSG_DL_EN_TRANS"
wget -q -O ~/klipper/klippy/extras/auto_power_off_langs/en.json "$REPO_URL/src/auto_power_off_langs/en.json"
print_success "$MSG_EN_TRANS_DOWNLOADED"

print_status "$MSG_DL_FR_TRANS"
wget -q -O ~/klipper/klippy/extras/auto_power_off_langs/fr.json "$REPO_URL/src/auto_power_off_langs/fr.json"
print_success "$MSG_FR_TRANS_DOWNLOADED"

# Create Fluidd configuration file
if [ "$UI_TYPE" = "fluidd" ] || [ "$UI_TYPE" = "both" ]; then
    print_status "$MSG_CREATE_FLUIDD"
    wget -q -O $PRINTER_CONFIG_DIR/fluidd/auto_power_off.cfg "$REPO_URL/ui/fluidd/auto_power_off.cfg"
    print_success "$MSG_FLUIDD_CREATED"
fi

# Create Mainsail configuration file
if [ "$UI_TYPE" = "mainsail" ] || [ "$UI_TYPE" = "both" ]; then
    print_status "$MSG_CREATE_MAINSAIL"
    wget -q -O $PRINTER_CONFIG_DIR/mainsail/auto_power_off.cfg "$REPO_URL/ui/mainsail/auto_power_off.cfg"
    wget -q -O $PRINTER_CONFIG_DIR/mainsail/auto_power_off_panel.cfg "$REPO_URL/ui/mainsail/auto_power_off_panel.cfg"
    print_success "$MSG_MAINSAIL_CREATED"
fi

# Ask user if they want to add the configuration to printer.cfg
print_status "$MSG_MODIFY_CFG"
CONFIG_FILE="$PRINTER_CONFIG_DIR/printer.cfg"

if [ ! -f "$CONFIG_FILE" ]; then
    print_error "$MSG_CFG_NOT_FOUND $CONFIG_FILE"
    print_warning "$MSG_MANUAL_ADD"
else
    echo "$MSG_AUTO_ADD_CFG"
    read -r ADD_CONFIG
    
    if [[ "$ADD_CONFIG" =~ ^[$MSG_YES_CONFIRM][eEyY]?[sS]?$ ]]; then
    # Check if [auto_power_off] section already exists
    if grep -q "\[auto_power_off\]" "$CONFIG_FILE"; then
        print_warning "$MSG_SECTION_EXISTS"
        print_warning "$MSG_CHECK_UPDATE"
    else
        # Add configuration to file
        # Vérifier si SAVE_CONFIG existe dans le fichier
        if grep -q "SAVE_CONFIG" "$CONFIG_FILE"; then
            # Préparer le texte de configuration à insérer
            CONFIG_TEXT="\n#\n# Auto Power Off Configuration\n#\n"
            
            # Ajouter les includes appropriés en fonction de l'interface
            if [ "$UI_TYPE" = "fluidd" ]; then
                CONFIG_TEXT="${CONFIG_TEXT}[include fluidd/auto_power_off.cfg]  # Include Fluidd panel\n\n"
            elif [ "$UI_TYPE" = "mainsail" ]; then
                CONFIG_TEXT="${CONFIG_TEXT}[include mainsail/auto_power_off.cfg]  # Include Mainsail panel\n\n"
            else
                CONFIG_TEXT="${CONFIG_TEXT}[include fluidd/auto_power_off.cfg]  # Include Fluidd panel\n"
                CONFIG_TEXT="${CONFIG_TEXT}[include mainsail/auto_power_off.cfg]  # Include Mainsail panel\n\n"
            fi
            
            # Ajouter la section auto_power_off
            CONFIG_TEXT="${CONFIG_TEXT}[auto_power_off]\nidle_timeout: 600     # Idle time in seconds before power off (10 minutes)\ntemp_threshold: 40    # Temperature threshold in °C (printer considered cool)\npower_device: psu_control  # Name of your power device (must match the [power] section)\nauto_poweroff_enabled: True  # Enable auto power off by default at startup\nlanguage: auto        # Language setting: 'en', 'fr', or 'auto' for auto-detection\ndiagnostic_mode: False # Enable detailed logging for troubleshooting power off issues"
            
            # Insérer avant la section SAVE_CONFIG
            awk -v config="$CONFIG_TEXT" '/SAVE_CONFIG/{ print config; print } !/SAVE_CONFIG/{ print }' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
        else
            # Si pas de SAVE_CONFIG, ajouter à la fin
            cat >> "$CONFIG_FILE" << 'EOL'

#
# Auto Power Off Configuration
#
EOL

            # Add the appropriate include based on the interface
            if [ "$UI_TYPE" = "fluidd" ]; then
                echo -e "[include fluidd/auto_power_off.cfg]  # Include Fluidd panel\n" >> "$CONFIG_FILE"
            elif [ "$UI_TYPE" = "mainsail" ]; then
                echo -e "[include mainsail/auto_power_off.cfg]  # Include Mainsail panel\n" >> "$CONFIG_FILE"
            else
                echo -e "[include fluidd/auto_power_off.cfg]  # Include Fluidd panel" >> "$CONFIG_FILE"
                echo -e "[include mainsail/auto_power_off.cfg]  # Include Mainsail panel\n" >> "$CONFIG_FILE"
            fi

            cat >> "$CONFIG_FILE" << 'EOL'
[auto_power_off]
idle_timeout: 600     # Idle time in seconds before power off (10 minutes)
temp_threshold: 40    # Temperature threshold in °C (printer considered cool)
power_device: psu_control  # Name of your power device (must match the [power] section)
auto_poweroff_enabled: True  # Enable auto power off by default at startup
moonraker_integration: True  # Enable Moonraker integration
moonraker_url: http://localhost:7125  # Moonraker API URL (usually default)
language: auto        # Language setting: 'en', 'fr', or 'auto' for auto-detection
diagnostic_mode: False # Enable detailed logging for troubleshooting power off issues
EOL
        fi
        
        print_success "$MSG_CFG_ADDED"
    fi
else
    print_warning "$MSG_CFG_NOT_ADDED"

        # Ajout d'information sur la configuration Moonraker
        if [ "$LANG_CHOICE" = "fr" ]; then
            echo "Voulez-vous voir un exemple de configuration Moonraker pour l'intégration avec Auto Power Off? [o/N]"
        else
            echo "Would you like to see an example Moonraker configuration for integration with Auto Power Off? [y/N]"
        fi
        read -r SHOW_MOONRAKER_CONFIG

        if [[ "$SHOW_MOONRAKER_CONFIG" =~ ^[$MSG_YES_CONFIRM][eEyY]?[sS]?$ ]]; then
            echo ""
            if [ "$LANG_CHOICE" = "fr" ]; then
                echo "=== Configuration Moonraker recommandée ==="
                echo "Ajoutez cette section à votre fichier moonraker.conf:"
                echo ""
            else
                echo "=== Recommended Moonraker Configuration ==="
                echo "Add this section to your moonraker.conf file:"
                echo ""
            fi
            
            show_moonraker_config_example
            
            echo ""
            if [ "$LANG_CHOICE" = "fr" ]; then
                echo "IMPORTANT: N'utilisez pas l'option 'off_when_job_complete', elle est obsolète."
            else
                echo "IMPORTANT: Do not use the 'off_when_job_complete' option, it is deprecated."
            fi
            echo ""            
        fi

    fi
fi

# Ask user if they want to restart Klipper
echo "$MSG_RESTART_KLIPPER"
read -r RESTART_KLIPPER

if [[ "$RESTART_KLIPPER" =~ ^[$MSG_YES_CONFIRM][eEyY]?[sS]?$ ]]; then
    print_status "$MSG_RESTARTING"
    sudo systemctl restart klipper
    print_success "$MSG_RESTARTED"
    
    echo "$MSG_WAIT_RESTART"
    sleep 5
    
    # Check if the module was loaded correctly
    # Tenter de trouver le fichier de log Klipper
    KLIPPY_LOG="/tmp/klippy.log"
    if [ ! -f "$KLIPPY_LOG" ]; then
        for possible_log in /var/log/klipper/klippy.log /home/*/printer_data/logs/klippy.log /home/*/klipper_logs/klippy.log; do
            if [ -f "$possible_log" ]; then
                KLIPPY_LOG="$possible_log"
                break
            fi
        done
    fi

    if [ -f "$KLIPPY_LOG" ] && (grep -q "Auto Power Off: Module initialized" "$KLIPPY_LOG" || grep -q "Auto Power Off: Module initialisé" "$KLIPPY_LOG"); then
        print_success "$MSG_LOADED_SUCCESS"
    else
        print_warning "$MSG_VERIFY_FAILED"
    fi
else
    print_warning "$MSG_NOT_RESTARTED"
    echo "$MSG_RESTART_CMD"
fi

echo ""
print_success "$MSG_INSTALL_COMPLETE"
echo ""
echo -e "${GREEN}$MSG_HOW_TO_USE${NC}"
echo "$MSG_PANEL_AVAILABLE"
echo "$MSG_AUTO_ACTIVATE"
echo "$MSG_AVAILABLE_CMDS"
echo "$MSG_CMD_ON"
echo "$MSG_CMD_OFF"
echo "$MSG_CMD_START"
# Note on Moonraker integration.
if [ "$LANG_CHOICE" = "fr" ]; then
    echo -e "\n${YELLOW}Note sur l'intégration Moonraker:${NC} L'option 'off_when_job_complete' est obsolète dans les versions récentes de Moonraker."
    echo "Le module Auto Power Off gère l'extinction intelligente après l'impression en fonction des températures et de l'inactivité."
else
    echo -e "\n${YELLOW}Note on Moonraker integration:${NC} The 'off_when_job_complete' option is deprecated in recent Moonraker versions."
    echo "The Auto Power Off module handles intelligent shutdown after printing based on temperatures and idle timeout."
fi
echo "$MSG_CMD_CANCEL"
echo "$MSG_CMD_NOW"
echo "$MSG_CMD_STATUS"
echo "$MSG_CMD_DIAGNOSTIC"
echo ""
echo "$MSG_CHECK_LOGS"
echo ""