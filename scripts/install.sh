#!/bin/bash
# Unified installation/update script for Klipper Auto Power Off module
# This script handles both installation and updates
# Usage: bash install.sh [--en|--fr]

# Set default language to English
DEFAULT_LANG="en"
LANG_CHOICE="$DEFAULT_LANG"

# Function to validate installation mode
validate_installation_mode() {
    # Explicitly reset UPDATE_MODE
    if [ -z "$UPDATE_MODE" ]; then
        UPDATE_MODE=false
    fi

    # Multilingual messages
    local msg_checking_install_mode
    local msg_module_detected
    local msg_lang_dir_detected
    local msg_config_detected
    local msg_final_mode

    if [ "$LANG_CHOICE" = "fr" ]; then
        msg_checking_install_mode="Validation du mode d'installation"
        msg_module_detected="Module précédemment installé détecté"
        msg_lang_dir_detected="Répertoire de langues précédemment installé détecté"
        msg_config_detected="Fichiers de configuration précédents détectés"
        msg_final_mode="Mode d'installation final :"
    else
        msg_checking_install_mode="Validating installation mode"
        msg_module_detected="Previously installed module detected"
        msg_lang_dir_detected="Previous language directory detected"
        msg_config_detected="Previous configuration files detected"
        msg_final_mode="Final installation mode:"
    fi

    # Paths to check — MODULE_PATH is already resolved at the top of the script
    local module_path="${MODULE_PATH:-${HOME}/klipper/klippy/extras/auto_power_off.py}"
    local langs_path="${module_path%/auto_power_off.py}/auto_power_off_langs"

    # Multilingual diagnostic logs
    print_status "$msg_checking_install_mode"
    print_status "Paths checked:"
    print_status "- Module: $module_path"
    print_status "- Languages: $langs_path"

    # Detailed check of previous state
    if [ -f "$module_path" ]; then
        print_status "$msg_module_detected"
        UPDATE_MODE=true
    elif [ -d "$langs_path" ]; then
        print_status "$msg_lang_dir_detected"
        UPDATE_MODE=true
    fi

    # Checking configuration files — PRINTER_CONFIG_DIR may not be set yet;
    # search common locations as a fallback.
    local cfg_search_dirs="${PRINTER_CONFIG_DIR} ${HOME}/printer_data/config ${HOME}/klipper_config"
    local found_cfg=false
    for _d in $cfg_search_dirs; do
        if [ -n "$_d" ] && ([ -f "$_d/fluidd/auto_power_off.cfg" ] || \
                             [ -f "$_d/mainsail/auto_power_off.cfg" ]); then
            found_cfg=true; break
        fi
    done
    if [ "$found_cfg" = true ]; then
        print_status "$msg_config_detected"
        UPDATE_MODE=true
    fi

    # Command line argument can force mode
    for arg in "$@"; do
        if [ "$arg" = "--update" ]; then
            UPDATE_MODE=true
            break
        fi
    done

    # Final mode log
    print_status "$msg_final_mode ${UPDATE_MODE}"
}

# Determine script directory and version
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -z "$MODULE_PATH" ]; then
    MODULE_PATH="${HOME}/klipper/klippy/extras/auto_power_off.py"
fi

# Try to get version from module file if it exists
if [ -f "$MODULE_PATH" ]; then
    VERSION=$(grep -o "__version__ = \"[0-9.]*\"" "$MODULE_PATH" | cut -d'"' -f2)
else
    VERSION="2.1.1" # Default version if not found!
fi

# Colors for messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions to display messages
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

# Repository information
REPO_URL="https://raw.githubusercontent.com/JayceeB1/Klipper-Auto-Power-Off/main"
REPO_GIT="https://github.com/JayceeB1/Klipper-Auto-Power-Off.git"

# Adding functions to check and repair the Git repository

# Function to check and repair an existing Git repository
repair_git_repo() {
    local repo_dir="$1"
    
    if [ -d "$repo_dir/.git" ]; then
        cd "$repo_dir" || return 1
        
        # Check if the repository is in good condition
        if ! git status &>/dev/null; then
            print_warning "Dépôt Git corrompu, tentative de réparation..."
            
            # Create a backup of the repository
            local backup_dir="${repo_dir}_backup_$(date +%Y%m%d%H%M%S)"
            mkdir -p "$backup_dir"
            cp -r "$repo_dir"/* "$backup_dir"/ 2>/dev/null
            
            # Completely reset the repository
            rm -rf "$repo_dir"
            mkdir -p "$repo_dir"
            git clone "${REPO_GIT}" "$repo_dir"
            
            # Restore locally modified files
            if [ -d "$backup_dir" ]; then
                cp -n "$backup_dir"/*.py "$repo_dir"/ 2>/dev/null
                cp -n "$backup_dir"/*.md "$repo_dir"/ 2>/dev/null
                cp -n "$backup_dir"/*.cfg "$repo_dir"/ 2>/dev/null
            fi
            
            print_status "Dépôt Git réparé et réinitialisé"
            return 0
        fi
        
        # Check if the remote URL is correct (case-sensitive)
        local current_url=$(git config --get remote.origin.url)
        if [ "$current_url" != "${REPO_GIT}" ]; then
            print_warning "URL du dépôt incorrect : $current_url"
            print_status "Correction de l'URL vers ${REPO_GIT}"
            git remote set-url origin "${REPO_GIT}"
        fi
        
        return 0
    fi
    
    return 1
}

# Function to check the installed version
verify_version() {
    local module_path="$1"
    if [ -f "$module_path" ]; then
        local detected_version=$(grep -o "__version__ = \"[0-9.]*\"" "$module_path" | cut -d'"' -f2)
        if [ -n "$detected_version" ]; then
            print_status "Version détectée: $detected_version"
            VERSION="$detected_version"
        else
            print_warning "Version non détectée dans $module_path, utilisation de la version par défaut"
        fi
    fi
}

# Function to restart Moonraker
restart_moonraker() {
    if [ -t 0 ]; then
        if [ "$LANG_CHOICE" = "fr" ]; then
            read -p "Voulez-vous redémarrer Moonraker maintenant pour appliquer les changements? [o/N] " RESTART_MOONRAKER
        else
            read -p "Do you want to restart Moonraker now to apply the changes? [y/N] " RESTART_MOONRAKER
        fi
        
        if [[ "$RESTART_MOONRAKER" =~ ^[$MSG_YES_CONFIRM][eEyY]?[sS]?$ ]]; then
            print_status "$MSG_MOONRAKER_RESTARTING"
            sudo systemctl restart moonraker
            
            echo "$MSG_WAIT_MOONRAKER"
            sleep 5
            
            # Check if the restart was successful
            if sudo systemctl is-active --quiet moonraker; then
                print_success "$MSG_MOONRAKER_RESTARTED"
            else
                print_warning "$MSG_MOONRAKER_RESTART_FAILED"
                echo "$MSG_MOONRAKER_RESTART_CMD"
            fi
        else
            if [ "$LANG_CHOICE" = "fr" ]; then
                print_warning "Moonraker n'a pas été redémarré. Veuillez le redémarrer manuellement pour appliquer les changements."
            else
                print_warning "Moonraker was not restarted. Please restart it manually to apply the changes."
            fi
            echo "$MSG_MOONRAKER_RESTART_CMD"
        fi
    else
        # In non-interactive mode, restart automatically
        print_status "$MSG_MOONRAKER_RESTARTING"
        sudo systemctl restart moonraker
        print_success "$MSG_MOONRAKER_RESTARTED"
    fi
}

validate_installation_mode "$@"

# Function to automatically detect main paths
detect_paths() {
    # Detect Klipper directory
    if [ -z "$KLIPPER_PATH" ]; then
        for p in ~/klipper /home/*/klipper; do
            if [ -d "$p" ]; then
                KLIPPER_PATH="$p"
                break
            fi
        done
    fi
    
    # Automatically detect configuration directory
    if [ -z "$PRINTER_CONFIG_DIR" ]; then
        for p in ~/printer_data/config ~/klipper_config /home/*/printer_data/config /home/*/klipper_config; do
            if [ -d "$p" ]; then
                PRINTER_CONFIG_DIR="$p"
                break
            fi
        done
    fi
    
    # Detect path to moonraker.conf
    if [ -z "$MOONRAKER_CONF" ]; then
        for p in "$PRINTER_CONFIG_DIR/moonraker.conf" /home/*/printer_data/config/moonraker.conf /home/*/klipper_config/moonraker.conf; do
            if [ -f "$p" ]; then
                MOONRAKER_CONF="$p"
                break
            fi
        done
    fi
    
    # Detect existing auto_power_off repository
    for p in ~/auto_power_off /home/*/auto_power_off; do
        if [ -d "$p" ]; then
            DEFAULT_REPO_PATH="$p"

            if [ -d "$DEFAULT_REPO_PATH" ]; then
                print_status "Vérification de l'état du dépôt Git..."
                repair_git_repo "$DEFAULT_REPO_PATH"
                verify_version "$MODULE_PATH"
            fi

            break
        fi
    done
}

# Installation paths
KLIPPER_PATH=""
MODULE_PATH=""
LANGS_PATH=""
PRINTER_CONFIG_DIR=""
MOONRAKER_CONF=""

# Default repo path for update manager
DEFAULT_REPO_PATH=""

# Automatically detect paths
detect_paths

# Finalize paths after detection
if [ -n "$KLIPPER_PATH" ]; then
    MODULE_PATH="${KLIPPER_PATH}/klippy/extras/auto_power_off.py"
    LANGS_PATH="${KLIPPER_PATH}/klippy/extras/auto_power_off_langs"
else
    KLIPPER_PATH="${HOME}/klipper"
    MODULE_PATH="${KLIPPER_PATH}/klippy/extras/auto_power_off.py"
    LANGS_PATH="${KLIPPER_PATH}/klippy/extras/auto_power_off_langs"
fi

if [ -z "$DEFAULT_REPO_PATH" ]; then
    DEFAULT_REPO_PATH="${HOME}/auto_power_off"
fi

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

# Function to add update manager config to moonraker.conf
add_update_manager_config() {
    local moonraker_conf="$1"
    local repo_path="$2"

    # Check moonraker.asvc file — it lives next to printer_data, not inside
    # printer_data/config. Search both locations plus common layouts.
    if [ -z "$moonraker_asvc" ]; then
        local config_dir="${PRINTER_CONFIG_DIR%/}"
        local data_dir="$(dirname "$config_dir")"
        for candidate in \
            "$config_dir/moonraker.asvc" \
            "$data_dir/moonraker.asvc" \
            "$HOME/printer_data/moonraker.asvc" \
            "$HOME/klipper_config/moonraker.asvc"; do
            if [ -f "$candidate" ]; then
                moonraker_asvc="$candidate"
                break
            fi
        done
        # If none exist, default to the canonical location so the warning
        # below points at the right path for new installs.
        if [ -z "$moonraker_asvc" ]; then
            moonraker_asvc="$data_dir/moonraker.asvc"
        fi
    fi

    if [ ! -f "$moonraker_asvc" ]; then
        if [ "$LANG_CHOICE" = "fr" ]; then
            print_warning "Fichier moonraker.asvc non trouvé à $moonraker_asvc"
            print_warning "Le service auto_power_off ne sera pas ajouté automatiquement"
        else
            print_warning "moonraker.asvc file not found at $moonraker_asvc"
            print_warning "auto_power_off service will not be automatically added"
        fi
    else
        # Add auto_power_off if not already present
        if ! grep -q "auto_power_off" "$moonraker_asvc"; then
            echo "auto_power_off" >> "$moonraker_asvc"
            if [ "$LANG_CHOICE" = "fr" ]; then
                print_success "Service auto_power_off ajouté à moonraker.asvc"
            else
                print_success "auto_power_off service added to moonraker.asvc"
            fi
        fi
    fi

    # Check configuration file
    if [ ! -f "$moonraker_conf" ]; then
        if [ "$LANG_CHOICE" = "fr" ]; then
            print_warning "Fichier moonraker.conf non trouvé à $moonraker_conf"
            print_warning "Configuration du gestionnaire de mise à jour non ajoutée"
        else
            print_warning "moonraker.conf file not found at $moonraker_conf"
            print_warning "Update manager configuration not added"
        fi
        return 1
    fi
    
    # Remove old update manager configuration if it exists
    # This avoids duplicates or incorrect configurations
    if grep -q "\[update_manager auto_power_off\]" "$moonraker_conf"; then
        # Backup only once — avoid overwriting a good .bak on re-runs
        if [ ! -f "${moonraker_conf}.bak" ]; then
            cp "$moonraker_conf" "${moonraker_conf}.bak"
        fi

        if [ "$LANG_CHOICE" = "fr" ]; then
            print_status "Suppression de l'ancienne configuration du gestionnaire de mise à jour"
        else
            print_status "Removing old update manager configuration"
        fi
        
        # Remove the entire [update_manager auto_power_off] section and its attributes
        # This approach is more robust, as it also removes old incorrect URLs
        awk '
        BEGIN { skip=0; }
        /^\[update_manager auto_power_off\]/ { skip=1; next; }
        /^\[/ { if (skip) { skip=0; } }
        { if (!skip) print; }
        ' "$moonraker_conf" > "${moonraker_conf}.tmp" && mv "${moonraker_conf}.tmp" "$moonraker_conf"
        
        # Remove any remaining consecutive empty lines
        sed -i '/^$/N;/^\n$/D' "$moonraker_conf"
    fi
    
    # Add configuration with multilingual support and correct URL (case-sensitive)
    cat >> "$moonraker_conf" << EOL

[update_manager auto_power_off]
type: git_repo
path: ${repo_path}
origin: ${REPO_GIT}
primary_branch: main
install_script: scripts/install.sh

EOL
    
    if [ "$LANG_CHOICE" = "fr" ]; then
        print_success "Configuration du gestionnaire de mise à jour ajoutée à moonraker.conf"
    else
        print_success "Update manager configuration added to moonraker.conf"
    fi
    
    return 0
}

# Function to properly initialize a git repository
setup_git_repo() {
    local repo_dir="$1"
    local username="$2"
    local email="$3"
    
    # Check if the destination folder already exists
    if [ -d "$repo_dir" ]; then
        # If a Git repository already exists, clean it up and update its configuration
        if [ -d "$repo_dir/.git" ]; then
            cd "$repo_dir" || exit 1
            
            # Backup modified files if necessary
            if [ "$(git status --porcelain | wc -l)" -gt 0 ]; then
                if [ "$LANG_CHOICE" = "fr" ]; then
                    print_status "Sauvegarde des fichiers modifiés..."
                else
                    print_status "Backing up modified files..."
                fi
                mkdir -p /tmp/auto_power_off_backup
                git status --porcelain | grep -v '??' | awk '{print $2}' | xargs -I{} cp --parents {} /tmp/auto_power_off_backup/
            fi
            
            # Remove the old remote configuration
            git remote remove origin 2>/dev/null || true
            
            # Add the new remote with the correct URL (case-sensitive)
            git remote add origin "${REPO_GIT}"
            
            # Configure git user if necessary
            if ! git config --get user.name > /dev/null; then
                git config user.name "$username"
            fi
            
            if ! git config --get user.email > /dev/null; then
                git config user.email "$email"
            fi
            
            # Add the repository to safe directories
            git config --global --add safe.directory "$repo_dir"
            
            if [ "$LANG_CHOICE" = "fr" ]; then
                print_status "Dépôt Git mis à jour à $repo_dir"
            else
                print_status "Git repository updated at $repo_dir"
            fi
            
            return 0
        else
            # If the folder exists but is not a Git repository, remove it
            rm -rf "$repo_dir"
        fi
    fi
    
    # Clone the repository directly instead of creating an empty folder
    if [ "$LANG_CHOICE" = "fr" ]; then
        print_status "Clonage du dépôt Git à $repo_dir"
    else
        print_status "Cloning Git repository to $repo_dir"
    fi
    
    # Use the correct URL with proper case
    git clone "${REPO_GIT}" "$repo_dir"
    
    # Enter the repository folder
    cd "$repo_dir" || exit 1
    
    # Configure git user
    git config user.name "$username"
    git config user.email "$email"
    
    # Add the repository to safe directories
    git config --global --add safe.directory "$repo_dir"
    
    return 0
}

# Install module files from the cloned repo into the Klipper extras directory.
# This function never creates git commits — the ~/auto_power_off repo must stay
# as a clean clone so Moonraker's update manager can pull without divergence.
install_from_repo() {
    local repo_dir="$1"

    # Python module
    if [ -f "$repo_dir/src/auto_power_off.py" ]; then
        cp "$repo_dir/src/auto_power_off.py" "$MODULE_PATH"
    fi

    # Language files
    mkdir -p "$LANGS_PATH"
    if [ -d "$repo_dir/src/auto_power_off_langs" ]; then
        cp "$repo_dir/src/auto_power_off_langs/"*.json "$LANGS_PATH/" 2>/dev/null || true
    fi

    # UI config files — only for the selected interface
    if [ "$UI_TYPE" = "fluidd" ] || [ "$UI_TYPE" = "both" ]; then
        cp "$repo_dir/ui/fluidd/auto_power_off.cfg" "$PRINTER_CONFIG_DIR/fluidd/" 2>/dev/null || true
        cp "$repo_dir/ui/fluidd/auto_power_off_fr.cfg" "$PRINTER_CONFIG_DIR/fluidd/" 2>/dev/null || true
    fi
    if [ "$UI_TYPE" = "mainsail" ] || [ "$UI_TYPE" = "both" ]; then
        cp "$repo_dir/ui/mainsail/auto_power_off.cfg" "$PRINTER_CONFIG_DIR/mainsail/" 2>/dev/null || true
        cp "$repo_dir/ui/mainsail/auto_power_off_panel.cfg" "$PRINTER_CONFIG_DIR/mainsail/" 2>/dev/null || true
        cp "$repo_dir/ui/mainsail/auto_power_off_fr.cfg" "$PRINTER_CONFIG_DIR/mainsail/" 2>/dev/null || true
        cp "$repo_dir/ui/mainsail/auto_power_off_panel_fr.cfg" "$PRINTER_CONFIG_DIR/mainsail/" 2>/dev/null || true
    fi

    return 0
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

# Display language options if no argument was provided and not running from update manager
if [ "$LANG_CHOICE" = "$DEFAULT_LANG" ] && [ $# -eq 0 ] && [ -t 0 ]; then
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
    MSG_UPDATE_COMPLETE="Mise à jour terminée !"
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
    MSG_ADD_MOONRAKER="Voulez-vous ajouter la configuration du gestionnaire de mise à jour à moonraker.conf? [o/N]"
    MSG_MOONRAKER_PATH="Chemin vers moonraker.conf [/home/pi/printer_data/config/moonraker.conf]:"
    MSG_CREATING_REPO="Création du dépôt local pour les mises à jour..."
    MSG_REPO_CREATED="Dépôt local créé avec succès."
    MSG_REPO_PATH="Chemin pour le dépôt local [${DEFAULT_REPO_PATH}]:"
    MSG_BACKUP_CREATED="Sauvegarde des fichiers existants créée."
    MSG_UPDATE_MODE="Mode mise à jour détecté. Mise à jour des fichiers..."
    MSG_INSTALL_MODE="Installation nouvelle détectée."
    MSG_REPO_EXISTS="Un dépôt existe déjà à cet emplacement."
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
    MSG_UPDATE_COMPLETE="Update complete!"
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
    MSG_ADD_MOONRAKER="Do you want to add update manager configuration to moonraker.conf? [y/N]"
    MSG_MOONRAKER_PATH="Path to moonraker.conf [/home/pi/printer_data/config/moonraker.conf]:"
    MSG_CREATING_REPO="Creating local repository for updates..."
    MSG_REPO_CREATED="Local repository created successfully."
    MSG_REPO_PATH="Path for local repository [${DEFAULT_REPO_PATH}]:"
    MSG_BACKUP_CREATED="Backup of existing files created."
    MSG_UPDATE_MODE="Update mode detected. Updating files..."
    MSG_INSTALL_MODE="New installation detected."
    MSG_REPO_EXISTS="A repository already exists at this location."
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

# Show info about update or install mode
if [ "$UPDATE_MODE" = true ]; then
    print_status "$MSG_UPDATE_MODE"
    
    # Create backup of current files
    if [ -f "${MODULE_PATH}" ]; then
        cp "${MODULE_PATH}" "${MODULE_PATH}.bak"
    fi
    
    if [ -d "${LANGS_PATH}" ]; then
        mkdir -p "${LANGS_PATH}.bak"
        cp -r "${LANGS_PATH}"/* "${LANGS_PATH}.bak/"
    fi
    print_success "$MSG_BACKUP_CREATED"
else
    print_status "$MSG_INSTALL_MODE"
fi

# Create Klipper extras directory if needed
print_status "$MSG_CHECK_DIRS"
mkdir -p ~/klipper/klippy/extras
mkdir -p ~/klipper/klippy/extras/auto_power_off_langs
print_success "$MSG_EXTRAS_CHECKED"

# Auto-detect configuration path
if [ -z "$PRINTER_CONFIG_DIR" ]; then
    print_error "$MSG_CONFIG_NOT_FOUND"
    echo "$MSG_ENTER_PATH"
    read -r PRINTER_CONFIG_DIR
    
    if [ ! -d "$PRINTER_CONFIG_DIR" ]; then
        print_error "$MSG_DIR_NOT_EXISTS"
        exit 1
    fi
else
    # Confirm automatically detected path
    if [ -t 0 ]; then
        if [ "$LANG_CHOICE" = "fr" ]; then
            print_status "Répertoire de configuration détecté: $PRINTER_CONFIG_DIR"
            read -p "Est-ce correct? [O/n]: " confirm_path
            if [[ "$confirm_path" =~ ^[Nn] ]]; then
                print_status "Veuillez entrer le chemin correct:"
                read -r PRINTER_CONFIG_DIR
                
                if [ ! -d "$PRINTER_CONFIG_DIR" ]; then
                    print_error "$MSG_DIR_NOT_EXISTS"
                    exit 1
                fi
            fi
        else
            print_status "Configuration directory detected: $PRINTER_CONFIG_DIR"
            read -p "Is this correct? [Y/n]: " confirm_path
            if [[ "$confirm_path" =~ ^[Nn] ]]; then
                print_status "Please enter the correct path:"
                read -r PRINTER_CONFIG_DIR
                
                if [ ! -d "$PRINTER_CONFIG_DIR" ]; then
                    print_error "$MSG_DIR_NOT_EXISTS"
                    exit 1
                fi
            fi
        fi
    fi
fi

print_success "$MSG_CONFIG_FOUND $PRINTER_CONFIG_DIR"

# Detect the interface used (Fluidd or Mainsail)
# Skip if we're in update mode
UI_TYPE="fluidd"
if [ "$UPDATE_MODE" = false ] && [ -t 0 ]; then
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
fi

# Create directories for the UI (only those actually needed)
if [ "$UI_TYPE" = "fluidd" ] || [ "$UI_TYPE" = "both" ]; then
    mkdir -p "$PRINTER_CONFIG_DIR/fluidd"
fi
if [ "$UI_TYPE" = "mainsail" ] || [ "$UI_TYPE" = "both" ]; then
    mkdir -p "$PRINTER_CONFIG_DIR/mainsail"
fi
print_success "$MSG_UI_DIRS_CREATED"

# In UPDATE_MODE the repo was already updated by Moonraker's git pull;
# install_from_repo (called below) copies from there. Skip wget entirely.
if [ "$UPDATE_MODE" = false ]; then
    # Download the Python module
    print_status "$MSG_DL_MODULE"
    wget -q -O ~/klipper/klippy/extras/auto_power_off.py "$REPO_URL/src/auto_power_off.py"
    print_success "$MSG_MODULE_DOWNLOADED"

    # Create language directories
    print_status "$MSG_CREATING_LANG_DIRS"
    mkdir -p ~/klipper/klippy/extras/auto_power_off_langs
    print_success "$MSG_LANG_DIRS_CREATED"

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
        wget -q -O "$PRINTER_CONFIG_DIR/fluidd/auto_power_off.cfg" "$REPO_URL/ui/fluidd/auto_power_off.cfg"
        wget -q -O "$PRINTER_CONFIG_DIR/fluidd/auto_power_off_fr.cfg" "$REPO_URL/ui/fluidd/auto_power_off_fr.cfg"
        print_success "$MSG_FLUIDD_CREATED"
    fi

    # Create Mainsail configuration file
    if [ "$UI_TYPE" = "mainsail" ] || [ "$UI_TYPE" = "both" ]; then
        print_status "$MSG_CREATE_MAINSAIL"
        wget -q -O "$PRINTER_CONFIG_DIR/mainsail/auto_power_off.cfg" "$REPO_URL/ui/mainsail/auto_power_off.cfg"
        wget -q -O "$PRINTER_CONFIG_DIR/mainsail/auto_power_off_panel.cfg" "$REPO_URL/ui/mainsail/auto_power_off_panel.cfg"
        wget -q -O "$PRINTER_CONFIG_DIR/mainsail/auto_power_off_fr.cfg" "$REPO_URL/ui/mainsail/auto_power_off_fr.cfg"
        wget -q -O "$PRINTER_CONFIG_DIR/mainsail/auto_power_off_panel_fr.cfg" "$REPO_URL/ui/mainsail/auto_power_off_panel_fr.cfg"
        print_success "$MSG_MAINSAIL_CREATED"
    fi
fi

# Ask user if they want to add the configuration to printer.cfg
# Skip if we're in update mode
if [ "$UPDATE_MODE" = false ] && [ -t 0 ]; then
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
                if grep -q "SAVE_CONFIG" "$CONFIG_FILE"; then
                    # Prepare configuration text
                    CONFIG_TEXT="\n#\n# Auto Power Off Configuration\n#\n"
                    
                    # Add appropriate includes based on interface
                    if [ "$UI_TYPE" = "fluidd" ]; then
                        CONFIG_TEXT="${CONFIG_TEXT}[include fluidd/auto_power_off.cfg]  # Include Fluidd panel\n\n"
                    elif [ "$UI_TYPE" = "mainsail" ]; then
                        CONFIG_TEXT="${CONFIG_TEXT}[include mainsail/auto_power_off.cfg]  # Include Mainsail panel\n\n"
                    else
                        CONFIG_TEXT="${CONFIG_TEXT}[include fluidd/auto_power_off.cfg]  # Include Fluidd panel\n"
                        CONFIG_TEXT="${CONFIG_TEXT}[include mainsail/auto_power_off.cfg]  # Include Mainsail panel\n\n"
                    fi
                    
                    # Add auto_power_off section
                    CONFIG_TEXT="${CONFIG_TEXT}[auto_power_off]\nidle_timeout: 600     # Idle time in seconds before power off (10 minutes)\ntemp_threshold: 40    # Temperature threshold in °C (printer considered cool)\npower_device: psu_control  # Name of your power device (must match the [power] section)\nauto_poweroff_enabled: True  # Enable auto power off by default at startup\nlanguage: auto        # Language setting: 'en', 'fr', or 'auto' for auto-detection\ndiagnostic_mode: False # Enable detailed logging for troubleshooting power off issues"
                    
                    # Insert before SAVE_CONFIG section
                    awk -v config="$CONFIG_TEXT" '/SAVE_CONFIG/{ print config; print } !/SAVE_CONFIG/{ print }' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
                else
                    # If no SAVE_CONFIG, add to end
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
        fi
    fi
fi

# UPDATE_MODE: Moonraker update manager already ran git pull on the repo.
# Just copy the updated files to klipper/extras — never touch moonraker.conf
# or create git commits (that would cause "diverged from remote" again).
if [ "$UPDATE_MODE" = true ]; then
    if [ -n "$DEFAULT_REPO_PATH" ] && [ -d "$DEFAULT_REPO_PATH/src" ]; then
        install_from_repo "$DEFAULT_REPO_PATH"
    fi
# Interactive fresh install / re-install: offer moonraker update manager setup.
elif [ -t 0 ]; then
    if [ -z "$MOONRAKER_CONF" ]; then
        echo "$MSG_MOONRAKER_PATH"
        read -r MOONRAKER_CONF
        [ -z "$MOONRAKER_CONF" ] && MOONRAKER_CONF="$PRINTER_CONFIG_DIR/moonraker.conf"
    else
        if [ "$LANG_CHOICE" = "fr" ]; then
            print_status "Fichier moonraker.conf détecté: $MOONRAKER_CONF"
            read -p "Est-ce correct? [O/n]: " confirm_moonraker
            [[ "$confirm_moonraker" =~ ^[Nn] ]] && { print_status "Veuillez entrer le chemin correct:"; read -r MOONRAKER_CONF; }
        else
            print_status "Moonraker.conf file detected: $MOONRAKER_CONF"
            read -p "Is this correct? [Y/n]: " confirm_moonraker
            [[ "$confirm_moonraker" =~ ^[Nn] ]] && { print_status "Please enter the correct path:"; read -r MOONRAKER_CONF; }
        fi
    fi

    read -p "$MSG_ADD_MOONRAKER" ADD_MOONRAKER

    if [[ "$ADD_MOONRAKER" =~ ^[$MSG_YES_CONFIRM][eEyY]?[sS]?$ ]]; then
        if [ -z "$REPO_PATH" ]; then
            if [ -n "$DEFAULT_REPO_PATH" ]; then
                if [ "$LANG_CHOICE" = "fr" ]; then
                    print_status "Dépôt local détecté: $DEFAULT_REPO_PATH"
                    read -p "Est-ce correct? [O/n]: " confirm_repo
                    if [[ "$confirm_repo" =~ ^[Nn] ]]; then
                        print_status "Veuillez entrer le chemin correct:"; read -r REPO_PATH
                    else
                        REPO_PATH="$DEFAULT_REPO_PATH"
                    fi
                else
                    print_status "Local repository detected: $DEFAULT_REPO_PATH"
                    read -p "Is this correct? [Y/n]: " confirm_repo
                    if [[ "$confirm_repo" =~ ^[Nn] ]]; then
                        print_status "Please enter the correct path:"; read -r REPO_PATH
                    else
                        REPO_PATH="$DEFAULT_REPO_PATH"
                    fi
                fi
            else
                echo "$MSG_REPO_PATH"; read -r REPO_PATH
                [ -z "$REPO_PATH" ] && REPO_PATH="$DEFAULT_REPO_PATH"
            fi
        fi

        print_status "$MSG_CREATING_REPO"
        GIT_USERNAME="$(whoami)"
        GIT_EMAIL="$GIT_USERNAME@$(hostname)"

        # Clone or update remote URL — never commit local changes
        setup_git_repo "$REPO_PATH" "$GIT_USERNAME" "$GIT_EMAIL"
        print_success "$MSG_REPO_CREATED"

        add_update_manager_config "$MOONRAKER_CONF" "$REPO_PATH"
        restart_moonraker
    fi
fi

# Ask user if they want to restart Klipper
if [ -t 0 ]; then
    echo "$MSG_RESTART_KLIPPER"
    read -r RESTART_KLIPPER
    
    if [[ "$RESTART_KLIPPER" =~ ^[$MSG_YES_CONFIRM][eEyY]?[sS]?$ ]]; then
        print_status "$MSG_RESTARTING"
        sudo systemctl restart klipper
        print_success "$MSG_RESTARTED"
        
        echo "$MSG_WAIT_RESTART"
        sleep 5
        
        # Check if the module was loaded correctly
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
fi

echo ""
if [ "$UPDATE_MODE" = true ]; then
    print_success "$MSG_UPDATE_COMPLETE"
else
    print_success "$MSG_INSTALL_COMPLETE"
fi

# Only show how to use if not in update mode or if explicitly run interactively
if [ "$UPDATE_MODE" = false ] || [ -t 0 ]; then
    echo ""
    echo -e "${GREEN}$MSG_HOW_TO_USE${NC}"
    echo "$MSG_PANEL_AVAILABLE"
    echo "$MSG_AUTO_ACTIVATE"
    echo "$MSG_AVAILABLE_CMDS"
    echo "$MSG_CMD_ON"
    echo "$MSG_CMD_OFF"
    echo "$MSG_CMD_START"
    
    # Note on Moonraker integration
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
fi
