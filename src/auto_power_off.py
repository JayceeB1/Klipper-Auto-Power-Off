# auto_power_off.py
# Automatic power off script for 3D printers running Klipper / Script d'extinction automatique pour imprimante 3D sous Klipper
# Place in ~/klipper/klippy/extras/ folder / À placer dans le dossier ~/klipper/klippy/extras/
# Utilise CURL pour les communications avec Moonraker / Uses CURL for Moonraker communications

import logging
import threading
import time
import os
import json
# Remarque: requests n'est plus utilisé, utilisation de subprocess et curl à la place
# Note: requests is no longer used, using subprocess and curl instead

class AutoPowerOff:
    def __init__(self, config):
        # État du périphérique / Device state
        self.device_available = False
        self.device_capabilities = {}
        self.optimal_method = None
        self.force_direct = False
        
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
        self.moonraker_integration = config.getboolean('moonraker_integration', True)  # Moonraker integration / Intégration avec Moonraker
        self.moonraker_url = config.get('moonraker_url', "http://localhost:7125")  # Moonraker URL / URL de Moonraker

        # Diagnostic mode parameters / Paramètres du mode diagnostique
        self.diagnostic_mode = config.getboolean('diagnostic_mode', False)  # Enable diagnostic logging / Activer la journalisation de diagnostic
        self.power_off_retries = config.getint('power_off_retries', 3)  # Number of retry attempts / Nombre de tentatives
        self.power_off_retry_delay = config.getint('power_off_retry_delay', 2)  # Delay between retries in seconds / Délai entre les tentatives en secondes

        # Dry run mode / Mode simulation
        self.dry_run_mode = config.getboolean('dry_run_mode', False)  # Default is real power off / Par défaut, extinction réelle   

        # Network device settings / Paramètres des périphériques réseau
        self.network_device = config.getboolean('network_device', False)  # Is this a network power device / Est-ce un périphérique d'alimentation réseau
        self.device_address = config.get('device_address', None)  # IP address or hostname / Adresse IP ou nom d'hôte
        self.network_test_attempts = config.getint('network_test_attempts', 3)  # Number of attempts to test connectivity / Nombre de tentatives pour tester la connectivité
        self.network_test_interval = config.getfloat('network_test_interval', 1.0)  # Interval between tests in seconds / Intervalle entre les tests en secondes
            
        # Register for events / S'enregistrer pour les événements
        self.printer.register_event_handler("klippy:ready", self._handle_ready)
        self.printer.register_event_handler("print_stats:complete", self._handle_print_complete)

        # Monitored components configuration / Configuration des composants à surveiller
        self.monitor_hotend = config.getboolean('monitor_hotend', True)
        self.monitor_bed = config.getboolean('monitor_bed', True)
        self.monitor_chamber = config.getboolean('monitor_chamber', False)
            
        # State variables / Variables d'état
        self.shutdown_timer = None
        self.is_checking_temp = False
        self.countdown_end = 0
        self.last_temps = {"hotend": 0, "bed": 0}

        # État du périphérique / Device state
        self.device_available = False
        self.device_capabilities = {}
        self.optimal_method = None
        self.force_direct = False
        self._shutdown_in_progress = False  # Flag pour suivre l'état d'extinction / Flag to track shutdown state      
        
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

    def _check_device_capabilities(self):
        """
        Check and discover the capabilities of the power device
        Vérifie et découvre les capacités du périphérique d'alimentation
        """
        if not self.device_available:
            self._diagnostic_log("Cannot check capabilities, device not available", level="warning")
            return
        
        self.device_capabilities = {
            'set_power': False,
            'turn_off': False,
            'power_off': False,
            'cmd_off': False,
            'moonraker_available': self.moonraker_integration
        }
        
        try:
            device_name = f'power {self.power_device}'
            power_device = self.printer.lookup_object(device_name)
            
            # Check available methods / Vérifier les méthodes disponibles
            self.device_capabilities['set_power'] = hasattr(power_device, 'set_power')
            self.device_capabilities['turn_off'] = hasattr(power_device, 'turn_off')
            self.device_capabilities['power_off'] = hasattr(power_device, 'power_off')
            
            # Check GCODE method / Vérifier la méthode GCODE
            try:
                gcode = self.printer.lookup_object('gcode')
                # Check if the POWER_OFF command exists / Vérifier si la commande POWER_OFF existe
                handler = gcode.get_command_handler().get("POWER_OFF")
                self.device_capabilities['cmd_off'] = handler is not None
            except Exception as e:
                self._diagnostic_log(f"Error checking GCODE capabilities: {str(e)}", level="warning")
            
            # Log detected capabilities / Journaliser les capacités détectées
            self._diagnostic_log(f"Device capabilities: {self.device_capabilities}", level="info")
            
            # Determine optimal power off method / Déterminer la méthode optimale d'extinction
            if self.device_capabilities['set_power']:
                self.optimal_method = 'set_power'
            elif self.device_capabilities['turn_off']:
                self.optimal_method = 'turn_off'
            elif self.device_capabilities['power_off']:
                self.optimal_method = 'power_off'
            elif self.device_capabilities['cmd_off']:
                self.optimal_method = 'cmd_off'
            elif self.device_capabilities['moonraker_available']:
                self.optimal_method = 'moonraker'
            else:
                self.optimal_method = None
                self._diagnostic_log("No viable power off method detected!", level="error")
            
            return True
        except Exception as e:
            self.logger.error(self.get_text("error_checking_capabilities", error=str(e)))
            self._diagnostic_log(f"Exception during capability check: {str(e)}", level="error", data=e)
            return False

    def _verify_power_device(self):
        """
        Verify that the configured power device exists
        Vérifie que le périphérique d'alimentation configuré existe
        """
        self.device_available = False
        
        # Si l'intégration Moonraker est activée, ne pas essayer d'accéder au périphérique via Klipper
        if self.moonraker_integration:
            # On fera la vérification plus tard, lors de l'utilisation
            self._diagnostic_log(f"Using device '{self.power_device}' via Moonraker integration", level="info")
            self.device_available = True
            return True
        
        # Uniquement pour les périphériques contrôlés directement par Klipper (sans Moonraker)
        try:
            device_name = f'power {self.power_device}'
            power_device = self.printer.lookup_object(device_name, None)
            
            if power_device is None:
                self.logger.error(self.get_text("power_device_not_found", device=self.power_device))
                self._notify_user("power_device_not_found", device=self.power_device)
                return False
            
            self.device_available = True
            self._check_device_capabilities()
            self._diagnostic_log(f"Power device '{self.power_device}' found", level="info")
            return True
        except Exception as e:
            self.logger.error(self.get_text("error_verifying_device", error=str(e), device=self.power_device))
            self._diagnostic_log(f"Exception during power device verification: {str(e)}", level="error", data=e)
            return False
        
    def _power_off_dry_run(self):
        """
        Simulate power off for testing purposes
        Simule l'extinction à des fins de test
        """
        self.logger.info(self.get_text("dry_run_power_off"))
        
        # Log all the actions that would happen / Journaliser toutes les actions qui se produiraient
        if self.moonraker_integration and not self.force_direct:
            self._diagnostic_log("DRY RUN: Would use Moonraker API for power off", level="info")
        else:
            self._diagnostic_log("DRY RUN: Would use direct Klipper method", level="info")
            
        if self.optimal_method:
            self._diagnostic_log(f"DRY RUN: Would use {self.optimal_method} method", level="info")
        
        # Notify the user / Notifier l'utilisateur
        self._notify_user("dry_run_power_off")
        
        # Return success / Retourner succès
        return True
    
    def _test_network_device(self):
        """
        Test if a network device is reachable
        Teste si un périphérique réseau est accessible
        """
        if not self.network_device or not self.device_address:
            # Not a network device or no address provided / Pas un périphérique réseau ou pas d'adresse fournie
            return True
        
        import socket
        import time
        
        self._diagnostic_log(f"Testing connectivity to network device: {self.device_address}", level="info")
        
        for attempt in range(self.network_test_attempts):
            try:
                # Try to connect to the device / Essayer de se connecter au périphérique
                # Use a default port, as we only need to check if the host is reachable
                # Utiliser un port par défaut, car nous avons juste besoin de vérifier si l'hôte est accessible
                port = 80  # A commonly open port / Un port couramment ouvert
                
                # Create a socket with a timeout / Créer un socket avec un timeout
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2.0)  # 2 seconds timeout / 2 secondes de timeout
                
                # Try to connect / Essayer de se connecter
                self._diagnostic_log(f"Attempt {attempt+1}/{self.network_test_attempts}: Connecting to {self.device_address}:{port}", level="debug")
                result = sock.connect_ex((self.device_address, port))
                sock.close()
                
                if result == 0:
                    self._diagnostic_log(f"Successfully connected to {self.device_address}", level="info")
                    return True
                else:
                    self._diagnostic_log(f"Failed to connect to {self.device_address}, error code: {result}", level="warning")
                    
            except socket.error as e:
                self._diagnostic_log(f"Socket error connecting to {self.device_address}: {str(e)}", level="warning")
            
            # Wait before next attempt / Attendre avant la prochaine tentative
            if attempt < self.network_test_attempts - 1:
                self._diagnostic_log(f"Waiting {self.network_test_interval}s before next attempt", level="debug")
                time.sleep(self.network_test_interval)
        
        # All attempts failed / Toutes les tentatives ont échoué
        self.logger.error(self.get_text("network_device_unreachable", device=self.device_address, attempts=self.network_test_attempts))
        self._notify_user("network_device_unreachable", device=self.device_address, attempts=self.network_test_attempts)
        return False

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
            "diagnostic_mode_enabled": "Diagnostic mode enabled. Detailed logging activated.",
            "diagnostic_mode_disabled": "Diagnostic mode disabled.",
            "power_off_direct_attempt": "Attempting direct power off method"
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
        # Vérifier si l'objet existe déjà avant de l'ajouter
        try:
            self.printer.lookup_object("auto_power_off")
            # L'objet existe déjà, ne rien faire
        except self.printer.config_error:
            # L'objet n'existe pas encore, l'ajouter
            self.printer.add_object("auto_power_off", self)
    
    def _handle_ready(self):
        """Called when Klipper is ready / Appelé quand Klipper est prêt"""
        self.logger.info(self.get_text("module_initialized"))
        
        # Verify that the power device exists / Vérifier que le périphérique d'alimentation existe
        if self._verify_power_device():
            self.logger.info(self.get_text("power_device_ready", device=self.power_device))
        else:
            self.logger.warning(self.get_text("power_device_not_available", device=self.power_device))
        
        # Set up periodic temperature checker / Mise en place du vérificateur de température périodique
        self.reactor.register_timer(self._update_temps, self.reactor.monotonic() + 1)
    
    def _handle_print_complete(self):
        """
        Called when print is complete / Appelé quand l'impression est terminée
        
        Note: This replaces the now deprecated Moonraker 'off_when_job_complete' functionality
        with a more intelligent approach that checks temperatures and allows cooling before shutdown.
        
        Note (FR): Ceci remplace la fonctionnalité 'off_when_job_complete' de Moonraker (maintenant obsolète)
        avec une approche plus intelligente qui vérifie les températures et permet le refroidissement avant l'extinction.
        """
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
   

    def _check_print_status_via_moonraker(self):
        """Vérifier l'état d'impression via l'API Moonraker"""
        if not self.moonraker_integration:
            return None
            
        import subprocess
        import json
        
        try:
            # Vérifier l'état d'impression via l'API Moonraker avec curl
            base_url = self.moonraker_url.rstrip('/')
            curl_command = f'curl -s "{base_url}/printer/objects/query?print_stats=state"'
            
            # Exécuter la commande curl
            result = subprocess.run(curl_command, shell=True, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if 'result' in data and 'status' in data['result']:
                    state = data['result']['status'].get('print_stats', {}).get('state')
                    self._diagnostic_log(f"Moonraker print state: {state}", level="info")
                    return state
        except Exception as e:
            self._diagnostic_log(f"Error checking print status via Moonraker: {str(e)}", level="warning")
        
        return None

    def _check_conditions(self, eventtime):
        """Check if conditions for power off are met / Vérifie si les conditions pour éteindre sont remplies"""
        # Vérifier si le MCU est connecté / Check if MCU is connected
        if not self._is_mcu_connected():
            # Ne pas journaliser d'avertissement ici car cette fonction est appelée fréquemment
            # Don't log warning here as this function is called frequently
            return eventtime + 1.0

        # Check current print state / Vérifier l'état d'impression actuel
        print_stats = self.printer.lookup_object('print_stats', None)
        
        if print_stats:
            state = print_stats.get_status(eventtime)['state']
            if state in ['printing', 'paused']:
                self.logger.info(self.get_text("print_in_progress"))
                return self.reactor.NEVER
        try:
            gcode_move = self.printer.lookup_object('gcode_move')
            if gcode_move and gcode_move.get_status(eventtime).get('is_printing', False):
                self.logger.info(self.get_text("print_in_progress"))
                return self.reactor.NEVER
        except Exception as e:
            self._diagnostic_log(f"Error checking gcode_move: {str(e)}", level="warning") 

        # Vérification supplémentaire via Moonraker si disponible
        if self.moonraker_integration:
            moonraker_state = self._check_print_status_via_moonraker()
            if moonraker_state in ['printing', 'paused']:
                self.logger.info(self.get_text("print_in_progress_moonraker", state=moonraker_state))
                return self.reactor.NEVER

        # Check if printer is truly idle / Vérifier si l'imprimante est vraiment inactive
        idle_timeout = self.printer.lookup_object('idle_timeout')
        if idle_timeout.get_status(eventtime)['state'] != 'Idle':
            self.logger.info(self.get_text("printer_not_idle"))
            return eventtime + 60.0  # Check again in 60 seconds / Vérifier à nouveau dans 60 secondes
        
        # Check temperatures / Vérifier les températures
        heaters = self.printer.lookup_object('heaters')
        max_temp = 0.0
        temps = {}
        
        # Check hotend if enabled / Vérifier l'extrudeur si activé
        if self.monitor_hotend:
            try:
                hotend = self.printer.lookup_object('extruder').get_heater()
                hotend_temp = heaters.get_status(eventtime)[hotend.get_name()]['temperature']
                temps['hotend'] = hotend_temp
                max_temp = max(max_temp, hotend_temp)
            except Exception as e:
                self.logger.warning(f"Unable to get hotend temperature: {str(e)}")
        
        # Check bed if enabled / Vérifier le lit si activé
        if self.monitor_bed:
            try:
                bed = self.printer.lookup_object('heater_bed', None)
                if bed is not None:
                    bed_temp = heaters.get_status(eventtime)[bed.get_heater().get_name()]['temperature']
                    temps['bed'] = bed_temp
                    max_temp = max(max_temp, bed_temp)
            except Exception as e:
                self.logger.warning(f"Unable to get bed temperature: {str(e)}")
        
        # Check chamber if enabled / Vérifier la chambre si activée
        if self.monitor_chamber:
            try:
                chamber = self.printer.lookup_object('temperature_sensor chamber', None)
                if chamber is not None:
                    chamber_temp = chamber.get_status(eventtime)['temperature']
                    temps['chamber'] = chamber_temp
                    max_temp = max(max_temp, chamber_temp)
            except Exception as e:
                self.logger.warning(f"Unable to get chamber temperature: {str(e)}")
        
        # Update last temperatures for status / Mettre à jour les dernières températures pour le statut
        self.last_temps = temps
        
        # Check if max temperature is below threshold / Vérifier si la température maximale est inférieure au seuil
        if max_temp > self.temp_threshold:
            # Format temperature message / Formater le message de température
            temp_msg = ", ".join(f"{key}: {value:.1f}°C" for key, value in temps.items())
            self.logger.info(self.get_text("temperatures_too_high_custom", temp_msg=temp_msg, max_temp=max_temp))
            return eventtime + 60.0  # Check again in 60 seconds / Vérifier à nouveau dans 60 secondes
        
        # All conditions met, power off the printer / Toutes les conditions sont remplies, éteindre l'imprimante
        self._power_off()
        return self.reactor.NEVER
    
    def _is_mcu_connected(self):
        """
        Vérifie si le MCU est connecté et répond aux commandes
        Checks if the MCU is connected and responding to commands
        """
        try:
            # Tentative de vérification de l'état du MCU / Attempt to check MCU status
            mcu = self.printer.lookup_object('mcu', None)
            if mcu is None:
                self._diagnostic_log("MCU object not found", level="warning")
                return False
            if mcu.is_shutdown():
                self._diagnostic_log("MCU is shutdown or disconnected", level="warning")
                return False
            return True
        except Exception as e:
            self._diagnostic_log(f"Error while checking MCU status: {str(e)}", level="warning")
            return False
        
    def _prepare_mcu_for_shutdown(self):
        """
        Prépare le MCU pour une extinction propre
        Prepares the MCU for a clean shutdown
        """
        try:
            # Éviter les actions redondantes / Avoid redundant actions
            if hasattr(self, '_shutdown_in_progress') and self._shutdown_in_progress:
                return
                
            self._shutdown_in_progress = True
            self._diagnostic_log("Préparation du MCU pour l'extinction", level="info")
            
            # Essayer d'éteindre tous les chauffages / Try to turn off all heaters
            try:
                gcode = self.printer.lookup_object('gcode')
                gcode.run_script_from_command("TURN_OFF_HEATERS")
                
                # Petit délai pour permettre au traitement / Small delay to allow processing
                import time
                time.sleep(0.5)
            except Exception as e:
                self._diagnostic_log(f"Erreur lors de la désactivation des chauffages: {str(e)}", 
                                    level="warning")
        except Exception as e:
            self._diagnostic_log(f"Erreur lors de la préparation pour l'extinction: {str(e)}", 
                                level="warning")
    
    def _power_off(self, force_direct=False, diagnostic_mode=None):
        """
        Power off the printer with enhanced error handling and retry mechanism
        Éteint l'imprimante avec une gestion d'erreur améliorée et un mécanisme de nouvelle tentative
        
        Parameters:
        - force_direct: Force direct Klipper method instead of Moonraker API (bypass API)
                        Forcer la méthode directe Klipper au lieu de l'API Moonraker (contourne l'API)
        - diagnostic_mode: Override global diagnostic mode setting if not None
                        Remplacer le paramètre global du mode diagnostic si non None
        """
        try:
            # Vérifier si l'extinction est déjà en cours
            # Check if shutdown is already in progress
            if hasattr(self, '_shutdown_in_progress') and self._shutdown_in_progress:
                self.logger.info("Une extinction est déjà en cours, commande ignorée")
                return
                
            # Vérifier si l'imprimante est déjà arrêtée
            # Check if printer is already shutdown
            if self.printer.is_shutdown():
                self.logger.warning("L'imprimante est déjà arrêtée, abandon de la procédure d'extinction")
                return
                
            self.logger.info(self.get_text("conditions_met"))
            self.force_direct = force_direct
            
            # Ajout de logs pour diagnostiquer les problèmes d'URL et de configuration
            self._diagnostic_log(f"Starting power off process: moonraker_integration={self.moonraker_integration}, " 
                                f"force_direct={force_direct}, device={self.power_device}", level="info")
            
            # Vérifier les URLs Moonraker
            if self.moonraker_integration:
                base_url = self.moonraker_url.rstrip('/')
                power_status_url = f"{base_url}/printer/objects/query?objects=power_devices"
                power_off_url = f"{base_url}/machine/device_power/device?device={self.power_device}&action=off"
                self._diagnostic_log(f"Moonraker URLs: status={power_status_url}, power_off={power_off_url}", level="info")
            
            # Initialiser un flag pour le suivi de l'extinction
            # Initialize a flag for shutdown tracking
            self._shutdown_in_progress = False
            
            # Check if power device is available / Vérifier si le périphérique d'alimentation est disponible
            if not self.device_available:
                self.logger.error(self.get_text("power_device_not_available_for_poweroff", device=self.power_device))
                self._notify_user("power_device_not_available_for_poweroff", device=self.power_device)
                return
            
            # If diagnostic parameter is passed, use it temporarily, otherwise use the global setting
            # Si le paramètre de diagnostic est passé, l'utiliser temporairement, sinon utiliser le paramètre global
            self._diagnostic_mode = diagnostic_mode if diagnostic_mode is not None else self.diagnostic_mode

            # For network devices, test connectivity first / Pour les périphériques réseau, tester d'abord la connectivité
            if self.network_device and not self._test_network_device():
                self.logger.error(self.get_text("network_device_unreachable_poweroff", device=self.device_address))
                self._notify_user("network_device_unreachable_poweroff", device=self.device_address)
                return
            
            # If dry run mode is enabled, simulate power off / Si le mode simulation est activé, simuler l'extinction
            if self.dry_run_mode:
                return self._power_off_dry_run()
            
            # IMPORTANT: Préparer le système pour l'extinction
            # IMPORTANT: Prepare the system for shutdown
            self._prepare_mcu_for_shutdown()
            
            # Ajouter un délai de sécurité pour permettre aux logs d'être écrits
            # Add a safety delay to allow logs to be written
            import time
            time.sleep(1)
            
            # Check if we should use Moonraker's API and not forced to use direct method
            # Vérifier si nous devons utiliser l'API Moonraker et pas forcé d'utiliser la méthode directe
            if self.moonraker_integration and not force_direct:
                self._diagnostic_log("Using Moonraker API for power off", level="info")
                self._power_off_via_moonraker(max_retries=self.power_off_retries, retry_delay=self.power_off_retry_delay)
            else:
                method = "direct (forced)" if force_direct else "direct"
                self._diagnostic_log(f"Using {method} Klipper method for power off", level="info")
                self._power_off_direct()
        except Exception as e:
            self.logger.error(f"Unhandled exception during power off: {str(e)}")
            self._diagnostic_log(f"Power off exception details: {str(e)}", level="error", data=e)
            self._shutdown_in_progress = False
            # Ne pas propager l'exception plus loin / Don't propagate exception further
            return

    def _diagnostic_log(self, message, level="debug", data=None):
        """
        Log diagnostic information if diagnostic mode is enabled
        Journalise les informations de diagnostic si le mode diagnostic est activé
        
        Parameters:
        - message: Message to log / Message à journaliser
        - level: Log level (debug, info, warning, error) / Niveau de journal
        - data: Additional data to log / Données supplémentaires à journaliser
        """
        # Always log errors regardless of diagnostic mode
        # Toujours journaliser les erreurs quel que soit le mode diagnostic
        if level == "error":
            self.logger.error(message)
            if data:
                self.logger.error(f"Error details: {data}")
            return
                
        # For other levels, only log if in diagnostic mode
        # Pour les autres niveaux, journaliser uniquement en mode diagnostic
        if hasattr(self, '_diagnostic_mode') and self._diagnostic_mode:
            log_method = getattr(self.logger, level, self.logger.info)
            log_method(f"DIAGNOSTIC: {message}")
            if data:
                log_method(f"DIAGNOSTIC DATA: {data}")
    
    def _power_off_via_moonraker(self, max_retries=3, retry_delay=2):
        """Power off the printer using Moonraker API via curl command"""
        import subprocess
        import time
        import json

        base_url = self.moonraker_url.rstrip('/')
        power_off_command = f'curl -s -X POST "{base_url}/machine/device_power/device?device={self.power_device}&action=off"'
        
        self._diagnostic_log(f"Using curl command: {power_off_command}", level="info")
        
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            self._diagnostic_log(f"Power off attempt {retry_count + 1}/{max_retries}", level="info")
            
            try:
                # Exécuter la commande curl
                result = subprocess.run(power_off_command, shell=True, capture_output=True, text=True, timeout=10)
                
                # Vérifier le résultat
                if result.returncode == 0:
                    try:
                        # Essayer de parser la réponse JSON pour un meilleur diagnostic
                        response_data = json.loads(result.stdout)
                        self._diagnostic_log(f"Curl command response: {response_data}", level="info")
                        
                        # Vérifier si la réponse indique une erreur
                        if 'error' in response_data:
                            error_msg = f"Moonraker API error: {response_data['error']}"
                            self._diagnostic_log(error_msg, level="error")
                            last_error = Exception(error_msg)
                        else:
                            self.logger.info(self.get_text("powered_off_moonraker"))
                            self._notify_user("power_off_success")
                            self.state = "off"
                            return
                    except json.JSONDecodeError:
                        # Si la réponse n'est pas du JSON valide mais que curl a réussi, considérer comme un succès
                        self._diagnostic_log(f"Non-JSON response but curl successful: {result.stdout[:200]}", level="info")
                        self.logger.info(self.get_text("powered_off_moonraker"))
                        self._notify_user("power_off_success")
                        self.state = "off"
                        return
                else:
                    error_msg = f"Curl command failed (code {result.returncode}): {result.stderr}"
                    self._diagnostic_log(error_msg, level="error")
                    last_error = Exception(error_msg)
            except subprocess.TimeoutExpired:
                error_msg = "Curl command timed out"
                self._diagnostic_log(error_msg, level="error")
                last_error = Exception(error_msg)
            except Exception as e:
                error_msg = f"Error executing curl command: {str(e)}"
                self._diagnostic_log(error_msg, level="error")
                last_error = e
                
            retry_count += 1
            if retry_count < max_retries:
                self._diagnostic_log(f"Retrying in {retry_delay} seconds...", level="info")
                time.sleep(retry_delay)
        
        # Si on arrive ici, toutes les tentatives ont échoué
        error_message = str(last_error) if last_error else "Unknown error"
        self.logger.error(self.get_text("error_moonraker_all_retries_failed", 
                                    retries=max_retries, 
                                    error=error_message))
        
        # Notify user about failure and fallback
        self._notify_user("moonraker_retries_failed")
        
        # Fallback to direct method
        self.logger.info(self.get_text("falling_back_to_direct"))
        try:
            self._prepare_mcu_for_shutdown()
            time.sleep(1)
            self._power_off_direct()
        except Exception as e:
            self.logger.error(f"Direct method also failed: {str(e)}")
            self.state = "error"
                
    def _power_off_direct(self):
        """
        Power off the printer using direct Klipper control methods
        Éteint l'imprimante en utilisant les méthodes de contrôle directes de Klipper
        """
        try:
            # Vérifier si l'imprimante est déjà arrêtée / Check if printer is already shutdown
            if self.printer.is_shutdown():
                self.logger.warning("Printer is already shutdown, cannot execute power off command")
                return
                
            if not self.device_available:
                self.logger.error(self.get_text("power_device_not_available_for_poweroff", device=self.power_device))
                self._notify_user("power_device_not_available_for_poweroff", device=self.power_device)
                return
            
            # Try to lookup power device, but handle errors gracefully
            try:
                device_name = f'power {self.power_device}'
                self._diagnostic_log(f"Looking up power device: {device_name}", level="info")
                power_device = self.printer.lookup_object(device_name)
                
                # Make sure we have checked capabilities / S'assurer qu'on a vérifié les capacités
                if not hasattr(self, 'optimal_method') or self.optimal_method is None:
                    self._check_device_capabilities()
                
                # Use the optimal method determined during capability check
                # Utiliser la méthode optimale déterminée pendant la vérification des capacités
                if self.optimal_method == 'set_power':
                    self._diagnostic_log("Using set_power(0) method")
                    power_device.set_power(0)
                    self.logger.info(self.get_text("powered_off_set_power"))
                    self._notify_user("power_off_success")
                elif self.optimal_method == 'turn_off':
                    self._diagnostic_log("Using turn_off() method")
                    power_device.turn_off()
                    self.logger.info(self.get_text("powered_off_turn_off"))
                    self._notify_user("power_off_success")
                elif self.optimal_method == 'power_off':
                    self._diagnostic_log("Using power_off() method")
                    power_device.power_off()
                    self.logger.info(self.get_text("powered_off_power_off"))
                    self._notify_user("power_off_success")
                elif self.optimal_method == 'cmd_off':
                    self._diagnostic_log("Using GCODE POWER_OFF command")
                    gcode = self.printer.lookup_object('gcode')
                    gcode.run_script_from_command(f"POWER_OFF {self.power_device}")
                    self.logger.info(self.get_text("powered_off_gcode"))
                    self._notify_user("power_off_success")
                else:
                    self.logger.error(self.get_text("no_power_off_method"))
                    self._notify_user("no_power_off_method")
                self.state = "off"
                
            except self.printer.config_error as e:
                # Device not found in Klipper but might be in Moonraker
                self.logger.warning(f"Power device not found in Klipper: {str(e)}")
                self._diagnostic_log(f"Power device lookup failed: {str(e)}", level="warning")
                
                # Fall back to use GCODE POWER_OFF if available
                try:
                    gcode = self.printer.lookup_object('gcode')
                    self._diagnostic_log("Using GCODE POWER_OFF command as fallback", level="info")
                    gcode.run_script_from_command(f"POWER_OFF {self.power_device}")
                    self.logger.info(self.get_text("powered_off_gcode"))
                    self._notify_user("power_off_success")
                    self.state = "off"
                    return
                except Exception as gcode_error:
                    self.logger.error(f"Failed to use GCODE POWER_OFF command: {str(gcode_error)}")
                    self._notify_user("power_off_failed", error="Could not find power device in Klipper")
                    self.state = "error"
                    return
            
            except Exception as e:
                # Si c'est un type d'erreur expected lors de l'extinction (MCU déconnecté)
                # If it's an expected error type during shutdown (MCU disconnected)
                error_str = str(e).lower()
                if (
                    "command request" in error_str or 
                    "shutdown" in error_str or 
                    "disconnected" in error_str
                ):
                    self._diagnostic_log("Extinction normale avec déconnexion MCU détectée", level="info")
                    self.state = "off"
                    return
                # Pour les autres erreurs, c'est un problème réel
                # For other errors, it's a real problem
                self.logger.error(self.get_text("error_powering_off", error=str(e)))
                self._diagnostic_log(f"Error details: {str(e)}", level="error", data=e)
                self._notify_user("power_off_failed", error=str(e))
                self.state = "error"
                
        except Exception as e:
            error_str = str(e).lower()
            if (
                "command request" in error_str or 
                "shutdown" in error_str or 
                "disconnected" in error_str
            ):
                self._diagnostic_log("Extinction normale avec déconnexion MCU détectée", level="info")
                self.state = "off"
                return
            self.logger.error(f"Unhandled exception during direct power off: {str(e)}")
            self._diagnostic_log(f"Direct power off exception details: {str(e)}", level="error", data=e)
            self.state = "error"
            return

    def _notify_user(self, message_key, **kwargs):
        """
        Send notification to user via GCODE response
        Envoyer une notification à l'utilisateur via une réponse GCODE
        
        Parameters:
        - message_key: Key for the message in translations / Clé pour le message dans les traductions
        - kwargs: Format parameters for the message / Paramètres de formatage pour le message
        """
        # Vérifier si le MCU est connecté / Check if MCU is connected
        if not self._is_mcu_connected():
            # Simplement journaliser le message au lieu d'essayer de l'envoyer à l'utilisateur
            # Simply log the message instead of trying to send it to the user
            message = self.get_text(message_key, **kwargs)
            self.logger.info(f"User notification (not sent due to MCU state): {message}")
            return


        try:
            # Get message text from translations
            # Obtenir le texte du message depuis les traductions
            message = self.get_text(message_key, **kwargs)
            
            # Try to send GCODE message to display to user
            # Essayer d'envoyer un message GCODE à afficher à l'utilisateur
            gcode = self.printer.lookup_object('gcode')
            gcode.respond_info(message)
            
            # Also try to send to the display if available
            # Essayer aussi d'envoyer à l'écran si disponible
            try:
                display = self.printer.lookup_object('display', None)
                if display:
                    self._diagnostic_log("Sending notification to display")
                    # Format message for display (shorter)
                    # Formater le message pour l'affichage (plus court)
                    short_msg = message[:40] + "..." if len(message) > 40 else message
                    gcode.run_script_from_command(f"M117 {short_msg}")
            except Exception as display_err:
                self._diagnostic_log(f"Could not send to display: {str(display_err)}")
                
        except Exception as e:
            # Just log this error, don't try to notify about notification failure
            # Journaliser cette erreur, ne pas essayer de notifier d'un échec de notification
            self.logger.warning(f"Failed to send notification to user: {str(e)}")
    
    def _update_temps(self, eventtime):
        """Update temperatures for status API / Met à jour les températures pour l'API de status"""
        try:
            temps = {}
            
            # Méthode simple et directe pour récupérer les températures
            # Ces informations sont visibles dans les statistiques de Klipper
            try:
                extruder = self.printer.lookup_object('extruder')
                if extruder and hasattr(extruder, 'get_status'):
                    status = extruder.get_status(eventtime)
                    if 'temperature' in status:
                        temps['hotend'] = status['temperature']
            except Exception as e:
                self.logger.debug(f"Error getting extruder temp: {str(e)}")
                
            try:
                heater_bed = self.printer.lookup_object('heater_bed')
                if heater_bed and hasattr(heater_bed, 'get_status'):
                    status = heater_bed.get_status(eventtime)
                    if 'temperature' in status:
                        temps['bed'] = status['temperature']
            except Exception as e:
                self.logger.debug(f"Error getting bed temp: {str(e)}")
            
            # Valeurs par défaut si non trouvées
            if 'hotend' not in temps:
                # Récupérer de manière alternative via les statistiques
                try:
                    stats = self.printer.lookup_object('extruder').stats(eventtime)
                    if 'temp' in stats:
                        temps['hotend'] = stats['temp']
                except:
                    temps['hotend'] = 0.0
                    
            if 'bed' not in temps:
                # Récupérer de manière alternative via les statistiques
                try:
                    stats = self.printer.lookup_object('heater_bed').stats(eventtime)
                    if 'temp' in stats:
                        temps['bed'] = stats['temp']
                except:
                    temps['bed'] = 0.0
            
            self.last_temps = temps
                
        except Exception as e:
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
            'current_temps': self.last_temps,
            'language': self.lang,
            'diagnostic_mode': self.diagnostic_mode,
            'device_available': self.device_available,
            'dry_run_mode': self.dry_run_mode,
            'optimal_method': self.optimal_method,
            'device_capabilities': self.device_capabilities
        }
        
    cmd_AUTO_POWEROFF_help = "Configure or trigger automatic printer power off / Configure ou déclenche l'extinction automatique de l'imprimante"
    
    def cmd_AUTO_POWEROFF(self, gcmd):
        """GCODE command to configure or trigger automatic power off / Commande GCODE pour configurer ou déclencher l'extinction automatique"""
        # Vérifier si le MCU est connecté pour les commandes qui interagissent avec le matériel
        # Check if MCU is connected for commands that interact with hardware
        option = gcmd.get('OPTION', 'status').lower()

        # Ces options peuvent fonctionner sans MCU / These options can work without MCU
        if option in ['language', 'status', 'diagnostic', 'dryrun']:
            # Traiter ces options normalement / Process these options normally
            pass
        else:
            # Pour les autres options qui interagissent avec le matériel
            # For other options that interact with hardware
            if not self._is_mcu_connected() and option in ['now', 'start']:
                gcmd.respond_info("MCU communication not possible, cannot execute hardware-related command")
                return

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

        elif option == 'diagnostic':
            # Enable or disable diagnostic mode / Activer ou désactiver le mode diagnostic
            diag_mode = gcmd.get_int('VALUE', 1, minval=0, maxval=1)
            self.diagnostic_mode = bool(diag_mode)
            if self.diagnostic_mode:
                gcmd.respond_info(self.get_text("diagnostic_mode_enabled"))
                self.logger.info("Diagnostic mode enabled by user")
            else:
                gcmd.respond_info(self.get_text("diagnostic_mode_disabled"))
                self.logger.info("Diagnostic mode disabled by user")

        elif option == 'dryrun':
            dry_run_value = gcmd.get_int('VALUE', 1, minval=0, maxval=1)
            self.dry_run_mode = bool(dry_run_value)
            if self.dry_run_mode:
                gcmd.respond_info(self.get_text("dry_run_enabled"))
                self.logger.info("Dry run mode enabled by user")
            else:
                gcmd.respond_info(self.get_text("dry_run_disabled"))
                self.logger.info("Dry run mode disabled by user")
                
        else:
            gcmd.respond_info(self.get_text("option_not_recognized"))

def load_config(config):
    return AutoPowerOff(config)