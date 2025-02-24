# auto_power_off.py
# Automatic power off script for 3D printers running Klipper / Script d'extinction automatique pour imprimante 3D sous Klipper
# Place in ~/klipper/klippy/extras/ folder / À placer dans le dossier ~/klipper/klippy/extras/

import logging
import threading
import time
import os

class AutoPowerOff:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        
        # Determine language / Déterminer la langue
        self.lang = self._get_language()
        
        # Configuration parameters / Configuration des paramètres
        self.idle_timeout = config.getfloat('idle_timeout', 600.0)  # Idle time in seconds (10 min default) / Temps d'inactivité en secondes (10 min par défaut)
        self.temp_threshold = config.getfloat('temp_threshold', 40.0)  # Temperature threshold in °C / Seuil de température en °C
        self.power_device = config.get('power_device', 'psu_control')  # Name of your power device / Le nom de votre périphérique d'alimentation
        self.enabled = config.getboolean('auto_poweroff_enabled', False)  # Default enabled/disabled state / État activé/désactivé par défaut
        
        # Register for events / S'enregistrer pour les événements
        self.printer.register_event_handler("klippy:ready", self._handle_ready)
        self.printer.register_event_handler("print_stats:complete", self._handle_print_complete)
        
        # State variables / Variables d'état
        self.shutdown_timer = None
        self.is_checking_temp = False
        self.countdown_end = 0
        self.last_temps = {"hotend": 0, "bed": 0}
        
        # Register gcode commands / Enregistrement pour les commandes gcode
        gcode = self.printer.lookup_object('gcode')
        gcode.register_command('AUTO_POWEROFF', self.cmd_AUTO_POWEROFF,
                              desc=self.cmd_AUTO_POWEROFF_help)
                              
        # Register for Fluidd/Mainsail status API / Enregistrement pour l'API de status Fluidd/Mainsail
        self.printer.register_event_handler("klippy:connect", 
                                           self._handle_connect)
        
        # Logging
        self.logger = logging.getLogger('auto_power_off')
        self.logger.setLevel(logging.INFO)
    
    def _get_language(self):
        """Determine the language to use / Déterminer la langue à utiliser"""
        # Try to detect system language / Essayer de détecter la langue du système
        try:
            lang = os.environ.get('LANG', '').split('.')[0].lower()
            if lang.startswith('fr'):
                return 'fr'
        except:
            pass
        # Default to English / Par défaut en anglais
        return 'en'
    
    def _handle_connect(self):
        """Called on initial connection / Appelé lors de la connexion initiale"""
        # Register the object to make it accessible via API / Enregistrer l'objet pour qu'il soit accessible via l'API
        self.printer.add_object("auto_power_off", self)
    
    def _handle_ready(self):
        """Called when Klipper is ready / Appelé quand Klipper est prêt"""
        if self.lang == 'fr':
            self.logger.info("Auto Power Off: Module initialisé")
        else:
            self.logger.info("Auto Power Off: Module initialized")
        
        # Set up periodic temperature checker / Mise en place du vérificateur de température périodique
        self.reactor.register_timer(self._update_temps, self.reactor.monotonic() + 1)
    
    def _handle_print_complete(self):
        """Called when print is complete / Appelé quand l'impression est terminée"""
        if not self.enabled:
            if self.lang == 'fr':
                self.logger.info("Impression terminée, mais l'extinction automatique est désactivée")
            else:
                self.logger.info("Print complete, but auto power off is disabled")
            return
            
        if self.lang == 'fr':
            self.logger.info("Impression terminée, démarrage du minuteur d'extinction")
        else:
            self.logger.info("Print complete, starting power-off timer")
        
        # Cancel any existing timer / Annuler tout minuteur existant
        if self.shutdown_timer is not None:
            self.reactor.unregister_timer(self.shutdown_timer)
        
        # Start the idle timer / Démarrer le minuteur d'inactivité
        waketime = self.reactor.monotonic() + self.idle_timeout
        self.countdown_end = self.reactor.monotonic() + self.idle_timeout
        self.shutdown_timer = self.reactor.register_timer(self._check_conditions, waketime)
    
    def _check_conditions(self, eventtime):
        """Check if conditions for power off are met / Vérifie si les conditions pour éteindre sont remplies"""
        # Check current print state / Vérifier l'état d'impression actuel
        print_stats = self.printer.lookup_object('print_stats', None)
        if print_stats and print_stats.get_status(eventtime)['state'] != 'complete':
            if self.lang == 'fr':
                self.logger.info("Impression en cours ou reprise, annulation de l'extinction")
            else:
                self.logger.info("Print in progress or resumed, canceling shutdown")
            return self.reactor.NEVER
        
        # Check if printer is truly idle / Vérifier si l'imprimante est vraiment inactive
        idle_timeout = self.printer.lookup_object('idle_timeout')
        if idle_timeout.get_status(eventtime)['state'] != 'Idle':
            if self.lang == 'fr':
                self.logger.info("Imprimante non inactive, report de l'extinction")
            else:
                self.logger.info("Printer not idle, postponing shutdown")
            return eventtime + 60.0  # Check again in 60 seconds / Vérifier à nouveau dans 60 secondes
        
        # Check temperatures / Vérifier les températures
        heaters = self.printer.lookup_object('heaters')
        hotend = self.printer.lookup_object('extruder').get_heater()
        try:
            bed = self.printer.lookup_object('heater_bed').get_heater()
            bed_temp = heaters.get_status(eventtime)[bed.get_name()]['temperature']
        except:
            bed_temp = 0.0
            
        hotend_temp = heaters.get_status(eventtime)[hotend.get_name()]['temperature']
        
        if max(hotend_temp, bed_temp) > self.temp_threshold:
            if self.lang == 'fr':
                self.logger.info(f"Températures trop élevées (Hotend: {hotend_temp:.1f}, Bed: {bed_temp:.1f}), report de l'extinction")
            else:
                self.logger.info(f"Temperatures too high (Hotend: {hotend_temp:.1f}, Bed: {bed_temp:.1f}), postponing shutdown")
            return eventtime + 60.0  # Check again in 60 seconds / Vérifier à nouveau dans 60 secondes
        
        # All conditions met, power off the printer / Toutes les conditions sont remplies, éteindre l'imprimante
        self._power_off()
        return self.reactor.NEVER
    
    def _power_off(self):
        """Power off the printer / Éteindre l'imprimante"""
        if self.lang == 'fr':
            self.logger.info("Conditions remplies, extinction de l'imprimante")
        else:
            self.logger.info("Conditions met, powering off the printer")
        
        try:
            # Access the power controller / Accéder au contrôleur d'alimentation
            power_device = self.printer.lookup_object('power ' + self.power_device)
            
            # Try to use the standard method / Essayer d'utiliser la méthode standard
            if hasattr(power_device, 'set_power'):
                power_device.set_power(0)
                if self.lang == 'fr':
                    self.logger.info("Imprimante éteinte avec succès (méthode set_power)")
                else:
                    self.logger.info("Printer powered off successfully (set_power method)")
            # Alternative for other device types / Alternative pour d'autres types de périphériques
            elif hasattr(power_device, 'turn_off'):
                power_device.turn_off()
                if self.lang == 'fr':
                    self.logger.info("Imprimante éteinte avec succès (méthode turn_off)")
                else:
                    self.logger.info("Printer powered off successfully (turn_off method)")
            # Try with standard Moonraker API call / Essayer avec un appel API standard Moonraker
            else:
                # Use a generic command via GCODE / Utiliser une commande générique via GCODE
                gcode = self.printer.lookup_object('gcode')
                gcode.run_script_from_command(f"POWER_OFF {self.power_device}")
                if self.lang == 'fr':
                    self.logger.info("Imprimante éteinte avec succès (via GCODE)")
                else:
                    self.logger.info("Printer powered off successfully (via GCODE)")
                
        except Exception as e:
            if self.lang == 'fr':
                self.logger.error(f"Erreur lors de l'extinction: {str(e)}")
            else:
                self.logger.error(f"Error during power off: {str(e)}")
    
    def _update_temps(self, eventtime):
        """Update temperatures for status API / Met à jour les températures pour l'API de status"""
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
            if self.lang == 'fr':
                self.logger.error(f"Erreur lors de la mise à jour des températures: {str(e)}")
            else:
                self.logger.error(f"Error updating temperatures: {str(e)}")
            
        # Schedule next update in 1 second / Planifier la prochaine mise à jour dans 1 seconde
        return eventtime + 1.0
        
    def get_status(self, eventtime):
        """Get status for Fluidd/Mainsail API / Obtenir le statut pour l'API Fluidd/Mainsail"""
        time_left = max(0, self.countdown_end - eventtime) if self.shutdown_timer is not None else 0
        
        return {
            'enabled': self.enabled,
            'active': self.shutdown_timer is not None,
            'countdown': int(time_left),
            'idle_timeout': int(self.idle_timeout),
            'temp_threshold': self.temp_threshold,
            'current_temps': self.last_temps
        }
    
    cmd_AUTO_POWEROFF_help = "Configure or trigger automatic printer power off / Configure ou déclenche l'extinction automatique de l'imprimante"
    
    def cmd_AUTO_POWEROFF(self, gcmd):
        """GCODE command to configure or trigger automatic power off / Commande GCODE pour configurer ou déclencher l'extinction automatique"""
        option = gcmd.get('OPTION', 'status')
        
        if option.lower() == 'on':
            # Globally enable auto power off / Activer globalement l'extinction automatique
            self.enabled = True
            if self.lang == 'fr':
                gcmd.respond_info("Extinction automatique activée globalement")
            else:
                gcmd.respond_info("Auto power off globally enabled")
                
        elif option.lower() == 'off':
            # Globally disable auto power off / Désactiver globalement l'extinction automatique
            self.enabled = False
            if self.shutdown_timer is not None:
                self.reactor.unregister_timer(self.shutdown_timer)
                self.shutdown_timer = None
            if self.lang == 'fr':
                gcmd.respond_info("Extinction automatique désactivée globalement")
            else:
                gcmd.respond_info("Auto power off globally disabled")
                
        elif option.lower() == 'now':
            # Trigger power off immediately / Déclencher l'extinction immédiatement
            if self.lang == 'fr':
                gcmd.respond_info("Extinction de l'imprimante...")
            else:
                gcmd.respond_info("Powering off printer...")
            # Small delay to allow gcode response to be sent / Petit délai pour permettre à la réponse de gcode d'être envoyée
            self.reactor.register_callback(lambda e: self._power_off())
        
        elif option.lower() == 'start':
            # Start the idle timer / Démarrer le minuteur d'inactivité
            if not self.enabled:
                if self.lang == 'fr':
                    gcmd.respond_info("L'extinction automatique est désactivée globalement")
                else:
                    gcmd.respond_info("Auto power off is globally disabled")
                return
            if self.shutdown_timer is None:
                waketime = self.reactor.monotonic() + self.idle_timeout
                self.countdown_end = self.reactor.monotonic() + self.idle_timeout
                self.shutdown_timer = self.reactor.register_timer(self._check_conditions, waketime)
                if self.lang == 'fr':
                    gcmd.respond_info("Minuteur d'extinction automatique démarré")
                else:
                    gcmd.respond_info("Auto power off timer started")
            else:
                if self.lang == 'fr':
                    gcmd.respond_info("Le minuteur d'extinction automatique est déjà actif")
                else:
                    gcmd.respond_info("Auto power off timer already active")
                
        elif option.lower() == 'cancel':
            # Cancel the idle timer / Annuler le minuteur d'inactivité
            if self.shutdown_timer is not None:
                self.reactor.unregister_timer(self.shutdown_timer)
                self.shutdown_timer = None
                if self.lang == 'fr':
                    gcmd.respond_info("Minuteur d'extinction automatique annulé")
                else:
                    gcmd.respond_info("Auto power off timer canceled")
            else:
                if self.lang == 'fr':
                    gcmd.respond_info("Aucun minuteur d'extinction automatique actif")
                else:
                    gcmd.respond_info("No active auto power off timer")
            
        elif option.lower() == 'status':
            # Display current status / Afficher l'état actuel
            if self.lang == 'fr':
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
                enabled_status = "enabled" if self.enabled else "disabled"
                timer_status = "active" if self.shutdown_timer is not None else "inactive"
                temps = f"Hotend: {self.last_temps['hotend']:.1f}°C, Bed: {self.last_temps['bed']:.1f}°C"
                
                time_left = max(0, self.countdown_end - self.reactor.monotonic())
                countdown = f"{int(time_left / 60)}m {int(time_left % 60)}s" if self.shutdown_timer is not None else "N/A"
                
                gcmd.respond_info(
                    f"Auto power off: {enabled_status}\n"
                    f"Timer: {timer_status} (Remaining: {countdown})\n"
                    f"Current temperatures: {temps}\n"
                    f"Temperature threshold: {self.temp_threshold}°C\n"
                    f"Idle timeout: {int(self.idle_timeout / 60)} minutes"
                )
            
        else:
            if self.lang == 'fr':
                gcmd.respond_info("Option non reconnue. Utilisez ON, OFF, START, CANCEL, NOW ou STATUS")
            else:
                gcmd.respond_info("Unrecognized option. Use ON, OFF, START, CANCEL, NOW, or STATUS")

def load_config(config):
    return AutoPowerOff(config)