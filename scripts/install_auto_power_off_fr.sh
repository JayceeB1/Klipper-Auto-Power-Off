#!/bin/bash
# Script d'installation global pour le module Auto Power Off de Klipper
# Usage: bash install_auto_power_off_fr.sh

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher des messages formatés
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[ATTENTION]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERREUR]${NC} $1"
}

# Vérifier si le script est exécuté en tant que root
if [ "$EUID" -eq 0 ]; then
    print_error "Ne pas exécuter ce script en tant que root (sudo). Utilisez votre utilisateur normal."
    exit 1
fi

# Vérifier si Klipper est installé
if [ ! -d ~/klipper ]; then
    print_error "Le répertoire Klipper n'a pas été trouvé dans votre répertoire home."
    print_error "Assurez-vous que Klipper est installé avant d'exécuter ce script."
    exit 1
fi

# Créer le répertoire des extras de Klipper si nécessaire
print_status "Vérification des répertoires nécessaires..."
mkdir -p ~/klipper/klippy/extras
print_success "Répertoire des extras vérifié."

# Détection automatique du chemin de configuration
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
    print_error "Impossible de trouver automatiquement le répertoire de configuration."
    echo "Veuillez entrer le chemin complet vers votre répertoire de configuration Klipper:"
    read -r PRINTER_CONFIG_DIR
    
    if [ ! -d "$PRINTER_CONFIG_DIR" ]; then
        print_error "Le répertoire n'existe pas. Installation annulée."
        exit 1
    fi
fi

print_success "Répertoire de configuration trouvé: $PRINTER_CONFIG_DIR"

# Détecter l'interface utilisée (Fluidd ou Mainsail)
UI_TYPE="fluidd"
echo "Quelle interface utilisez-vous? (1 = Fluidd, 2 = Mainsail, 3 = Les deux)"
read -r UI_CHOICE

case $UI_CHOICE in
    2)
        UI_TYPE="mainsail"
        print_status "Configuration pour Mainsail..."
        ;;
    3)
        UI_TYPE="both"
        print_status "Configuration pour Fluidd et Mainsail..."
        ;;
    *)
        print_status "Configuration pour Fluidd (par défaut)..."
        ;;
esac

# Créer les répertoires pour l'interface utilisateur
mkdir -p $PRINTER_CONFIG_DIR/fluidd
if [ "$UI_TYPE" = "mainsail" ] || [ "$UI_TYPE" = "both" ]; then
    mkdir -p $PRINTER_CONFIG_DIR/mainsail
fi
print_success "Répertoires de l'interface utilisateur créés."

# Créer le module Python
print_status "Création du module Python auto_power_off.py..."
cat > ~/klipper/klippy/extras/auto_power_off.py << 'EOF'
# auto_power_off.py
# Script d'extinction automatique pour imprimante 3D sous Klipper
# À placer dans le dossier ~/klipper/klippy/extras/

import logging
import threading
import time

class AutoPowerOff:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        
        # Configuration des paramètres
        self.idle_timeout = config.getfloat('idle_timeout', 600.0)  # Temps d'inactivité en secondes (10 min par défaut)
        self.temp_threshold = config.getfloat('temp_threshold', 40.0)  # Seuil de température en °C
        self.power_device = config.get('power_device', 'psu_control')  # Le nom de votre périphérique d'alimentation
        self.enabled = config.getboolean('auto_poweroff_enabled', False)  # État activé/désactivé par défaut
        
        # S'enregistrer pour les événements
        self.printer.register_event_handler("klippy:ready", self._handle_ready)
        self.printer.register_event_handler("print_stats:complete", self._handle_print_complete)
        
        # Variables d'état
        self.shutdown_timer = None
        self.is_checking_temp = False
        self.countdown_end = 0
        self.last_temps = {"hotend": 0, "bed": 0}
        
        # Enregistrement pour les commandes gcode
        gcode = self.printer.lookup_object('gcode')
        gcode.register_command('AUTO_POWEROFF', self.cmd_AUTO_POWEROFF,
                              desc=self.cmd_AUTO_POWEROFF_help)
                              
        # Enregistrement pour l'API de status Fluidd/Mainsail
        self.printer.register_event_handler("klippy:connect", 
                                           self._handle_connect)
        
        # Logging
        self.logger = logging.getLogger('auto_power_off')
        self.logger.setLevel(logging.INFO)
    
    def _handle_connect(self):
        """Appelé lors de la connexion initiale"""
        # Enregistrer l'objet pour qu'il soit accessible via l'API
        self.printer.add_object("auto_power_off", self)
    
    def _handle_ready(self):
        """Appelé quand Klipper est prêt"""
        self.logger.info("Auto Power Off: Module initialisé")
        
        # Mise en place du vérificateur de température périodique
        self.reactor.register_timer(self._update_temps, self.reactor.monotonic() + 1)
    
    def _handle_print_complete(self):
        """Appelé quand l'impression est terminée"""
        if not self.enabled:
            self.logger.info("Impression terminée, mais l'extinction automatique est désactivée")
            return
            
        self.logger.info("Impression terminée, démarrage du minuteur d'extinction")
        
        # Annuler tout minuteur existant
        if self.shutdown_timer is not None:
            self.reactor.unregister_timer(self.shutdown_timer)
        
        # Démarrer le minuteur d'inactivité
        waketime = self.reactor.monotonic() + self.idle_timeout
        self.countdown_end = self.reactor.monotonic() + self.idle_timeout
        self.shutdown_timer = self.reactor.register_timer(self._check_conditions, waketime)
    
    def _check_conditions(self, eventtime):
        """Vérifie si les conditions pour éteindre sont remplies"""
        # Vérifier l'état d'impression actuel
        print_stats = self.printer.lookup_object('print_stats', None)
        if print_stats and print_stats.get_status(eventtime)['state'] != 'complete':
            self.logger.info("Impression en cours ou reprise, annulation de l'extinction")
            self.shutdown_timer = None
            return self.reactor.NEVER
        
        # Vérifier si l'imprimante est vraiment inactive
        idle_timeout = self.printer.lookup_object('idle_timeout')
        if idle_timeout.get_status(eventtime)['state'] != 'Idle':
            self.logger.info("Imprimante non inactive, report de l'extinction")
            return eventtime + 60.0  # Vérifier à nouveau dans 60 secondes
        
        # Vérifier les températures
        heaters = self.printer.lookup_object('heaters')
        hotend = self.printer.lookup_object('extruder').get_heater()
        try:
            bed = self.printer.lookup_object('heater_bed').get_heater()
            bed_temp = heaters.get_status(eventtime)[bed.get_name()]['temperature']
        except:
            bed_temp = 0.0
            
        hotend_temp = heaters.get_status(eventtime)[hotend.get_name()]['temperature']
        
        if max(hotend_temp, bed_temp) > self.temp_threshold:
            self.logger.info(f"Températures trop élevées (Hotend: {hotend_temp:.1f}, Bed: {bed_temp:.1f}), report de l'extinction")
            return eventtime + 60.0  # Vérifier à nouveau dans 60 secondes
        
        # Toutes les conditions sont remplies, éteindre l'imprimante
        self._power_off()
        self.shutdown_timer = None
        return self.reactor.NEVER
    
    def _power_off(self):
        """Éteindre l'imprimante"""
        self.logger.info("Conditions remplies, extinction de l'imprimante")
        
        try:
            # Accéder au contrôleur d'alimentation et l'éteindre
            power_device = self.printer.lookup_object('power ' + self.power_device)
            power_device.set_power(0)
            self.logger.info("Imprimante éteinte avec succès")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'extinction: {str(e)}")
    
    def _update_temps(self, eventtime):
        """Met à jour les températures pour l'API de status"""
        try:
            heaters = self.printer.lookup_object('heaters')
            hotend = self.printer.lookup_object('extruder').get_heater()
            hotend_temp = heaters.get_status(eventtime)[hotend.get_name()]['temperature']
            
            try:
                bed = self.printer.lookup_object('heater_bed').get_heater()
                bed_temp = heaters.get_status(eventtime)[bed.get_name()]['temperature']
            except:
                bed_temp = 0.0
                
            self.last_temps = {"hotend": hotend_temp, "bed": bed_temp}
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour des températures: {str(e)}")
            
        # Planifier la prochaine mise à jour dans 1 seconde
        return eventtime + 1.0
        
    def get_status(self, eventtime):
        """Obtenir le statut pour l'API Fluidd/Mainsail"""
        time_left = max(0, self.countdown_end - eventtime) if self.shutdown_timer is not None else 0
        
        return {
            'enabled': self.enabled,
            'active': self.shutdown_timer is not None,
            'countdown': int(time_left),
            'idle_timeout': int(self.idle_timeout),
            'temp_threshold': self.temp_threshold,
            'current_temps': self.last_temps
        }
        
    cmd_AUTO_POWEROFF_help = "Configure ou déclenche l'extinction automatique de l'imprimante"
    def cmd_AUTO_POWEROFF(self, gcmd):
        """Commande GCODE pour configurer ou déclencher l'extinction automatique"""
        option = gcmd.get('OPTION', 'status')
        
        if option.lower() == 'on':
            # Activer globalement l'extinction automatique
            self.enabled = True
            gcmd.respond_info("Extinction automatique activée globalement")
                
        elif option.lower() == 'off':
            # Désactiver globalement l'extinction automatique
            self.enabled = False
            if self.shutdown_timer is not None:
                self.reactor.unregister_timer(self.shutdown_timer)
                self.shutdown_timer = None
            gcmd.respond_info("Extinction automatique désactivée globalement")
                
        elif option.lower() == 'now':
            # Déclencher l'extinction immédiatement
            gcmd.respond_info("Extinction de l'imprimante...")
            # Petit délai pour permettre à la réponse de gcode d'être envoyée
            self.reactor.register_callback(lambda e: self._power_off())
        
        elif option.lower() == 'start':
            # Démarrer le minuteur d'inactivité
            if not self.enabled:
                gcmd.respond_info("L'extinction automatique est désactivée globalement")
                return
            if self.shutdown_timer is None:
                waketime = self.reactor.monotonic() + self.idle_timeout
                self.countdown_end = self.reactor.monotonic() + self.idle_timeout
                self.shutdown_timer = self.reactor.register_timer(self._check_conditions, waketime)
                gcmd.respond_info("Minuteur d'extinction automatique démarré")
            else:
                gcmd.respond_info("Le minuteur d'extinction automatique est déjà actif")
                
        elif option.lower() == 'cancel':
            # Annuler le minuteur d'inactivité
            if self.shutdown_timer is not None:
                self.reactor.unregister_timer(self.shutdown_timer)
                self.shutdown_timer = None
                gcmd.respond_info("Minuteur d'extinction automatique annulé")
            else:
                gcmd.respond_info("Aucun minuteur d'extinction automatique actif")
            
        elif option.lower() == 'status':
            # Afficher l'état actuel
            enabled_status = "activée" if self.enabled else "désactivée"
            timer_status = "actif" if self.shutdown_timer is not None else "inactif"
            temps = f"Buse: {self.last_temps['hotend']:.1f}°C, Lit: {self.last_temps['bed']:.1f}°C"
            
            time_left = max(0, self.countdown_end - self.reactor.monotonic())
            countdown = f"{int(time_left / 60)}m {int(time_left % 60)}s" if self.shutdown_timer is not None else "N/A"
            
            gcmd.respond_info(
                f"Extinction automatique: {enabled_status}\n"
                f"Minuteur: {timer_status} (Reste: {countdown})\n"
                f"Températures actuelles: {temps}\n"
                f"Seuil de température: {self.temp_threshold}°C\n"
                f"Délai d'inactivité: {int(self.idle_timeout / 60)} minutes"
            )
            
        else:
            gcmd.respond_info("Option non reconnue. Utilisez ON, OFF, START, CANCEL, NOW ou STATUS")

def load_config(config):
    return AutoPowerOff(config)
EOF
print_success "Module Python créé."

# Créer le fichier de configuration de Fluidd
if [ "$UI_TYPE" = "fluidd" ] || [ "$UI_TYPE" = "both" ]; then
    print_status "Création du panneau Fluidd..."
    cat > $PRINTER_CONFIG_DIR/fluidd/auto_power_off.cfg << 'EOF'
<!-- auto_power_off.cfg - Panneau Fluidd pour l'extinction automatique -->
<!-- Sauvegardez ce fichier dans ~/printer_data/config/fluidd/auto_power_off.cfg -->

{% set auto_power_off = printer['auto_power_off'] %}

<v-card>
  <v-card-title class="blue-grey darken-1 white--text">
    <v-icon class="white--text">mdi-power-plug-off</v-icon>
    Extinction Automatique
  </v-card-title>
  <v-card-text class="py-3">
    <v-layout align-center>
      <v-flex>
        <p class="mb-0">État global:</p>
      </v-flex>
      <v-flex class="text-right">
        <v-switch
          v-model="auto_power_off_enabled"
          hide-details
          dense
          class="mt-0"
          @change="setPoweroffState"
        />
      </v-flex>
    </v-layout>

    <v-divider class="my-3"></v-divider>

    <p v-if="auto_power_off.active" class="mb-2 mt-0">
      <v-icon small color="orange">mdi-timer-outline</v-icon>
      L'imprimante s'éteindra automatiquement dans <strong>{{ formatTime(auto_power_off.countdown) }}</strong>
    </p>
    <p v-else class="mb-2 mt-0">
      <v-icon small color="gray">mdi-timer-off-outline</v-icon>
      Aucun minuteur d'extinction actif
    </p>

    <p class="mb-2">
      <v-icon small color="red">mdi-thermometer</v-icon>
      Température de la buse: <strong>{{ auto_power_off.current_temps.hotend.toFixed(1) }}°C</strong> 
      | Lit: <strong>{{ auto_power_off.current_temps.bed.toFixed(1) }}°C</strong>
    </p>

    <p class="mb-2">
      <v-icon small color="blue">mdi-alert-circle-outline</v-icon>
      L'extinction se déclenchera quand les températures seront en dessous de <strong>{{ auto_power_off.temp_threshold }}°C</strong>
    </p>

    <v-alert
      v-if="auto_power_off.current_temps.hotend > auto_power_off.temp_threshold || auto_power_off.current_temps.bed > auto_power_off.temp_threshold"
      dense
      text
      type="warning"
      class="mt-2 mb-2"
    >
      Les températures sont encore trop élevées pour l'extinction
    </v-alert>

    <v-layout class="mt-3">
      <v-btn
        small
        color="primary"
        text
        :disabled="!auto_power_off.enabled || auto_power_off.active"
        @click="sendGcode('AUTO_POWEROFF START')"
      >
        <v-icon small class="mr-1">mdi-timer-outline</v-icon>
        Démarrer
      </v-btn>
      <v-btn
        small
        color="error"
        text
        :disabled="!auto_power_off.active"
        @click="sendGcode('AUTO_POWEROFF CANCEL')"
      >
        <v-icon small class="mr-1">mdi-timer-off-outline</v-icon>
        Annuler
      </v-btn>
      <v-spacer></v-spacer>
      <v-btn
        small
        color="error"
        @click="confirmShutdown"
      >
        <v-icon small class="mr-1">mdi-power</v-icon>
        Éteindre maintenant
      </v-btn>
    </v-layout>
  </v-card-text>
</v-card>

<script>
  export default {
    data() {
      return {
        auto_power_off_enabled: this.printer.auto_power_off?.enabled || false
      }
    },
    methods: {
      setPoweroffState() {
        const cmd = this.auto_power_off_enabled ? 'AUTO_POWEROFF ON' : 'AUTO_POWEROFF OFF'
        this.$store.dispatch('server/addEvent', { message: `Extinction automatique ${this.auto_power_off_enabled ? 'activée' : 'désactivée'}`, type: 'complete' })
        this.$socket.emit('printer.gcode.script', { script: cmd })
      },
      confirmShutdown() {
        this.$store.dispatch('power/createConfirmDialog', { 
          title: 'Éteindre l\'imprimante',
          text: 'Êtes-vous sûr de vouloir éteindre l\'imprimante maintenant ?',
          onConfirm: () => this.sendGcode('AUTO_POWEROFF NOW')
        })
      },
      sendGcode(gcode) {
        this.$socket.emit('printer.gcode.script', { script: gcode })
      },
      formatTime(seconds) {
        const minutes = Math.floor(seconds / 60)
        seconds = seconds % 60
        return `${minutes}m ${seconds}s`
      }
    },
    watch: {
      'printer.auto_power_off.enabled': {
        deep: true,
        handler(val) {
          this.auto_power_off_enabled = val
        }
      }
    }
  }
</script>
EOF
    print_success "Panneau Fluidd créé."
fi

# Créer le fichier de configuration de Mainsail
if [ "$UI_TYPE" = "mainsail" ] || [ "$UI_TYPE" = "both" ]; then
    print_status "Création du panneau Mainsail..."
    cat > $PRINTER_CONFIG_DIR/mainsail/auto_power_off.cfg << 'EOF'
# auto_power_off.cfg - Panneau Mainsail pour l'extinction automatique
# Sauvegardez ce fichier dans ~/printer_data/config/mainsail/auto_power_off.cfg

[include auto_power_off_panel.cfg]

[gcode_macro POWEROFF_STATUS]
description: Affiche l'état du module d'extinction automatique
gcode:
    AUTO_POWEROFF OPTION=STATUS

[gcode_macro POWEROFF_ON]
description: Active l'extinction automatique
gcode:
    AUTO_POWEROFF OPTION=ON

[gcode_macro POWEROFF_OFF]
description: Désactive l'extinction automatique
gcode:
    AUTO_POWEROFF OPTION=OFF

[gcode_macro POWEROFF_START]
description: Démarre le minuteur d'extinction
gcode:
    AUTO_POWEROFF OPTION=START

[gcode_macro POWEROFF_CANCEL]
description: Annule le minuteur d'extinction
gcode:
    AUTO_POWEROFF OPTION=CANCEL

[gcode_macro POWEROFF_NOW]
description: Éteint immédiatement l'imprimante
gcode:
    AUTO_POWEROFF OPTION=NOW
EOF

    cat > $PRINTER_CONFIG_DIR/mainsail/auto_power_off_panel.cfg << 'EOF'
# auto_power_off_panel.cfg - Configuration pour le panneau Mainsail
# Ce fichier est automatiquement inclus par auto_power_off.cfg

[virtual_sdcard]
path: ~/printer_data/gcodes

[display_status]

[pause_resume]

[respond]

[board_pins]

[button auto_poweroff_toggle]
pin: ^!gpio22
press_gcode:
    {% if printer['auto_power_off'].enabled|lower == 'true' %}
        AUTO_POWEROFF OPTION=OFF
    {% else %}
        AUTO_POWEROFF OPTION=ON
    {% endif %}

[button auto_poweroff_start]
pin: ^!gpio23
press_gcode:
    AUTO_POWEROFF OPTION=START

[button auto_poweroff_cancel]
pin: ^!gpio24
press_gcode:
    AUTO_POWEROFF OPTION=CANCEL
    
[menu __main]
type: list
name: Menu principal
items:
    __power_control
    
[menu __main __power_control]
type: list
name: Contrôle Alimentation
items:
    __poweroff_toggle
    __poweroff_start
    __poweroff_cancel
    __poweroff_now
    __poweroff_status
    
[menu __main __power_control __poweroff_toggle]
type: command
name: Extinction: {% if printer['auto_power_off'] is defined and printer['auto_power_off'].enabled|lower == 'true' %}ON{% else %}OFF{% endif %}
gcode:
    {% if printer['auto_power_off'].enabled|lower == 'true' %}
        AUTO_POWEROFF OPTION=OFF
    {% else %}
        AUTO_POWEROFF OPTION=ON
    {% endif %}
    
[menu __main __power_control __poweroff_start]
type: command
enable: {% if printer['auto_power_off'] is defined and printer['auto_power_off'].enabled|lower == 'true' and not printer['auto_power_off'].active|lower == 'true' %}true{% else %}false{% endif %}
name: Démarrer minuteur
gcode:
    AUTO_POWEROFF OPTION=START
    
[menu __main __power_control __poweroff_cancel]
type: command
enable: {% if printer['auto_power_off'] is defined and printer['auto_power_off'].active|lower == 'true' %}true{% else %}false{% endif %}
name: Annuler minuteur
gcode:
    AUTO_POWEROFF OPTION=CANCEL
    
[menu __main __power_control __poweroff_now]
type: command
name: Éteindre maintenant
gcode:
    M117 Extinction dans 3s...
    G4 P1000
    M117 Extinction dans 2s...
    G4 P1000
    M117 Extinction dans 1s...
    G4 P1000
    M117 Extinction maintenant!
    AUTO_POWEROFF OPTION=NOW
    
[menu __main __power_control __poweroff_status]
type: command
name: Afficher statut
gcode:
    AUTO_POWEROFF OPTION=STATUS
EOF
    print_success "Panneau Mainsail créé."
fi

# Demander à l'utilisateur s'il souhaite ajouter la configuration à printer.cfg
print_status "Modification du fichier printer.cfg..."
CONFIG_FILE="$PRINTER_CONFIG_DIR/printer.cfg"

if [ ! -f "$CONFIG_FILE" ]; then
    print_error "Fichier printer.cfg non trouvé à l'emplacement: $CONFIG_FILE"
    print_warning "Vous devrez ajouter manuellement la configuration à votre fichier printer.cfg."
else
    echo "Voulez-vous ajouter automatiquement la configuration au fichier printer.cfg? [o/N]"
    read -r ADD_CONFIG
    
    if [[ "$ADD_CONFIG" =~ ^[oO][uU][iI]?$ ]]; then
        # Vérifier si la section [auto_power_off] existe déjà
        if grep -q "\[auto_power_off\]" "$CONFIG_FILE"; then
            print_warning "La section [auto_power_off] existe déjà dans printer.cfg."
            print_warning "Veuillez vérifier et mettre à jour la configuration manuellement."
        else
            # Ajouter la configuration au fichier
            cat >> "$CONFIG_FILE" << EOF

#
# Configuration Auto Power Off
#
[auto_power_off]
idle_timeout: 600     # Temps d'inactivité en secondes avant extinction (10 minutes)
temp_threshold: 40    # Seuil de température en °C (imprimante considérée comme refroidie)
power_device: psu_control  # Nom de votre périphérique d'alimentation (doit correspondre à la section [power])
auto_poweroff_enabled: True  # Active l'extinction automatique par défaut au démarrage

EOF

            # Ajouter l'inclusion appropriée en fonction de l'interface
            if [ "$UI_TYPE" = "fluidd" ]; then
                echo "[include fluidd/auto_power_off.cfg]  # Inclusion du panneau Fluidd" >> "$CONFIG_FILE"
            elif [ "$UI_TYPE" = "mainsail" ]; then
                echo "[include mainsail/auto_power_off.cfg]  # Inclusion du panneau Mainsail" >> "$CONFIG_FILE"
            else
                echo "[include fluidd/auto_power_off.cfg]  # Inclusion du panneau Fluidd" >> "$CONFIG_FILE"
                echo "[include mainsail/auto_power_off.cfg]  # Inclusion du panneau Mainsail" >> "$CONFIG_FILE"
            fi
            
            print_success "Configuration ajoutée au fichier printer.cfg."
        fi
    else
        print_warning "Configuration non ajoutée. Vous devrez l'ajouter manuellement."
    fi
fi

# Demander à l'utilisateur s'il souhaite redémarrer Klipper
echo "Voulez-vous redémarrer Klipper maintenant pour appliquer les changements? [o/N]"
read -r RESTART_KLIPPER

if [[ "$RESTART_KLIPPER" =~ ^[oO][uU][iI]?$ ]]; then
    print_status "Redémarrage de Klipper..."
    sudo systemctl restart klipper
    print_success "Klipper redémarré."
    
    echo "Patientez quelques secondes pour que Klipper redémarre complètement..."
    sleep 5
    
    # Vérifier si le module a été chargé correctement
    if grep -q "Auto Power Off: Module initialisé" /tmp/klippy.log; then
        print_success "Le module Auto Power Off a été chargé avec succès!"
    else
        print_warning "Vérification du chargement du module impossible. Veuillez vérifier les logs de Klipper."
    fi
else
    print_warning "Klipper n'a pas été redémarré. Veuillez le redémarrer manuellement pour appliquer les changements."
    echo "Commande pour redémarrer: sudo systemctl restart klipper"
fi

echo ""
print_success "Installation terminée !"
echo ""
echo -e "${GREEN}=== Comment utiliser ====${NC}"
echo "1. Le panneau Auto Power Off sera disponible dans l'interface Fluidd/Mainsail"
echo "2. Le module s'activera automatiquement à la fin de chaque impression si configuré ainsi"
echo "3. Commandes GCODE disponibles:"
echo "   - AUTO_POWEROFF ON    - Active globalement la fonction"
echo "   - AUTO_POWEROFF OFF   - Désactive globalement la fonction"
echo "   - AUTO_POWEROFF START - Démarre manuellement le minuteur"
echo "   - AUTO_POWEROFF CANCEL - Annule le minuteur en cours"
echo "   - AUTO_POWEROFF NOW   - Éteint immédiatement l'imprimante"
echo "   - AUTO_POWEROFF STATUS - Affiche l'état détaillé"
echo ""
echo "Si vous rencontrez des problèmes, vérifiez les logs de Klipper avec: tail -f /tmp/klippy.log"
echo ""