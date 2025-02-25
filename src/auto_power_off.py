# auto_power_off.py
# Automatic power off script for 3D printers running Klipper / Script d'extinction automatique pour imprimante 3D sous Klipper
# Place in ~/klipper/klippy/extras/ folder / À placer dans le dossier ~/klipper/klippy/extras/

import logging
import threading
import time
import os
import json

class AutoPowerOff:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        
        # Set up logging first / Configuration du logging en premier
        self.logger = logging.getLogger('auto_power_off')
        self.logger.setLevel(logging.INFO)
        
        # Language configuration / Configuration de la langue
        self._configure_language(config)
        
        # Load translations / Charger les traductions
        self._load_translations()
        
        # Configuration parameters / Configuration des paramètres
        self.idle_timeout = config.getfloat('idle_timeout', 600.0)  # Idle time in seconds (10 min default) / Temps d'inactivité en secondes (10 min par défaut)
        self.temp_threshold = config.getfloat('temp_threshold', 40.0)  # Temperature threshold in °C / Seuil de température en °C
        self.power_device = config.get('power_device', 'psu_control')  # Name of your power device / Le nom de votre périphérique d'alimentation
        self.enabled = config.getboolean('auto_poweroff_enabled', False)  # Default enabled/disabled state / État activé/désactivé par défaut
        self.moonraker_integration = config.getboolean('moonraker_integration', False)  # Moonraker integration / Intégration avec Moonraker
        self.moonraker_url = config.get('moonraker_url', "http://localhost:7125")  # Moonraker URL / URL de Moonraker
        
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
    
    def _configure_language(self, config):
        """
        Configure language settings using multiple sources
        Configure les paramètres de langue en utilisant plusieurs sources
        """
        # 1. Check explicit config parameter first (highest priority)
        # 1. Vérifier d'abord le paramètre explicite (priorité la plus élevée)
        configured_lang = config.get('language', None)
        if configured_lang == 'auto':
            configured_lang = None
        
        # Get persistent language if saved / Récupérer la langue persistante si enregistrée
        persistent_lang = self._get_persistent_language()
        
        # 2. Check environment variables / Vérifier les variables d'environnement
        env_lang = None
        try:
            # Check both LANG and LANGUAGE env vars / Vérifier les variables d'environnement LANG et LANGUAGE
            for env_var in ['LANG', 'LANGUAGE', 'LC_ALL']:
                if env_var in os.environ and os.environ[env_var]:
                    env_value = os.environ[env_var].split('.')[0].lower()
                    if env_value.startswith('fr'):
                        env_lang = 'fr'
                        break
                    elif env_value.startswith('en'):
                        env_lang = 'en'
                        break
        except Exception as e:
            self.logger.warning(f"Error checking environment language: {str(e)}")
            
        # 3. Check Klipper config files / Vérifier les fichiers de configuration de Klipper
        klipper_lang = self._check_klipper_language_settings()
        
        # 4. Determine language with priority order / Déterminer la langue avec un ordre de priorité
        self.lang = configured_lang or persistent_lang or env_lang or klipper_lang or 'en'
        
        # Validate and normalize language choice / Valider et normaliser le choix de langue
        if self.lang.lower() not in ['en', 'fr']:
            self.logger.warning(f"Unsupported language '{self.lang}'. Defaulting to English.")
            self.lang = 'en'
        else:
            self.lang = self.lang.lower()
        
        # Save language choice for persistence / Sauvegarder le choix de langue pour la persistance
        if configured_lang and configured_lang != persistent_lang:
            self._save_persistent_language(self.lang)
        
        # Log language detection process / Journaliser le processus de détection de langue
        self.logger.info(f"Language detection: config={configured_lang}, "
                        f"persistent={persistent_lang}, env={env_lang}, "
                        f"klipper={klipper_lang}, final={self.lang}")

    def _check_klipper_language_settings(self):
        """
        Check if there's any language preference in Klipper configuration files
        Vérifie s'il y a une préférence de langue dans les fichiers de configuration de Klipper
        """
        try:
            # Try to check for common paths to French config files
            # Essayer de vérifier les chemins courants des fichiers de configuration en français
            config_paths = [
                "~/printer_data/config/mainsail/auto_power_off_fr.cfg",
                "~/printer_data/config/fluidd/auto_power_off_fr.cfg",
                "~/klipper_config/mainsail/auto_power_off_fr.cfg",
                "~/klipper_config/fluidd/auto_power_off_fr.cfg"
            ]
            
            for path in config_paths:
                expanded_path = os.path.expanduser(path)
                if os.path.exists(expanded_path):
                    return 'fr'
        except Exception as e:
            self.logger.warning(f"Error checking Klipper config: {str(e)}")
        
        return None

    def _get_persistent_language(self):
        """
        Get saved language from persistence file
        Obtenir la langue sauvegardée depuis le fichier de persistance
        """
        try:
            persistence_file = os.path.expanduser("~/printer_data/config/auto_power_off_language.conf")
            if os.path.exists(persistence_file):
                with open(persistence_file, 'r') as f:
                    saved_lang = f.read().strip()
                    return saved_lang if saved_lang in ['en', 'fr'] else None
        except Exception as e:
            self.logger.warning(f"Error reading persistent language: {str(e)}")
        
        return None

    def _save_persistent_language(self, language):
        """
        Save language preference to persistence file
        Sauvegarder la préférence de langue dans le fichier de persistance
        """
        try:
            persistence_dir = os.path.expanduser("~/printer_data/config")
            if not os.path.exists(persistence_dir):
                persistence_dir = os.path.expanduser("~/klipper_config")
                if not os.path.exists(persistence_dir):
                    self.logger.warning("Could not find config directory for language persistence")
                    return
                    
            persistence_file = os.path.join(persistence_dir, "auto_power_off_language.conf")
            with open(persistence_file, 'w') as f:
                f.write(language)
            self.logger.info(f"Language preference saved to {persistence_file}")
        except Exception as e:
            self.logger.warning(f"Error saving language preference: {str(e)}")

    def _load_translations(self):
        """
        Load language strings from translation files
        Charger les chaînes de langue à partir des fichiers de traduction
        """
        self.translations = {}
        lang_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'auto_power_off_langs')
        
        try:
            # Fallback to English if translation file doesn't exist
            # Utiliser l'anglais par défaut si le fichier de traduction n'existe pas
            lang_file = os.path.join(lang_dir, f"{self.lang}.json")
            
            if not os.path.exists(lang_file):
                self.logger.warning(f"Translation file {lang_file} not found, falling back to English")
                lang_file = os.path.join(lang_dir, "en.json")
            
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
                
            self.logger.info(f"Loaded {len(self.translations)} translations from {lang_file}")
            
        except Exception as e:
            self.logger.error(f"Error loading translations: {str(e)}. Using hardcoded English strings.")
            # We'll fallback to the hardcoded strings in get_text()
    
    def get_text(self, key, **kwargs):
        """
        Get translated text by key, with optional formatting parameters
        Obtenir le texte traduit par clé, avec paramètres de formatage optionnels
        """
        if key in self.translations:
            text = self.translations[key]
            if kwargs:
                try:
                    return text.format(**kwargs)
                except Exception as e:
                    self.logger.warning(f"Error formatting translation key '{key}': {str(e)}")
                    return text
            return text
        
        # Fallback to hardcoded English strings
        # Retour aux chaînes anglaises codées en dur
        self.logger.warning(f"Missing translation key: {key}")
        
        # Basic English fallbacks for critical messages
        fallbacks = {
            "module_initialized": "Auto Power Off: Module initialized",
            "print_complete_disabled": "Print complete, but auto power off is disabled",
            "print_complete_starting_timer": "Print complete, starting power-off timer",
            "print_in_progress": "Print in progress or resumed, canceling shutdown",
            "printer_not_idle": "Printer not idle, postponing shutdown",
            "temperatures_too_high": "Temperatures too high (Hotend: {hotend_temp:.1f}, Bed: {bed_temp:.1f}), postponing shutdown",
            "conditions_met": "Conditions met, powering off the printer",
            "powered_off_moonraker": "Printer powered off successfully via Moonraker API",
            "error_powering_off": "Error during power off: {error}",
            "powered_off_set_power": "Printer powered off successfully (set_power method)",
            "auto_power_off_enabled": "Auto power off globally enabled",
            "auto_power_off_disabled": "Auto power off globally disabled",
        }
        
        if key in fallbacks:
            text = fallbacks[key]
            if kwargs:
                try:
                    return text.format(**kwargs)
                except:
                    return text
            return text
        
        return f"[{key}]"  # Return the key itself as last resort
    
    def _handle_connect(self):
        """Called on initial connection / Appelé lors de la connexion initiale"""
        # Register the object to make it accessible via API / Enregistrer l'objet pour qu'il soit accessible via l'API
        self.printer.add_object("auto_power_off", self)
    
    def _handle_ready(self):
        """Called when Klipper is ready / Appelé quand Klipper est prêt"""
        self.logger.info(self.get_text("module_initialized"))
        
        # Set up periodic temperature checker / Mise en place du vérificateur de température périodique
        self.reactor.register_timer(self._update_temps, self.reactor.monotonic() + 1)
    
    def _handle_print_complete(self):
        """Called when print is complete / Appelé quand l'impression est terminée"""
        if not self.enabled:
            self.logger.info(self.get_text("print_complete_disabled"))
            return
            
        self.logger.info(self.get_text("print_complete_starting_timer"))
        
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
            self.logger.info(self.get_text("print_in_progress"))
            return self.reactor.NEVER
        
        # Check if printer is truly idle / Vérifier si l'imprimante est vraiment inactive
        idle_timeout = self.printer.lookup_object('idle_timeout')
        if idle_timeout.get_status(eventtime)['state'] != 'Idle':
            self.logger.info(self.get_text("printer_not_idle"))
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
            self.logger.info(self.get_text("temperatures_too_high", 
                                         hotend_temp=hotend_temp, 
                                         bed_temp=bed_temp))
            return eventtime + 60.0  # Check again in 60 seconds / Vérifier à nouveau dans 60 secondes
        
        # All conditions met, power off the printer / Toutes les conditions sont remplies, éteindre l'imprimante
        self._power_off()
        return self.reactor.NEVER
    
    def _power_off(self):
        """Power off the printer / Éteindre l'imprimante"""
        self.logger.info(self.get_text("conditions_met"))
        
        try:
            # Check if we should use Moonraker's API
            if self.moonraker_integration:
                # Use Moonraker API to power off
                import requests
                
                # First, check if device exists
                power_status_url = f"{self.moonraker_url}/printer/objects/query?power_devices={self.power_device}"
                try:
                    status_resp = requests.get(power_status_url)
                    if status_resp.status_code == 200:
                        # Device exists, send power off command
                        power_off_url = f"{self.moonraker_url}/printer/objects/command?command=power_device_off&device={self.power_device}"
                        off_resp = requests.post(power_off_url)
                        
                        if off_resp.status_code == 200:
                            self.logger.info(self.get_text("powered_off_moonraker"))
                        else:
                            raise Exception(f"Moonraker API returned error: {off_resp.status_code}")
                    else:
                        raise Exception(f"Power device '{self.power_device}' not found in Moonraker")
                except Exception as e:
                    # Fall back to direct Klipper method if Moonraker API fails
                    self.logger.warning(f"Error using Moonraker API: {str(e)}. Falling back to Klipper method.")
                    self._use_klipper_power_control()
            else:
                # Use direct Klipper control
                self._use_klipper_power_control()
                    
        except Exception as e:
            self.logger.error(self.get_text("error_powering_off", error=str(e)))

    def _use_klipper_power_control(self):
        """Use Klipper's direct power control methods"""
        try:
            # Access the power controller
            power_device = self.printer.lookup_object('power ' + self.power_device)
            
            # Try to use the standard method
            if hasattr(power_device, 'set_power'):
                power_device.set_power(0)
                self.logger.info(self.get_text("powered_off_set_power"))
            # Alternative for other device types
            elif hasattr(power_device, 'turn_off'):
                power_device.turn_off()
                self.logger.info(self.get_text("powered_off_turn_off"))
            # Try with standard GCODE command
            else:
                gcode = self.printer.lookup_object('gcode')
                gcode.run_script_from_command(f"POWER_OFF {self.power_device}")
                self.logger.info(self.get_text("powered_off_gcode"))
        except Exception as e:
            raise e  # Re-raise the exception for the main error handler
    
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
            self.logger.error(self.get_text("error_updating_temps", error=str(e)))
            
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
            'current_temps': self.last_temps,
            'language': self.lang
        }
    
    cmd_AUTO_POWEROFF_help = "Configure or trigger automatic printer power off / Configure ou déclenche l'extinction automatique de l'imprimante"
    
    def cmd_AUTO_POWEROFF(self, gcmd):
        """GCODE command to configure or trigger automatic power off / Commande GCODE pour configurer ou déclencher l'extinction automatique"""
        option = gcmd.get('OPTION', 'status').lower()
        
        # Added language option / Ajout de l'option de langue
        if option == 'language':
            lang_value = gcmd.get('VALUE', '').lower()
            if lang_value in ['en', 'fr']:
                self.lang = lang_value
                self._save_persistent_language(self.lang)
                self._load_translations()  # Reload translations with new language
                gcmd.respond_info(self.get_text("language_set"))
            else:
                gcmd.respond_info(self.get_text("language_not_recognized", lang_value=lang_value))
            return
        
        if option == 'on':
            # Globally enable auto power off / Activer globalement l'extinction automatique
            self.enabled = True
            gcmd.respond_info(self.get_text("auto_power_off_enabled"))
                
        elif option == 'off':
            # Globally disable auto power off / Désactiver globalement l'extinction automatique
            self.enabled = False
            if self.shutdown_timer is not None:
                self.reactor.unregister_timer(self.shutdown_timer)
                self.shutdown_timer = None
            gcmd.respond_info(self.get_text("auto_power_off_disabled"))
                
        elif option == 'now':
            # Trigger power off immediately / Déclencher l'extinction immédiatement
            gcmd.respond_info(self.get_text("powering_off"))
            # Small delay to allow gcode response to be sent / Petit délai pour permettre à la réponse de gcode d'être envoyée
            self.reactor.register_callback(lambda e: self._power_off())
        
        elif option == 'start':
            # Start the idle timer / Démarrer le minuteur d'inactivité
            if not self.enabled:
                gcmd.respond_info(self.get_text("auto_power_off_globally_disabled"))
                return
            if self.shutdown_timer is None:
                waketime = self.reactor.monotonic() + self.idle_timeout
                self.countdown_end = self.reactor.monotonic() + self.idle_timeout
                self.shutdown_timer = self.reactor.register_timer(self._check_conditions, waketime)
                gcmd.respond_info(self.get_text("timer_started"))
            else:
                gcmd.respond_info(self.get_text("timer_already_active"))
                
        elif option == 'cancel':
            # Cancel the idle timer / Annuler le minuteur d'inactivité
            if self.shutdown_timer is not None:
                self.reactor.unregister_timer(self.shutdown_timer)
                self.shutdown_timer = None
                gcmd.respond_info(self.get_text("timer_canceled"))
            else:
                gcmd.respond_info(self.get_text("no_active_timer"))
            
        elif option == 'status':
            # Display current status / Afficher l'état actuel
            enabled_status = self.get_text("enabled_status" if self.enabled else "disabled_status")
            timer_status = self.get_text("timer_active" if self.shutdown_timer is not None else "timer_inactive")
            
            if self.lang == 'fr':
                temps = f"Buse: {self.last_temps['hotend']:.1f}°C, Lit: {self.last_temps['bed']:.1f}°C"
            else:
                temps = f"Hotend: {self.last_temps['hotend']:.1f}°C, Bed: {self.last_temps['bed']:.1f}°C"
            
            time_left = max(0, self.countdown_end - self.reactor.monotonic())
            countdown = f"{int(time_left / 60)}m {int(time_left % 60)}s" if self.shutdown_timer is not None else "N/A"
            
            gcmd.respond_info(self.get_text("status_template", 
                enabled_status=enabled_status,
                timer_status=timer_status,
                countdown=countdown,
                temps=temps,
                temp_threshold=self.temp_threshold,
                idle_timeout=int(self.idle_timeout / 60)
            ))
            
        else:
            gcmd.respond_info(self.get_text("option_not_recognized"))

def load_config(config):
    return AutoPowerOff(config)