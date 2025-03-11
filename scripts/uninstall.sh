#!/bin/bash
# Script de désinstallation pour le module Klipper Auto Power Off
# Uninstallation script for Klipper Auto Power Off module
#
# Ce script supprime tous les fichiers et configurations installés par le module
# This script removes all files and configurations installed by the module
#
# Usage: bash uninstall.sh [--en|--fr] [--force]

# Variables par défaut / Default variables
DEFAULT_LANG="en"
LANG_CHOICE="$DEFAULT_LANG"
FORCE_MODE=false

# Couleurs pour les messages / Colors for messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Chemins par défaut (seront détectés automatiquement)
# Default paths (will be detected automatically)
KLIPPER_PATH=""
MODULE_PATH=""
LANGS_PATH=""
PRINTER_CONFIG_DIR=""
MOONRAKER_CONF=""
REPO_PATH=""

# Vérifier les arguments pour la préférence de langue
# Check arguments for language preference and force mode
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
        --force)
            FORCE_MODE=true
            shift
            ;;
    esac
done

# Afficher les options de langue si aucun argument n'a été fourni
if [ "$LANG_CHOICE" = "$DEFAULT_LANG" ] && [ $# -eq 0 ] && [ -t 0 ]; then
    echo "Select language / Choisir la langue:"
    echo "1) English"
    echo "2) Français"
    read -p "Choice/Choix [1-2, default=1]: " lang_num
    
    if [ "$lang_num" = "2" ]; then
        LANG_CHOICE="fr"
    fi
fi

# Fonctions pour afficher les messages formatés
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

# Définir les messages en fonction de la langue
if [ "$LANG_CHOICE" = "fr" ]; then
    MSG_ROOT_ERROR="Ne pas exécuter ce script en tant que root (sudo). Utilisez votre utilisateur normal."
    MSG_INTRO="Ce script va désinstaller le module Auto Power Off pour Klipper."
    MSG_CONFIRM="Êtes-vous sûr de vouloir désinstaller Auto Power Off? [o/N] "
    MSG_ABORT="Désinstallation annulée."
    MSG_YES_CONFIRM="o"
    MSG_CHECKING_PATHS="Vérification des chemins d'installation..."
    MSG_PATH_DETECTED="Chemins détectés:"
    MSG_NO_MODULE="Le module Auto Power Off ne semble pas être installé."
    MSG_CONTINUE="Voulez-vous quand même continuer? [o/N] "
    MSG_REMOVE_MODULE="Suppression du module principal..."
    MSG_REMOVE_LANGS="Suppression des fichiers de traduction..."
    MSG_REMOVE_UI="Suppression des fichiers d'interface utilisateur..."
    MSG_CLEAN_PRINTER_CFG="Nettoyage de printer.cfg..."
    MSG_PRINTER_CFG_NOT_FOUND="Fichier printer.cfg non trouvé."
    MSG_PRINTER_CFG_UPDATED="Fichier printer.cfg mis à jour."
    MSG_PRINTER_CFG_BACKUP="Une sauvegarde a été créée: "
    MSG_CLEAN_MOONRAKER="Nettoyage de moonraker.conf..."
    MSG_MOONRAKER_NOT_FOUND="Fichier moonraker.conf non trouvé."
    MSG_MOONRAKER_UPDATED="Fichier moonraker.conf mis à jour."
    MSG_MOONRAKER_BACKUP="Une sauvegarde a été créée: "
    MSG_REMOVE_REPO="Suppression du dépôt Git local..."
    MSG_REPO_REMOVED="Dépôt Git supprimé."
    MSG_REPO_NOT_FOUND="Dépôt Git non trouvé."
    MSG_RESTART_KLIPPER="Voulez-vous redémarrer Klipper maintenant? [o/N] "
    MSG_RESTARTING_KLIPPER="Redémarrage de Klipper..."
    MSG_RESTART_MOONRAKER="Voulez-vous redémarrer Moonraker maintenant? [o/N] "
    MSG_RESTARTING_MOONRAKER="Redémarrage de Moonraker..."
    MSG_SUCCESS="Auto Power Off a été désinstallé avec succès!"
    MSG_MANUAL_STEPS="Si certains chemins n'ont pas été détectés automatiquement, vous devrez peut-être effectuer un nettoyage manuel."
    MSG_RESTART_CMD="Commandes pour redémarrer manuellement:"
    MSG_RESTART_KLIPPER_CMD="sudo systemctl restart klipper"
    MSG_RESTART_MOONRAKER_CMD="sudo systemctl restart moonraker"
else
    # English messages
    MSG_ROOT_ERROR="Do not run this script as root (sudo). Use your normal user."
    MSG_INTRO="This script will uninstall the Auto Power Off module for Klipper."
    MSG_CONFIRM="Are you sure you want to uninstall Auto Power Off? [y/N] "
    MSG_ABORT="Uninstallation aborted."
    MSG_YES_CONFIRM="y"
    MSG_CHECKING_PATHS="Checking installation paths..."
    MSG_PATH_DETECTED="Detected paths:"
    MSG_NO_MODULE="The Auto Power Off module does not seem to be installed."
    MSG_CONTINUE="Do you want to continue anyway? [y/N] "
    MSG_REMOVE_MODULE="Removing main module..."
    MSG_REMOVE_LANGS="Removing translation files..."
    MSG_REMOVE_UI="Removing user interface files..."
    MSG_CLEAN_PRINTER_CFG="Cleaning printer.cfg..."
    MSG_PRINTER_CFG_NOT_FOUND="printer.cfg file not found."
    MSG_PRINTER_CFG_UPDATED="printer.cfg file updated."
    MSG_PRINTER_CFG_BACKUP="A backup has been created: "
    MSG_CLEAN_MOONRAKER="Cleaning moonraker.conf..."
    MSG_MOONRAKER_NOT_FOUND="moonraker.conf file not found."
    MSG_MOONRAKER_UPDATED="moonraker.conf file updated."
    MSG_MOONRAKER_BACKUP="A backup has been created: "
    MSG_REMOVE_REPO="Removing local Git repository..."
    MSG_REPO_REMOVED="Git repository removed."
    MSG_REPO_NOT_FOUND="Git repository not found."
    MSG_RESTART_KLIPPER="Do you want to restart Klipper now? [y/N] "
    MSG_RESTARTING_KLIPPER="Restarting Klipper..."
    MSG_RESTART_MOONRAKER="Do you want to restart Moonraker now? [y/N] "
    MSG_RESTARTING_MOONRAKER="Restarting Moonraker..."
    MSG_SUCCESS="Auto Power Off has been successfully uninstalled!"
    MSG_MANUAL_STEPS="If some paths were not automatically detected, you may need to perform manual cleanup."
    MSG_RESTART_CMD="Commands to restart manually:"
    MSG_RESTART_KLIPPER_CMD="sudo systemctl restart klipper"
    MSG_RESTART_MOONRAKER_CMD="sudo systemctl restart moonraker"
fi

# Vérifier si le script est exécuté en tant que root
if [ "$EUID" -eq 0 ]; then
    print_error "$MSG_ROOT_ERROR"
    exit 1
fi

# Afficher l'introduction
echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   Auto Power Off - Désinstallation     ${NC}"
echo -e "${BLUE}=========================================${NC}"
print_status "$MSG_INTRO"

# Demander confirmation avant de désinstaller (sauf en mode force)
if [ "$FORCE_MODE" = false ] && [ -t 0 ]; then
    echo -e "$MSG_CONFIRM"
    read -r CONFIRMATION
    if [[ ! "$CONFIRMATION" =~ ^[$MSG_YES_CONFIRM][eEyY]?[sS]?$ ]]; then
        print_status "$MSG_ABORT"
        exit 0
    fi
fi

# Fonction pour détecter automatiquement les chemins d'installation
# Function to automatically detect installation paths
detect_paths() {
    # Détection du répertoire Klipper / Detecting Klipper directory
    if [ -z "$KLIPPER_PATH" ]; then
        for p in ~/klipper /home/*/klipper; do
            if [ -d "$p" ]; then
                KLIPPER_PATH="$p"
                break
            fi
        done
    fi
    
    # Définir les chemins du module et des traductions / Set module and translation paths
    if [ -n "$KLIPPER_PATH" ]; then
        MODULE_PATH="${KLIPPER_PATH}/klippy/extras/auto_power_off.py"
        LANGS_PATH="${KLIPPER_PATH}/klippy/extras/auto_power_off_langs"
    else
        MODULE_PATH="${HOME}/klipper/klippy/extras/auto_power_off.py"
        LANGS_PATH="${HOME}/klipper/klippy/extras/auto_power_off_langs"
    fi
    
    # Détection automatique du répertoire de configuration / Auto-detect configuration directory
    if [ -z "$PRINTER_CONFIG_DIR" ]; then
        for p in ~/printer_data/config ~/klipper_config /home/*/printer_data/config /home/*/klipper_config; do
            if [ -d "$p" ]; then
                PRINTER_CONFIG_DIR="$p"
                break
            fi
        done
    fi
    
    # Détection du chemin de printer.cfg / Detect printer.cfg path
    if [ -z "$PRINTER_CFG" ]; then
        for p in "$PRINTER_CONFIG_DIR/printer.cfg" /home/*/printer_data/config/printer.cfg /home/*/klipper_config/printer.cfg; do
            if [ -f "$p" ]; then
                PRINTER_CFG="$p"
                break
            fi
        done
    fi
    
    # Détection du chemin de moonraker.conf / Detect moonraker.conf path
    if [ -z "$MOONRAKER_CONF" ]; then
        for p in "$PRINTER_CONFIG_DIR/moonraker.conf" /home/*/printer_data/config/moonraker.conf /home/*/klipper_config/moonraker.conf; do
            if [ -f "$p" ]; then
                MOONRAKER_CONF="$p"
                break
            fi
        done
    fi
    
    # Détection du dépôt auto_power_off existant / Detect existing auto_power_off repository
    if [ -z "$REPO_PATH" ]; then
        for p in ~/auto_power_off /home/*/auto_power_off; do
            if [ -d "$p" ]; then
                REPO_PATH="$p"
                break
            fi
        done
    fi
}

# Détecter les chemins automatiquement / Automatically detect paths
print_status "$MSG_CHECKING_PATHS"
detect_paths

# Afficher les chemins détectés
echo -e "$MSG_PATH_DETECTED"
echo "- Klipper: $KLIPPER_PATH"
echo "- Module: $MODULE_PATH"
echo "- Traductions: $LANGS_PATH"
echo "- Configuration: $PRINTER_CONFIG_DIR"
echo "- printer.cfg: $PRINTER_CFG"
echo "- moonraker.conf: $MOONRAKER_CONF"
echo "- Dépôt Git: $REPO_PATH"

# Vérifier si le module est installé / Check if the module is installed
if [ ! -f "$MODULE_PATH" ] && [ "$FORCE_MODE" = false ] && [ -t 0 ]; then
    print_warning "$MSG_NO_MODULE"
    echo -e "$MSG_CONTINUE"
    read -r CONTINUE
    if [[ ! "$CONTINUE" =~ ^[$MSG_YES_CONFIRM][eEyY]?[sS]?$ ]]; then
        print_status "$MSG_ABORT"
        exit 0
    fi
fi

# Supprimer le module principal / Remove main module
print_status "$MSG_REMOVE_MODULE"
if [ -f "$MODULE_PATH" ]; then
    rm -f "$MODULE_PATH"
    print_success "auto_power_off.py supprimé."
else
    print_warning "auto_power_off.py non trouvé."
fi

# Supprimer les fichiers de traduction / Remove translation files
print_status "$MSG_REMOVE_LANGS"
if [ -d "$LANGS_PATH" ]; then
    rm -rf "$LANGS_PATH"
    print_success "Répertoire de traductions supprimé."
else
    print_warning "Répertoire de traductions non trouvé."
fi

# Supprimer les fichiers d'interface utilisateur / Remove UI files
print_status "$MSG_REMOVE_UI"
# Fichiers Fluidd
if [ -f "$PRINTER_CONFIG_DIR/fluidd/auto_power_off.cfg" ]; then
    rm -f "$PRINTER_CONFIG_DIR/fluidd/auto_power_off.cfg"
    print_success "Panneau Fluidd (EN) supprimé."
fi
if [ -f "$PRINTER_CONFIG_DIR/fluidd/auto_power_off_fr.cfg" ]; then
    rm -f "$PRINTER_CONFIG_DIR/fluidd/auto_power_off_fr.cfg"
    print_success "Panneau Fluidd (FR) supprimé."
fi

# Fichiers Mainsail
if [ -f "$PRINTER_CONFIG_DIR/mainsail/auto_power_off.cfg" ]; then
    rm -f "$PRINTER_CONFIG_DIR/mainsail/auto_power_off.cfg"
    print_success "Panneau Mainsail (EN) supprimé."
fi
if [ -f "$PRINTER_CONFIG_DIR/mainsail/auto_power_off_panel.cfg" ]; then
    rm -f "$PRINTER_CONFIG_DIR/mainsail/auto_power_off_panel.cfg"
    print_success "Configuration Mainsail (EN) supprimée."
fi
if [ -f "$PRINTER_CONFIG_DIR/mainsail/auto_power_off_fr.cfg" ]; then
    rm -f "$PRINTER_CONFIG_DIR/mainsail/auto_power_off_fr.cfg"
    print_success "Panneau Mainsail (FR) supprimé."
fi
if [ -f "$PRINTER_CONFIG_DIR/mainsail/auto_power_off_panel_fr.cfg" ]; then
    rm -f "$PRINTER_CONFIG_DIR/mainsail/auto_power_off_panel_fr.cfg"
    print_success "Configuration Mainsail (FR) supprimée."
fi

# Nettoyer le fichier printer.cfg / Clean up printer.cfg file
print_status "$MSG_CLEAN_PRINTER_CFG"
if [ -f "$PRINTER_CFG" ]; then
    # Créer une sauvegarde avant de modifier / Create a backup before modifying
    BACKUP_FILE="${PRINTER_CFG}.bak.$(date +%Y%m%d%H%M%S)"
    cp "$PRINTER_CFG" "$BACKUP_FILE"
    if [ "$LANG_CHOICE" = "fr" ]; then
        print_status "Sauvegarde créée: $BACKUP_FILE"
    else
        print_status "Backup created: $BACKUP_FILE"
    fi
    print_success "$MSG_PRINTER_CFG_BACKUP $BACKUP_FILE"
    
    # Supprimer la section [auto_power_off] et les lignes include associées
    # Remove [auto_power_off] section and associated include lines
    TMP_FILE="${PRINTER_CFG}.tmp"
    
    # Supprimer les includes auto_power_off.cfg
    grep -v '\[include fluidd\/auto_power_off.cfg\]' "$PRINTER_CFG" | \
    grep -v '\[include mainsail\/auto_power_off.cfg\]' | \
    grep -v '\[include fluidd\/auto_power_off_fr.cfg\]' | \
    grep -v '\[include mainsail\/auto_power_off_fr.cfg\]' > "$TMP_FILE"
    
    # Supprimer la section [auto_power_off]
    awk '
    BEGIN { skip=0; }
    /^\[auto_power_off\]/ { skip=1; next; }
    /^\[/ { if (skip) { skip=0; } }
    { if (!skip) print; }
    ' "$TMP_FILE" > "${TMP_FILE}.2" && mv "${TMP_FILE}.2" "$TMP_FILE"
    
    # Supprimer les lignes vides consécutives
    sed -i '/^$/N;/^\n$/D' "$TMP_FILE"
    
    # Supprimer les commentaires liés à Auto Power Off
    grep -v '# Auto Power Off Configuration' "$TMP_FILE" > "${TMP_FILE}.2" && mv "${TMP_FILE}.2" "$TMP_FILE"
    
    # Appliquer les modifications
    mv "$TMP_FILE" "$PRINTER_CFG"
    print_success "$MSG_PRINTER_CFG_UPDATED"
else
    print_warning "$MSG_PRINTER_CFG_NOT_FOUND"
fi

# Nettoyer le fichier moonraker.conf / Clean up moonraker.conf file
print_status "$MSG_CLEAN_MOONRAKER"
if [ -f "$MOONRAKER_CONF" ]; then
    # Créer une sauvegarde avant de modifier / Create a backup before modifying
    BACKUP_FILE="${MOONRAKER_CONF}.bak.$(date +%Y%m%d%H%M%S)"
    cp "$MOONRAKER_CONF" "$BACKUP_FILE"
    if [ "$LANG_CHOICE" = "fr" ]; then
        print_status "Sauvegarde créée: $BACKUP_FILE"
    else
        print_status "Backup created: $BACKUP_FILE"
    fi
    print_success "$MSG_MOONRAKER_BACKUP $BACKUP_FILE"
    
    # Supprimer la section [update_manager auto_power_off]
    # Remove [update_manager auto_power_off] section
    TMP_FILE="${MOONRAKER_CONF}.tmp"
    
    awk '
    BEGIN { skip=0; }
    /^\[update_manager auto_power_off\]/ { skip=1; next; }
    /^\[/ { if (skip) { skip=0; } }
    { if (!skip) print; }
    ' "$MOONRAKER_CONF" > "$TMP_FILE"
    
    # Supprimer les lignes vides consécutives
    sed -i '/^$/N;/^\n$/D' "$TMP_FILE"
    
    # Appliquer les modifications
    mv "$TMP_FILE" "$MOONRAKER_CONF"
    print_success "$MSG_MOONRAKER_UPDATED"
else
    print_warning "$MSG_MOONRAKER_NOT_FOUND"
fi

# Supprimer le dépôt Git local / Remove local Git repository
print_status "$MSG_REMOVE_REPO"
if [ -d "$REPO_PATH" ]; then
    rm -rf "$REPO_PATH"
    print_success "$MSG_REPO_REMOVED"
else
    print_warning "$MSG_REPO_NOT_FOUND"
fi

# Supprimer le fichier de persistance de langue / Remove language persistence file
if [ -f "$PRINTER_CONFIG_DIR/auto_power_off_language.conf" ]; then
    rm -f "$PRINTER_CONFIG_DIR/auto_power_off_language.conf"
    print_success "Fichier de persistance de langue supprimé."
fi

# Demander si l'utilisateur veut redémarrer Klipper / Ask if user wants to restart Klipper
if [ -t 0 ] && [ "$FORCE_MODE" = false ]; then
    echo -e "$MSG_RESTART_KLIPPER"
    read -r RESTART_KLIPPER
    
    if [[ "$RESTART_KLIPPER" =~ ^[$MSG_YES_CONFIRM][eEyY]?[sS]?$ ]]; then
        print_status "$MSG_RESTARTING_KLIPPER"
        sudo systemctl restart klipper
    fi
    
    # Demander si l'utilisateur veut redémarrer Moonraker
    echo -e "$MSG_RESTART_MOONRAKER"
    read -r RESTART_MOONRAKER
    
    if [[ "$RESTART_MOONRAKER" =~ ^[$MSG_YES_CONFIRM][eEyY]?[sS]?$ ]]; then
        print_status "$MSG_RESTARTING_MOONRAKER"
        sudo systemctl restart moonraker
    fi
else
    # En mode non interactif, ne pas redémarrer automatiquement
    print_warning "$MSG_RESTART_CMD"
    echo "$MSG_RESTART_KLIPPER_CMD"
    echo "$MSG_RESTART_MOONRAKER_CMD"
fi

# Afficher un message de succès
echo -e "${GREEN}=========================================${NC}"
print_success "$MSG_SUCCESS"
echo -e "${GREEN}=========================================${NC}"

# Avertissement pour le nettoyage manuel si nécessaire
print_warning "$MSG_MANUAL_STEPS"
