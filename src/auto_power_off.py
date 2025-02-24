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
                              
        # Enregistrement pour l'API de status Fluidd
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
