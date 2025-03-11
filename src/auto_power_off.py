# auto_power_off.py
# Automatic power off script for 3D printers running Klipper / Script d'extinction automatique pour imprimante 3D sous Klipper
# Place in ~/klipper/klippy/extras/ folder / À placer dans le dossier ~/klipper/klippy/extras/

import logging
import threading
import time
import os
import json
import subprocess
import socket
from enum import Enum, auto
from typing import Dict, List, Optional, Union, Any, Tuple, Callable, Set, TypeVar, Generic, Type, cast

__version__ = "2.0.8"  # Module version for update checking

# Définition des énumérations pour les états et méthodes
class PowerOffMethod(Enum):
    """Available methods to power off the power device / Méthodes disponibles pour éteindre le périphérique d'alimentation"""
    SET_POWER = auto()  # Utilise la méthode set_power(0)
    TURN_OFF = auto()   # Utilise la méthode turn_off()
    POWER_OFF = auto()  # Utilise la méthode power_off()
    CMD_OFF = auto()    # Utilise la commande GCODE POWER_OFF
    MOONRAKER = auto()  # Utilise l'API Moonraker
    UNKNOWN = auto()    # Méthode inconnue ou non déterminée

class DeviceState(Enum):
    """Possible states of the power device / États possibles du périphérique d'alimentation"""
    AVAILABLE = auto()    # Périphérique disponible
    UNAVAILABLE = auto()  # Périphérique indisponible
    ERROR = auto()        # Erreur avec le périphérique

class PrinterState(Enum):
    """Possible printer states / États possibles de l'imprimante"""
    IDLE = auto()        # Imprimante inactive
    PRINTING = auto()    # Impression en cours
    PAUSED = auto()      # Impression en pause
    BUSY = auto()        # Imprimante occupée (mais pas en impression)
    SHUTDOWN = auto()    # Imprimante arrêtée
    UNKNOWN = auto()     # État inconnu

class Language(Enum):
    """Supported languages / Langues supportées"""
    ENGLISH = "en"
    FRENCH = "fr"
    # Ajouter de nouvelles langues ici

# Définition des exceptions personnalisées
class PowerOffError(Exception):
    """Base exception for power off errors / Exception de base pour les erreurs d'extinction"""
    pass

class PowerDeviceError(PowerOffError):
    """Exception for errors related to the power device / Exception pour les erreurs liées au périphérique d'alimentation"""
    pass

class PowerDeviceNotFoundError(PowerDeviceError):
    """Exception raised when the power device is not found / Exception levée quand le périphérique d'alimentation est introuvable"""
    pass

class PowerDeviceNotAvailableError(PowerDeviceError):
    """Exception raised when the power device is not available / Exception levée quand le périphérique d'alimentation n'est pas disponible"""
    pass

class NetworkDeviceError(PowerDeviceError):
    """Exception for network device errors / Exception pour les erreurs de périphérique réseau"""
    pass

class NetworkDeviceUnreachableError(NetworkDeviceError):
    """Exception raised when the network device is unreachable / Exception levée quand le périphérique réseau est injoignable"""
    pass

class MoonrakerApiError(PowerOffError):
    """Exception for Moonraker API errors / Exception pour les erreurs d'API Moonraker"""
    pass

class TranslationError(Exception):
    """Exception for translation errors / Exception pour les erreurs de traduction"""
    pass

class MCUError(PowerOffError):
    """Exception for MCU-related errors / Exception pour les erreurs liées au MCU"""
    pass


class AutoPowerOff:
    def __init__(self, config):
        # Device state / État du périphérique
        self.device_state: DeviceState = DeviceState.UNAVAILABLE
        self.device_capabilities: Dict[str, bool] = {}
        self.optimal_method: Optional[PowerOffMethod] = None
        self.force_direct: bool = False

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
        self.idle_timeout: float = config.getfloat('idle_timeout', 600.0)  # Idle time in seconds (10 min default) / Temps d'inactivité en secondes (10 min par défaut)
        self.temp_threshold: float = config.getfloat('temp_threshold', 40.0)  # Temperature threshold in °C / Seuil de température en °C
        self.power_device: str = config.get('power_device', 'psu_control')  # Name of your power device / Nom du périphérique d'alimentation
        self.enabled: bool = config.getboolean('auto_poweroff_enabled', False)  # Default enabled/disabled state / État activé/désactivé par défaut
        self.moonraker_integration: bool = config.getboolean('moonraker_integration', True)  # Moonraker integration / Intégration avec Moonraker
        self.moonraker_url: str = config.get('moonraker_url', "http://localhost:7125")  # Moonraker URL / URL de Moonraker

        # Diagnostic mode parameters / Paramètres du mode diagnostique
        self.diagnostic_mode: bool = config.getboolean('diagnostic_mode', False)  # Enable diagnostic logging / Activer la journalisation de diagnostic
        self.power_off_retries: int = config.getint('power_off_retries', 3)  # Number of retry attempts / Nombre de tentatives
        self.power_off_retry_delay: int = config.getint('power_off_retry_delay', 2)  # Delay between retries in seconds / Délai entre les tentatives en secondes

        # Dry run mode / Mode simulation
        self.dry_run_mode: bool = config.getboolean('dry_run_mode', False)  # Default is real power off / Par défaut, extinction réelle

        # Network device settings / Paramètres des périphériques réseau
        self.network_device: bool = config.getboolean('network_device', False)  # Is this a network power device / Est-ce un périphérique d'alimentation réseau
        self.device_address: Optional[str] = config.get('device_address', None)  # IP address or hostname / Adresse IP ou nom d'hôte
        self.network_test_attempts: int = config.getint('network_test_attempts', 3)  # Number of attempts to test connectivity / Nombre de tentatives pour tester la connectivité
        self.network_test_interval: float = config.getfloat('network_test_interval', 1.0)  # Interval between tests in seconds / Intervalle entre les tests en secondes

        # Register for events / Enregistrement pour les événements
        self.printer.register_event_handler("klippy:ready", self._handle_ready)
        self.printer.register_event_handler("print_stats:complete", self._handle_print_complete)

        # Monitored components configuration / Configuration des composants à surveiller
        self.monitor_hotend: bool = config.getboolean('monitor_hotend', True)
        self.monitor_bed: bool = config.getboolean('monitor_bed', True)
        self.monitor_chamber: bool = config.getboolean('monitor_chamber', False)

        # State variables / Variables d'état
        self.shutdown_timer: Optional[float] = None
        self.is_checking_temp: bool = False
        self.countdown_end: float = 0
        self.last_temps: Dict[str, float] = {"hotend": 0, "bed": 0}
        self._shutdown_in_progress: bool = False  # Flag to track shutdown state / Indicateur de suivi de l'état d'extinction
        self.state: str = "init"  # État initial du module (init, on, off, error)

        # Register gcode commands / Enregistrement des commandes GCODE
        gcode = self.printer.lookup_object('gcode')
        gcode.register_command('AUTO_POWEROFF', self.cmd_AUTO_POWEROFF,
                               desc=self.cmd_AUTO_POWEROFF_help)

        # Register for Fluidd/Mainsail status API / Enregistrement pour l'API de status Fluidd/Mainsail
        self.printer.register_event_handler("klippy:connect", self._handle_connect)

    def get_git_version(self) -> str:
        """
        Récupère la version à partir de Git si disponible.
        Évite les problèmes de 'inferred version'.
        
        Returns:
            str: Numéro de version Git ou version par défaut
        """
        try:
            # Vérifier si nous sommes dans un dépôt Git
            repo_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            git_dir = os.path.join(repo_dir, ".git")
            
            if os.path.isdir(git_dir):
                # Essayer d'obtenir la version depuis le tag Git
                try:
                    with open(os.path.join(git_dir, "HEAD"), 'r') as f:
                        head_ref = f.read().strip()
                    
                    # Si le HEAD pointe vers une référence
                    if head_ref.startswith("ref:"):
                        ref_path = head_ref[5:].strip()
                        ref_file = os.path.join(git_dir, ref_path)
                        
                        if os.path.isfile(ref_file):
                            with open(ref_file, 'r') as f:
                                return f"v{__version__}-{f.read().strip()[:7]}"
                except:
                    pass
            
            return f"v{__version__}"
        except:
            return f"v{__version__}"

    def _configure_language(self, config) -> None:
        """
        Configure language settings using multiple sources.
        
        This method determines the language to use by checking in this order:
        1. Explicit config parameter 'language'
        2. Persistent language file
        3. Environment variables (LANG, LANGUAGE, LC_ALL)
        4. Klipper configuration files
        5. Default to English if none of the above are available
        
        Args:
            config: Klipper config object containing language settings
            
        Returns:
            None
        
        Raises:
            TranslationError: If there's an error loading translations
        """
        configured_lang = config.get('language', None)
        if configured_lang == 'auto':
            configured_lang = None

        persistent_lang = self._get_persistent_language()

        env_lang = None
        try:
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

        klipper_lang = self._check_klipper_language_settings()
        self.lang = configured_lang or persistent_lang or env_lang or klipper_lang or 'en'
        
        # Validate language against available languages
        if self.lang.lower() not in [lang.value for lang in Language]:
            self.logger.warning(f"Unsupported language '{self.lang}'. Defaulting to English.")
            self.lang = Language.ENGLISH.value
        else:
            self.lang = self.lang.lower()

        if configured_lang and configured_lang != persistent_lang:
            self._save_persistent_language(self.lang)

        self.logger.info(f"Language detection: config={configured_lang}, persistent={persistent_lang}, env={env_lang}, klipper={klipper_lang}, final={self.lang}")

    def _check_klipper_language_settings(self) -> Optional[str]:
        """
        Check for language preference in Klipper configuration files.
        
        This method looks for French configuration files in common paths
        to determine if French should be used.
        
        Returns:
            str or None: 'fr' if French configuration is detected, None otherwise
        """
        try:
            config_paths = [
                "~/printer_data/config/mainsail/auto_power_off_fr.cfg",
                "~/printer_data/config/fluidd/auto_power_off_fr.cfg",
                "~/klipper_config/mainsail/auto_power_off_fr.cfg",
                "~/klipper_config/fluidd/auto_power_off_fr.cfg"
            ]
            for path in config_paths:
                expanded_path = os.path.expanduser(path)
                if os.path.exists(expanded_path):
                    return Language.FRENCH.value
        except Exception as e:
            self.logger.warning(f"Error checking Klipper config: {str(e)}")
        return None

    def _get_persistent_language(self) -> Optional[str]:
        """
        Get saved language from persistence file.
        
        Returns:
            str or None: The language code if found in persistence file, None otherwise
        """
        try:
            persistence_file = os.path.expanduser("~/printer_data/config/auto_power_off_language.conf")
            if os.path.exists(persistence_file):
                with open(persistence_file, 'r') as f:
                    saved_lang = f.read().strip()
                    return saved_lang if saved_lang in [lang.value for lang in Language] else None
        except Exception as e:
            self.logger.warning(f"Error reading persistent language: {str(e)}")
        return None

    def _save_persistent_language(self, language: str) -> None:
        """
        Save language preference to persistence file.
        
        Args:
            language: The language code to save
            
        Returns:
            None
        """
        try:
            persistence_dir = os.path.expanduser("~/printer_data/config")
            if not os.path.exists(persistence_dir):
                persistence_dir = os.path.expanduser("~/klipper_config")
                if not os.path.exists(persistence_dir):
                    self.logger.warning("Could not find config directory for language persistence / Répertoire de config introuvable pour la persistance de la langue")
                    return
            persistence_file = os.path.join(persistence_dir, "auto_power_off_language.conf")
            with open(persistence_file, 'w') as f:
                f.write(language)
            self.logger.info(f"Language preference saved to {persistence_file}")
        except Exception as e:
            self.logger.warning(f"Error saving language preference: {str(e)}")

    def _check_device_capabilities(self) -> bool:
        """
        Check and discover the capabilities of the power device.
        
        This method determines the available methods that can be used to power off
        the device and selects the optimal method.
        
        Returns:
            bool: True if device capabilities were successfully checked, False otherwise
            
        Raises:
            PowerDeviceError: If there's an error checking device capabilities
        """
        if not self.device_state == DeviceState.AVAILABLE:
            self._diagnostic_log("Cannot check capabilities, device not available / Impossible de vérifier les capacités, périphérique indisponible", level="warning")
            return False

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
            self.device_capabilities['set_power'] = hasattr(power_device, 'set_power')
            self.device_capabilities['turn_off'] = hasattr(power_device, 'turn_off')
            self.device_capabilities['power_off'] = hasattr(power_device, 'power_off')
            try:
                gcode = self.printer.lookup_object('gcode')
                handler = gcode.get_command_handler().get("POWER_OFF")
                self.device_capabilities['cmd_off'] = handler is not None
            except Exception as e:
                self._diagnostic_log(f"Error checking GCODE capabilities: {str(e)}", level="warning")
            
            self._diagnostic_log(f"Device capabilities: {self.device_capabilities}", level="info")
            
            # Determine optimal power off method based on available capabilities
            if self.device_capabilities['set_power']:
                self.optimal_method = PowerOffMethod.SET_POWER
            elif self.device_capabilities['turn_off']:
                self.optimal_method = PowerOffMethod.TURN_OFF
            elif self.device_capabilities['power_off']:
                self.optimal_method = PowerOffMethod.POWER_OFF
            elif self.device_capabilities['cmd_off']:
                self.optimal_method = PowerOffMethod.CMD_OFF
            elif self.device_capabilities['moonraker_available']:
                self.optimal_method = PowerOffMethod.MOONRAKER
            else:
                self.optimal_method = PowerOffMethod.UNKNOWN
                self._diagnostic_log("No viable power off method detected! / Aucune méthode d'extinction viable détectée!", level="error")
            
            return True
        except Exception as e:
            error_msg = f"Error checking device capabilities: {str(e)}"
            self.logger.error(self.get_text("error_checking_capabilities", error=str(e)))
            self._diagnostic_log(error_msg, level="error", data=e)
            raise PowerDeviceError(error_msg) from e

    def _verify_power_device(self) -> bool:
        """
        Verify that the configured power device exists and is available.
        
        This method checks if the power device exists in Klipper or if 
        Moonraker integration is enabled, and sets the device state accordingly.
        
        Returns:
            bool: True if device is available, False otherwise
            
        Raises:
            PowerDeviceNotFoundError: If the device is not found
            PowerDeviceError: For other device-related errors
        """
        self.device_state = DeviceState.UNAVAILABLE
        
        # If Moonraker integration is enabled, assume device is available
        if self.moonraker_integration:
            self._diagnostic_log(f"Using device '{self.power_device}' via Moonraker integration / Utilisation du périphérique via l'intégration Moonraker", level="info")
            self.device_state = DeviceState.AVAILABLE
            return True
        
        try:
            device_name = f'power {self.power_device}'
            power_device = self.printer.lookup_object(device_name, None)
            
            if power_device is None:
                error_msg = f"Power device '{self.power_device}' not found"
                self.logger.error(self.get_text("power_device_not_found", device=self.power_device))
                self._notify_user("power_device_not_found", device=self.power_device)
                raise PowerDeviceNotFoundError(error_msg)
            
            self.device_state = DeviceState.AVAILABLE
            self._check_device_capabilities()
            self._diagnostic_log(f"Power device '{self.power_device}' found / Périphérique d'alimentation trouvé", level="info")
            return True
        except PowerDeviceNotFoundError:
            # Re-raise device not found error
            raise
        except Exception as e:
            error_msg = f"Error verifying device '{self.power_device}': {str(e)}"
            self.logger.error(self.get_text("error_verifying_device", error=str(e), device=self.power_device))
            self._diagnostic_log(error_msg, level="error", data=e)
            raise PowerDeviceError(error_msg) from e

    def _power_off_dry_run(self) -> bool:
        """
        Simulate power off for testing purposes without actually powering off.
        
        This method logs the power off attempt and notifies the user,
        but does not actually power off the device.
        
        Returns:
            bool: True for successful dry run
        """
        self.logger.info(self.get_text("dry_run_power_off"))
        
        if self.moonraker_integration and not self.force_direct:
            self._diagnostic_log("DRY RUN: Would use Moonraker API for power off / SIMULATION : Utiliserait l'API Moonraker pour éteindre", level="info")
        else:
            self._diagnostic_log("DRY RUN: Would use direct Klipper method / SIMULATION : Utiliserait la méthode directe Klipper", level="info")
        
        if self.optimal_method:
            self._diagnostic_log(f"DRY RUN: Would use {self.optimal_method.name} method", level="info")
        
        self._notify_user("dry_run_power_off")
        return True

    def _test_network_device(self) -> bool:
        """
        Test if a network device is reachable.
        
        For network devices, this method attempts to connect to check
        if the device is reachable before trying to power it off.
        
        Returns:
            bool: True if device is reachable, False otherwise
            
        Raises:
            NetworkDeviceUnreachableError: If the network device is unreachable
        """
        if not self.network_device or not self.device_address:
            return True
        
        self._diagnostic_log(f"Testing connectivity to network device: {self.device_address}", level="info")
        
        for attempt in range(self.network_test_attempts):
            try:
                port = 80  # Commonly open port / Port couramment ouvert
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2.0)
                self._diagnostic_log(f"Attempt {attempt+1}/{self.network_test_attempts}: Connecting to {self.device_address}:{port}", level="debug")
                result = sock.connect_ex((self.device_address, port))
                sock.close()
                
                if result == 0:
                    self._diagnostic_log(f"Successfully connected to {self.device_address} / Connexion réussie", level="info")
                    return True
                else:
                    self._diagnostic_log(f"Failed to connect to {self.device_address}, error code: {result}", level="warning")
            
            except socket.error as e:
                self._diagnostic_log(f"Socket error connecting to {self.device_address}: {str(e)}", level="warning")
            
            if attempt < self.network_test_attempts - 1:
                self._diagnostic_log(f"Waiting {self.network_test_interval}s before next attempt / Attente de {self.network_test_interval}s avant prochaine tentative", level="debug")
                time.sleep(self.network_test_interval)
        
        error_msg = f"Network device '{self.device_address}' is unreachable after {self.network_test_attempts} attempts"
        self.logger.error(self.get_text("network_device_unreachable", device=self.device_address, attempts=self.network_test_attempts))
        self._notify_user("network_device_unreachable", device=self.device_address, attempts=self.network_test_attempts)
        raise NetworkDeviceUnreachableError(error_msg)

    def _load_translations(self) -> None:
        """
        Load language strings from translation files.
        
        This method attempts to load translations from the language files
        based on the configured language. If the file is not found, it falls
        back to English.
        
        Returns:
            None
            
        Raises:
            TranslationError: If there's an error loading translations
        """
        self.translations: Dict[str, str] = {}
        lang_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'auto_power_off_langs')
        
        try:
            lang_file = os.path.join(lang_dir, f"{self.lang}.json")
            
            if not os.path.exists(lang_file):
                self.logger.warning(f"Translation file {lang_file} not found, falling back to English / Fichier de traduction introuvable, utilisation de l'anglais par défaut")
                lang_file = os.path.join(lang_dir, f"{Language.ENGLISH.value}.json")
            
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            
            self.logger.info(f"Loaded {len(self.translations)} translations from {lang_file}")
        
        except Exception as e:
            error_msg = f"Error loading translations: {str(e)}"
            self.logger.error(f"{error_msg}. Using hardcoded English strings / Erreur lors du chargement des traductions : {str(e)}. Utilisation des chaînes anglaises codées en dur.")
            raise TranslationError(error_msg) from e

    def get_text(self, key: str, **kwargs) -> str:
        """
        Get translated text by key, with optional formatting parameters.
        
        Args:
            key: The translation key to look up
            **kwargs: Format parameters for the translation string
            
        Returns:
            str: The translated and formatted text
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
        
        self.logger.warning(f"Missing translation key: {key}")
        
        # Fallback dictionary for critical messages
        fallbacks = {
            "module_initialized": "Auto Power Off: Module initialized / Extinction auto : Module initialisé",
            "print_complete_disabled": "Print complete, but auto power off is disabled / Impression terminée, extinction auto désactivée",
            "print_complete_starting_timer": "Print complete, starting power-off timer / Impression terminée, démarrage du minuteur d'extinction",
            "print_in_progress": "Print in progress or resumed, canceling shutdown / Impression en cours ou reprise, annulation de l'extinction",
            "printer_not_idle": "Printer not idle, postponing shutdown / Imprimante non inoccupée, extinction reportée",
            "temperatures_too_high": "Temperatures too high (Hotend: {hotend_temp:.1f}, Bed: {bed_temp:.1f}), postponing shutdown / Températures trop élevées (Buse: {hotend_temp:.1f}, Lit: {bed_temp:.1f}), extinction reportée",
            "temperatures_too_high_custom": "Temperatures too high ({temp_msg}), maximum is {max_temp:.1f}°C / Températures trop élevées ({temp_msg}), maximum autorisé {max_temp:.1f}°C",
            "conditions_met": "Conditions met, powering off the printer / Conditions remplies, extinction de l'imprimante",
            "powered_off_moonraker": "Printer powered off successfully via Moonraker API / Imprimante éteinte avec succès via l'API Moonraker",
            "error_powering_off": "Error during power off: {error} / Erreur lors de l'extinction : {error}",
            "powered_off_set_power": "Printer powered off successfully (set_power method) / Imprimante éteinte avec succès (méthode set_power)",
            "powered_off_turn_off": "Printer powered off successfully (turn_off method) / Imprimante éteinte avec succès (méthode turn_off)",
            "powered_off_power_off": "Printer powered off successfully (power_off method) / Imprimante éteinte avec succès (méthode power_off)",
            "powered_off_gcode": "Printer powered off successfully via GCODE / Imprimante éteinte avec succès via GCODE",
            "power_device_not_found": "Power device '{device}' not found / Périphérique d'alimentation '{device}' introuvable",
            "error_checking_capabilities": "Error checking device capabilities: {error} / Erreur lors de la vérification des capacités : {error}",
            "error_verifying_device": "Error verifying device '{device}': {error} / Erreur lors de la vérification du périphérique '{device}' : {error}",
            "dry_run_power_off": "Dry run: Power off simulated / Simulation : Extinction simulée",
            "network_device_unreachable": "Network device '{device}' unreachable after {attempts} attempts / Périphérique réseau '{device}' injoignable après {attempts} tentatives",
            "power_device_not_available_for_poweroff": "Power device '{device}' not available for power off / Périphérique '{device}' non disponible pour l'extinction",
            "error_moonraker_all_retries_failed": "All Moonraker retries failed (retries: {retries}, error: {error}) / Toutes les tentatives via Moonraker ont échoué (tentatives : {retries}, erreur : {error})",
            "falling_back_to_direct": "Falling back to direct power off method / Repli sur la méthode directe d'extinction",
            "power_off_success": "Power off command issued successfully / Commande d'extinction émise avec succès",
            "no_power_off_method": "No power off method available / Aucune méthode d'extinction disponible",
            "shutdown_in_progress": "Shutdown already in progress / Extinction déjà en cours",
            "printer_already_shutdown": "Printer already shutdown / Imprimante déjà éteinte",
            "error_disabling_heaters": "Error disabling heaters: {error} / Erreur lors de la désactivation des chauffages : {error}",
            "error_preparing_shutdown": "Error preparing for shutdown: {error} / Erreur lors de la préparation à l'extinction : {error}",
            "auto_power_off_enabled": "Auto power off globally enabled / Extinction automatique activée globalement",
            "auto_power_off_disabled": "Auto power off globally disabled / Extinction automatique désactivée globalement",
            "timer_started": "Idle timer started / Minuteur d'inactivité démarré",
            "timer_already_active": "Idle timer already active / Minuteur d'inactivité déjà actif",
            "timer_canceled": "Idle timer canceled / Minuteur d'inactivité annulé",
            "no_active_timer": "No active timer to cancel / Aucun minuteur actif à annuler",
            "status_template": "Status: {enabled_status}, Timer: {timer_status}, Countdown: {countdown}, Temps: {temps}, Temp Threshold: {temp_threshold}°C, Idle Timeout: {idle_timeout} minutes / Statut : {enabled_status}, Minuteur : {timer_status}, Compte à rebours : {countdown}, Températures : {temps}, Seuil de Temp : {temp_threshold}°C, Temps inactivité : {idle_timeout} minutes",
            "powering_off": "Powering off the printer / Extinction de l'imprimante en cours",
            "option_not_recognized": "Option not recognized / Option non reconnue",
            "print_in_progress_moonraker": "Print in progress via Moonraker (state: {state}) / Impression en cours via Moonraker (état : {state})",
            "enabled_status": "Enabled / Activé",
            "disabled_status": "Disabled / Désactivé"
        }
        
        if key in fallbacks:
            text = fallbacks[key]
            if kwargs:
                try:
                    return text.format(**kwargs)
                except Exception:
                    return text
            return text
        
        return f"[{key}]"

    def _handle_connect(self) -> None:
        """
        Called on initial connection to register the object.
        
        This method registers the auto_power_off object with the printer
        if it doesn't already exist.
        
        Returns:
            None
        """
        try:
            self.printer.lookup_object("auto_power_off")
        except self.printer.config_error:
            self.printer.add_object("auto_power_off", self)

    def _handle_ready(self) -> None:
        """
        Called when Klipper is ready to set up the module.
        
        This method logs the initialization, verifies the power device,
        and sets up periodic temperature checking.
        
        Returns:
            None
        """
        self.logger.info(self.get_text("module_initialized"))
        
        # S'assurer que l'état d'extinction est réinitialisé
        self._reset_shutdown_state()
        
        try:
            if self._verify_power_device():
                self.logger.info(self.get_text("power_device_ready", device=self.power_device))
            else:
                self.logger.warning(self.get_text("power_device_not_available", device=self.power_device))
        except (PowerDeviceNotFoundError, PowerDeviceError) as e:
            self.logger.error(str(e))
        
        # Set up periodic temperature checker
        self.reactor.register_timer(self._update_temps, self.reactor.monotonic() + 1)
        
        # Set up periodic device state checker
        self.reactor.register_timer(self._verify_device_state, self.reactor.monotonic() + 10)

    def _handle_print_complete(self) -> None:
        """
        Called when print is complete to start shutdown timer.
        
        This method starts the shutdown timer if auto power off is enabled.
        
        Returns:
            None
        """
        if not self.enabled:
            self.logger.info(self.get_text("print_complete_disabled"))
            return
        
        self.logger.info(self.get_text("print_complete_starting_timer"))
        
        # Cancel any existing timer
        if self.shutdown_timer is not None:
            self.reactor.unregister_timer(self.shutdown_timer)
        
        # Start the idle timer
        waketime = self.reactor.monotonic() + self.idle_timeout
        self.countdown_end = self.reactor.monotonic() + self.idle_timeout
        self.shutdown_timer = self.reactor.register_timer(self._check_conditions, waketime)

    def _check_print_status_via_moonraker(self) -> Optional[str]:
        """
        Check print status via Moonraker API.
        
        This method uses the Moonraker API to check if a print
        is in progress, which is useful as a fallback check.
        
        Returns:
            str or None: The print state if available, None otherwise
            
        Raises:
            MoonrakerApiError: If there's an error accessing the Moonraker API
        """
        if not self.moonraker_integration:
            return None
        
        try:
            base_url = self.moonraker_url.rstrip('/')
            curl_command = f'curl -s "{base_url}/printer/objects/query?print_stats=state"'
            result = subprocess.run(curl_command, shell=True, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if 'result' in data and 'status' in data['result']:
                    state = data['result']['status'].get('print_stats', {}).get('state')
                    self._diagnostic_log(f"Moonraker print state: {state}", level="info")
                    return state
            
            return None
        except Exception as e:
            error_msg = f"Error checking print status via Moonraker: {str(e)}"
            self._diagnostic_log(error_msg, level="warning")
            raise MoonrakerApiError(error_msg) from e

    def _get_printer_state(self, eventtime: float) -> PrinterState:
        """
        Get the current state of the printer.
        
        This method checks different sources to determine if the printer
        is printing, idle, etc.
        
        Args:
            eventtime: Current event time from Klipper
            
        Returns:
            PrinterState: The current state of the printer
        """
        # Check if MCU is connected
        if not self._is_mcu_connected():
            return PrinterState.UNKNOWN
        
        # Check print_stats
        try:
            print_stats = self.printer.lookup_object('print_stats', None)
            if print_stats:
                state = print_stats.get_status(eventtime)['state']
                if state in ['printing', 'paused']:
                    return PrinterState.PRINTING if state == 'printing' else PrinterState.PAUSED
        except Exception as e:
            self._diagnostic_log(f"Error checking print_stats: {str(e)}", level="warning")
        
        # Check gcode_move
        try:
            gcode_move = self.printer.lookup_object('gcode_move')
            if gcode_move and gcode_move.get_status(eventtime).get('is_printing', False):
                return PrinterState.PRINTING
        except Exception as e:
            self._diagnostic_log(f"Error checking gcode_move: {str(e)}", level="warning")
        
        # Check via Moonraker
        if self.moonraker_integration:
            try:
                moonraker_state = self._check_print_status_via_moonraker()
                if moonraker_state in ['printing', 'paused']:
                    return PrinterState.PRINTING if moonraker_state == 'printing' else PrinterState.PAUSED
            except MoonrakerApiError as e:
                self._diagnostic_log(f"Error checking Moonraker: {str(e)}", level="warning")
        
        # Check if printer is idle
        try:
            idle_timeout_obj = self.printer.lookup_object('idle_timeout')
            idle_state = idle_timeout_obj.get_status(eventtime)['state']
            if idle_state == 'Idle':
                return PrinterState.IDLE
            else:
                return PrinterState.BUSY
        except Exception as e:
            self._diagnostic_log(f"Error checking idle_timeout: {str(e)}", level="warning")
        
        return PrinterState.UNKNOWN

    def _check_conditions(self, eventtime: float) -> float:
        """
        Check if conditions for power off are met.
        
        This method checks if the printer is idle and if temperatures
        are below the threshold. If all conditions are met, it powers off the printer.
        
        Args:
            eventtime: Current event time from Klipper
            
        Returns:
            float: Time for next check or NEVER if conditions are met
        """
        # Get printer state
        printer_state = self._get_printer_state(eventtime)
        
        # If printer is printing or paused, cancel shutdown
        if printer_state in [PrinterState.PRINTING, PrinterState.PAUSED]:
            self.logger.info(self.get_text("print_in_progress"))
            return self.reactor.NEVER
        
        # If printer is not idle, postpone shutdown
        if printer_state != PrinterState.IDLE:
            self.logger.info(self.get_text("printer_not_idle"))
            return eventtime + 60.0  # Recheck in 60 seconds
        
        # Check temperatures
        temps: Dict[str, float] = {}
        max_temp: float = 0.0
        
        try:
            heaters = self.printer.lookup_object('heaters')
            
            # Check hotend if enabled
            if self.monitor_hotend:
                try:
                    hotend = self.printer.lookup_object('extruder').get_heater()
                    hotend_temp = heaters.get_status(eventtime)[hotend.get_name()]['temperature']
                    temps['hotend'] = hotend_temp
                    max_temp = max(max_temp, hotend_temp)
                except Exception as e:
                    self.logger.warning(f"Unable to get hotend temperature: {str(e)}")
            
            # Check bed if enabled
            if self.monitor_bed:
                try:
                    bed = self.printer.lookup_object('heater_bed', None)
                    if bed is not None:
                        bed_temp = heaters.get_status(eventtime)[bed.get_heater().get_name()]['temperature']
                        temps['bed'] = bed_temp
                        max_temp = max(max_temp, bed_temp)
                except Exception as e:
                    self.logger.warning(f"Unable to get bed temperature: {str(e)}")
            
            # Check chamber if enabled
            if self.monitor_chamber:
                try:
                    chamber = self.printer.lookup_object('temperature_sensor chamber', None)
                    if chamber is not None:
                        chamber_temp = chamber.get_status(eventtime)['temperature']
                        temps['chamber'] = chamber_temp
                        max_temp = max(max_temp, chamber_temp)
                except Exception as e:
                    self.logger.warning(f"Unable to get chamber temperature: {str(e)}")
            
            # Update last temperatures for status
            self.last_temps = temps
            
            # Check if max temperature is below threshold
            if max_temp > self.temp_threshold:
                temp_msg = ", ".join(f"{key}: {value:.1f}°C" for key, value in temps.items())
                self.logger.info(self.get_text("temperatures_too_high_custom", temp_msg=temp_msg, max_temp=max_temp))
                return eventtime + 60.0  # Recheck in 60 seconds
            
            # All conditions met, power off the printer
            try:
                self._power_off()
            except (PowerOffError, NetworkDeviceError, MoonrakerApiError) as e:
                self.logger.error(f"Error during power off: {str(e)}")
                return eventtime + 60.0  # Retry in 60 seconds
            
            return self.reactor.NEVER
        
        except Exception as e:
            self.logger.error(f"Error checking conditions: {str(e)}")
            return eventtime + 60.0  # Retry in 60 seconds

    def _is_mcu_connected(self) -> bool:
        """
        Check if the MCU is connected and responding.
        
        Returns:
            bool: True if MCU is connected, False otherwise
            
        Raises:
            MCUError: If there's an error checking MCU status
        """
        try:
            mcu = self.printer.lookup_object('mcu', None)
            if mcu is None:
                self._diagnostic_log(self.get_text("mcu_object_not_found"), level="warning")
                return False
            if mcu.is_shutdown():
                self._diagnostic_log(self.get_text("mcu_shutdown_disconnected"), level="warning")
                return False
            return True
        except Exception as e:
            error_msg = f"Error checking MCU status: {str(e)}"
            self._diagnostic_log(self.get_text("error_checking_mcu_status", error=str(e)), level="warning")
            raise MCUError(error_msg) from e

    def _prepare_mcu_for_shutdown(self) -> None:
        """
        Prepare the MCU for a clean shutdown.
        
        This method turns off heaters and performs other cleanup
        before powering off the printer.
        
        Returns:
            None
            
        Raises:
            PowerOffError: If there's an error preparing for shutdown
        """
        try:
            if self._shutdown_in_progress:
                self.logger.info(self.get_text("shutdown_in_progress"))
                return
            
            if self.printer.is_shutdown():
                self.logger.warning(self.get_text("printer_already_shutdown"))
                return
            
            self._shutdown_in_progress = True
            self._shutdown_start_time = self.reactor.monotonic()  # Enregistrer le moment du début de l'extinction
            self._diagnostic_log("Preparing MCU for shutdown / Préparation du MCU pour l'extinction", level="info")
            
            try:
                gcode = self.printer.lookup_object('gcode')
                gcode.run_script_from_command("TURN_OFF_HEATERS")
                time.sleep(0.5)
            except Exception as e:
                error_msg = f"Error disabling heaters: {str(e)}"
                self._diagnostic_log(self.get_text("error_disabling_heaters", error=str(e)), level="warning")
                raise PowerOffError(error_msg) from e
        
        except Exception as e:
            error_msg = f"Error preparing for shutdown: {str(e)}"
            self._diagnostic_log(self.get_text("error_preparing_shutdown", error=str(e)), level="warning")
            raise PowerOffError(error_msg) from e

    def _execute_curl_with_retry(self, command: str, max_retries: int, retry_delay: int, timeout: int = 10) -> subprocess.CompletedProcess:
        """
        Execute a curl command with retry logic.
        
        Args:
            command: The curl command to execute
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            timeout: Timeout for the curl command in seconds
            
        Returns:
            subprocess.CompletedProcess: The completed process if successful
            
        Raises:
            MoonrakerApiError: If all retries fail
        """
        retry_count = 0
        last_error: Optional[Exception] = None
        
        while retry_count < max_retries:
            self._diagnostic_log(f"Power off attempt {retry_count + 1}/{max_retries} / Tentative d'extinction {retry_count + 1}/{max_retries}", level="info")
            
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
                
                if result.returncode == 0:
                    try:
                        response_data = json.loads(result.stdout)
                        self._diagnostic_log(f"Curl command response: {response_data}", level="info")
                        
                        if 'error' in response_data:
                            error_msg = f"Moonraker API error: {response_data['error']}"
                            self._diagnostic_log(error_msg, level="error")
                            last_error = MoonrakerApiError(error_msg)
                        else:
                            return result
                    
                    except json.JSONDecodeError:
                        self._diagnostic_log("Non-JSON response but curl successful: " + result.stdout[:200], level="info")
                        return result
                
                else:
                    error_msg = f"Curl command failed (code {result.returncode}): {result.stderr}"
                    self._diagnostic_log(error_msg, level="error")
                    last_error = MoonrakerApiError(error_msg)
            
            except subprocess.TimeoutExpired:
                error_msg = "Curl command timed out / Délai d'attente expiré pour curl"
                self._diagnostic_log(error_msg, level="error")
                last_error = MoonrakerApiError(error_msg)
            
            except Exception as e:
                error_msg = f"Error executing curl command: {str(e)}"
                self._diagnostic_log(error_msg, level="error")
                last_error = e
            
            retry_count += 1
            
            if retry_count < max_retries:
                self._diagnostic_log(f"Retrying in {retry_delay} seconds... / Nouvelle tentative dans {retry_delay} secondes...", level="info")
                time.sleep(retry_delay)
        
        # If we get here, all retries failed
        error_msg = f"All {max_retries} retry attempts failed"
        if last_error:
            error_msg = f"{error_msg}: {str(last_error)}"
        
        raise MoonrakerApiError(error_msg)
    
    def _reset_shutdown_state(self):
        """
        Réinitialise l'état d'extinction du module.
        
        Cette méthode est utilisée pour s'assurer que le module est dans un état
        cohérent après un redémarrage ou lorsque l'état du relais change.
        """
        self._shutdown_in_progress = False
        self._diagnostic_log("État d'extinction réinitialisé / Shutdown state reset", level="info")


    def _power_off(self, force_direct: bool = False, diagnostic_mode: Optional[bool] = None) -> None:
        """
        Power off the printer with error handling and retry mechanism.
        
        Args:
            force_direct: Force direct Klipper method instead of Moonraker API
            diagnostic_mode: Override global diagnostic mode setting
            
        Returns:
            None
            
        Raises:
            PowerOffError: If there's an error during power off
            PowerDeviceNotAvailableError: If the power device is not available
            NetworkDeviceUnreachableError: If the network device is unreachable
            MoonrakerApiError: If there's an error with the Moonraker API
        """
        self._reset_shutdown_state()
    
        try:
            if self.printer.is_shutdown():
                self.logger.warning("Printer already shutdown / Imprimante déjà éteinte, abandon de la procédure")
                return
            
            self.logger.info(self.get_text("conditions_met"))
            self.force_direct = force_direct
            
            self._diagnostic_log(f"Starting power off process: moonraker_integration={self.moonraker_integration}, force_direct={force_direct}, device={self.power_device}", level="info")
            
            if self.moonraker_integration:
                base_url = self.moonraker_url.rstrip('/')
                power_status_url = f"{base_url}/printer/objects/query?objects=power_devices"
                power_off_url = f"{base_url}/machine/device_power/device?device={self.power_device}&action=off"
                self._diagnostic_log(f"Moonraker URLs: status={power_status_url}, power_off={power_off_url}", level="info")
            
            # Indique qu'une extinction est en cours
            self._shutdown_in_progress = True
            
            if self.device_state != DeviceState.AVAILABLE:
                error_msg = f"Power device '{self.power_device}' not available for power off"
                self.logger.error(self.get_text("power_device_not_available_for_poweroff", device=self.power_device))
                self._notify_user("power_device_not_available_for_poweroff", device=self.power_device)
                self._reset_shutdown_state()  # Réinitialisation en cas d'erreur
                raise PowerDeviceNotAvailableError(error_msg)
            
            # Override diagnostic mode if specified
            self._diagnostic_mode = diagnostic_mode if diagnostic_mode is not None else self.diagnostic_mode
            
            # For network devices, test connectivity first
            if self.network_device:
                try:
                    self._test_network_device()
                except NetworkDeviceUnreachableError as e:
                    self.logger.error(self.get_text("network_device_unreachable", device=self.device_address, attempts=self.network_test_attempts))
                    self._notify_user("network_device_unreachable_poweroff", device=self.device_address)
                    self._reset_shutdown_state()  # Réinitialisation en cas d'erreur
                    raise
            
            # If dry run mode is enabled, simulate power off
            if self.dry_run_mode:
                self._reset_shutdown_state()  # Réinitialisation après simulation
                return self._power_off_dry_run()
            
            # Prepare the MCU for shutdown
            try:
                self._prepare_mcu_for_shutdown()
                time.sleep(1)
            except Exception as e:
                self._reset_shutdown_state()  # Réinitialisation en cas d'erreur
                raise
            
            # Use Moonraker API if enabled and not forced to use direct method
            if self.moonraker_integration and not force_direct:
                self._diagnostic_log("Using Moonraker API for power off / Utilisation de l'API Moonraker pour extinction", level="info")
                
                try:
                    curl_cmd = f'curl -s -X POST "{self.moonraker_url.rstrip("/")}/machine/device_power/device?device={self.power_device}&action=off"'
                    result = self._execute_curl_with_retry(curl_cmd, self.power_off_retries, self.power_off_retry_delay, timeout=10)
                    
                    try:
                        json.loads(result.stdout)
                    except json.JSONDecodeError:
                        pass
                    
                    self.logger.info(self.get_text("powered_off_moonraker"))
                    self._notify_user("power_off_success")
                    self.state = "off"
                    # Ne pas réinitialiser _shutdown_in_progress ici, car l'appareil va s'éteindre
                    return
                
                except MoonrakerApiError as e:
                    self.logger.error(self.get_text("error_moonraker_all_retries_failed", retries=self.power_off_retries, error=str(e)))
                    self._notify_user("moonraker_retries_failed")
                    self.logger.info(self.get_text("falling_back_to_direct"))
                    
                    try:
                        self._prepare_mcu_for_shutdown()
                        time.sleep(1)
                        self._power_off_direct()
                    except PowerOffError as direct_error:
                        self.logger.error(f"Direct method also failed: {str(direct_error)}")
                        self.state = "error"
                        self._reset_shutdown_state()  # Réinitialisation en cas d'échec
                        raise
            
            else:
                method = "direct (forced)" if force_direct else "direct"
                self._diagnostic_log(f"Using {method} Klipper method for power off / Utilisation de la méthode {method} pour extinction", level="info")
                self._power_off_direct()
            
        except (PowerOffError, NetworkDeviceError, MoonrakerApiError) as e:
            self._reset_shutdown_state()  # Réinitialisation en cas d'erreur spécifique
            raise
        
        except Exception as e:
            error_msg = f"Unhandled exception during power off: {str(e)}"
            self.logger.error(error_msg)
            self._diagnostic_log(error_msg, level="error", data=e)
            self._reset_shutdown_state()  # Réinitialisation en cas d'erreur générique
            raise PowerOffError(error_msg) from e
        
    def _verify_device_state(self, eventtime: float) -> float:
        """
        Vérifie périodiquement l'état du périphérique d'alimentation et réinitialise
        l'état interne du module si nécessaire.
        
        Args:
            eventtime: Temps actuel fourni par Klipper
            
        Returns:
            float: Temps pour la prochaine vérification
        """
        try:
            # Vérifier si un redémarrage est nécessaire
            if self._shutdown_in_progress:
                # Si l'extinction est en cours depuis plus de 30 secondes, 
                # considérer qu'il y a eu un problème et réinitialiser
                if hasattr(self, "_shutdown_start_time") and (self.reactor.monotonic() - self._shutdown_start_time) > 30:
                    self._diagnostic_log("Réinitialisation forcée de l'état d'extinction après timeout / Forced reset of shutdown state after timeout", level="warning")
                    self._reset_shutdown_state()
            
            # Vérifier si le périphérique est disponible
            try:
                if not self._verify_power_device():
                    self._diagnostic_log("Périphérique d'alimentation non disponible lors de la vérification / Power device not available during check", level="warning")
                else:
                    # Si le périphérique est disponible et que l'extinction était en cours,
                    # cela signifie qu'il a été rallumé manuellement
                    if self._shutdown_in_progress:
                        self._diagnostic_log("Périphérique rallumé manuellement, réinitialisation de l'état / Device manually turned on, resetting state", level="info")
                        self._reset_shutdown_state()
            except Exception as e:
                self._diagnostic_log(f"Erreur lors de la vérification du périphérique: {str(e)} / Error checking device: {str(e)}", level="warning")
        except Exception as e:
            self.logger.error(f"Erreur non gérée dans _verify_device_state: {str(e)} / Unhandled error in _verify_device_state: {str(e)}")
        
        # Vérifier toutes les 10 secondes
        return eventtime + 10.0
        
    def _diagnostic_log(self, message: str, level: str = "debug", data: Any = None) -> None:
        """
        Log diagnostic information if diagnostic mode is enabled.
        
        Args:
            message: The message to log
            level: The log level (debug, info, warning, error)
            data: Additional data to log
            
        Returns:
            None
        """
        if level == "error":
            self.logger.error(message)
            if data:
                self.logger.error(f"Error details: {data}")
            return
        
        if hasattr(self, '_diagnostic_mode') and self._diagnostic_mode:
            log_method = getattr(self.logger, level, self.logger.info)
            log_method(f"DIAGNOSTIC: {message}")
            if data:
                log_method(f"DIAGNOSTIC DATA: {data}")

    def _power_off_direct(self) -> None:
        """
        Power off the printer using direct Klipper control methods.
        
        This method uses the optimal method determined during device
        capability check to power off the printer.
        
        Returns:
            None
            
        Raises:
            PowerOffError: If there's an error during power off
            PowerDeviceNotAvailableError: If the power device is not available
        """
        try:
            if self.printer.is_shutdown():
                self.logger.warning("Printer is already shutdown / Imprimante déjà éteinte, commande impossible")
                return
            
            if self.device_state != DeviceState.AVAILABLE:
                error_msg = f"Power device '{self.power_device}' not available for power off"
                self.logger.error(self.get_text("power_device_not_available_for_poweroff", device=self.power_device))
                self._notify_user("power_device_not_available_for_poweroff", device=self.power_device)
                raise PowerDeviceNotAvailableError(error_msg)
            
            try:
                device_name = f'power {self.power_device}'
                self._diagnostic_log(f"Looking up power device: {device_name} / Recherche du périphérique d'alimentation", level="info")
                power_device = self.printer.lookup_object(device_name)
                
                # Make sure device capabilities have been checked
                if self.optimal_method is None:
                    self._check_device_capabilities()
                
                # Use the optimal method determined during capability check
                if self.optimal_method == PowerOffMethod.SET_POWER:
                    self._diagnostic_log("Using set_power(0) method / Utilisation de la méthode set_power(0)", level="info")
                    power_device.set_power(0)
                    self.logger.info(self.get_text("powered_off_set_power"))
                    self._notify_user("power_off_success")
                
                elif self.optimal_method == PowerOffMethod.TURN_OFF:
                    self._diagnostic_log("Using turn_off() method / Utilisation de la méthode turn_off()", level="info")
                    power_device.turn_off()
                    self.logger.info(self.get_text("powered_off_turn_off"))
                    self._notify_user("power_off_success")
                
                elif self.optimal_method == PowerOffMethod.POWER_OFF:
                    self._diagnostic_log("Using power_off() method / Utilisation de la méthode power_off()", level="info")
                    power_device.power_off()
                    self.logger.info(self.get_text("powered_off_power_off"))
                    self._notify_user("power_off_success")
                
                elif self.optimal_method == PowerOffMethod.CMD_OFF:
                    self._diagnostic_log("Using GCODE POWER_OFF command / Utilisation de la commande GCODE POWER_OFF", level="info")
                    gcode = self.printer.lookup_object('gcode')
                    gcode.run_script_from_command(f"POWER_OFF {self.power_device}")
                    self.logger.info(self.get_text("powered_off_gcode"))
                    self._notify_user("power_off_success")
                
                else:
                    error_msg = "No valid power off method available"
                    self.logger.error(self.get_text("no_power_off_method"))
                    self._notify_user("no_power_off_method")
                    raise PowerOffError(error_msg)
                
                self.state = "off"
            
            except self.printer.config_error as e:
                self.logger.warning(f"Power device not found in Klipper: {str(e)} / Périphérique non trouvé dans Klipper")
                self._diagnostic_log(f"Power device lookup failed: {str(e)}", level="warning")
                
                # Try using GCODE POWER_OFF as fallback
                try:
                    gcode = self.printer.lookup_object('gcode')
                    self._diagnostic_log("Using GCODE POWER_OFF command as fallback / Utilisation de la commande GCODE POWER_OFF en solution de repli", level="info")
                    gcode.run_script_from_command(f"POWER_OFF {self.power_device}")
                    self.logger.info(self.get_text("powered_off_gcode"))
                    self._notify_user("power_off_success")
                    self.state = "off"
                    return
                
                except Exception as gcode_error:
                    error_msg = f"Failed to use GCODE POWER_OFF command: {str(gcode_error)}"
                    self.logger.error(f"{error_msg} / Échec de la commande GCODE POWER_OFF")
                    self._notify_user("power_off_failed", error="Could not find power device in Klipper / Périphérique non trouvé dans Klipper")
                    self.state = "error"
                    raise PowerOffError(error_msg) from gcode_error
            
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if this is an expected error during shutdown
                if ("command request" in error_str or "shutdown" in error_str or "disconnected" in error_str):
                    self._diagnostic_log("Normal shutdown with MCU disconnect detected / Extinction normale avec déconnexion MCU détectée", level="info")
                    self.state = "off"
                    return
                
                # Otherwise, it's a real error
                error_msg = f"Error during power off: {str(e)}"
                self.logger.error(self.get_text("error_powering_off", error=str(e)))
                self._diagnostic_log(error_msg, level="error", data=e)
                self._notify_user("power_off_failed", error=str(e))
                self.state = "error"
                raise PowerOffError(error_msg) from e
        
        except (PowerDeviceNotAvailableError, PowerOffError):
            # Re-raise these specific exceptions
            raise
        
        except Exception as e:
            error_str = str(e).lower()
            
            # Check if this is an expected error during shutdown
            if ("command request" in error_str or "shutdown" in error_str or "disconnected" in error_str):
                self._diagnostic_log("Normal shutdown with MCU disconnect detected / Extinction normale avec déconnexion MCU détectée", level="info")
                self.state = "off"
                return
            
            error_msg = f"Unhandled exception during direct power off: {str(e)}"
            self.logger.error(error_msg)
            self._diagnostic_log(error_msg, level="error", data=e)
            self.state = "error"
            raise PowerOffError(error_msg) from e

    def _notify_user(self, message_key: str, **kwargs) -> None:
        """
        Send notification to user via GCODE response.
        
        Args:
            message_key: The message key for translation
            **kwargs: Format parameters for the message
            
        Returns:
            None
        """
        if not self._is_mcu_connected():
            message = self.get_text(message_key, **kwargs)
            self.logger.info(f"User notification (not sent due to MCU state): {message}")
            return
        
        try:
            message = self.get_text(message_key, **kwargs)
            gcode = self.printer.lookup_object('gcode')
            gcode.respond_info(message)
            
            try:
                display = self.printer.lookup_object('display', None)
                if display:
                    self._diagnostic_log("Sending notification to display / Envoi de notification à l'écran", level="info")
                    short_msg = message[:40] + "..." if len(message) > 40 else message
                    gcode.run_script_from_command(f"M117 {short_msg}")
            except Exception as display_err:
                self._diagnostic_log(f"Could not send to display: {str(display_err)}", level="warning")
        
        except Exception as e:
            self.logger.warning(f"Failed to send notification to user: {str(e)}")

    def _update_temps(self, eventtime: float) -> float:
        """
        Update temperatures for status API.
        
        Args:
            eventtime: Current event time from Klipper
            
        Returns:
            float: Time for next update
        """
        temps: Dict[str, float] = {}
        
        try:
            # Try to get extruder temperature
            try:
                extruder = self.printer.lookup_object('extruder')
                if extruder and hasattr(extruder, 'get_status'):
                    status = extruder.get_status(eventtime)
                    if 'temperature' in status:
                        temps['hotend'] = status['temperature']
            except Exception as e:
                self.logger.debug(f"Error getting extruder temp: {str(e)}")
            
            # Try to get bed temperature
            try:
                heater_bed = self.printer.lookup_object('heater_bed')
                if heater_bed and hasattr(heater_bed, 'get_status'):
                    status = heater_bed.get_status(eventtime)
                    if 'temperature' in status:
                        temps['bed'] = status['temperature']
            except Exception as e:
                self.logger.debug(f"Error getting bed temp: {str(e)}")
            
            # Fallback for extruder temperature
            if 'hotend' not in temps:
                try:
                    stats = self.printer.lookup_object('extruder').stats(eventtime)
                    if 'temp' in stats:
                        temps['hotend'] = stats['temp']
                except:
                    temps['hotend'] = 0.0
            
            # Fallback for bed temperature
            if 'bed' not in temps:
                try:
                    stats = self.printer.lookup_object('heater_bed').stats(eventtime)
                    if 'temp' in stats:
                        temps['bed'] = stats['temp']
                except:
                    temps['bed'] = 0.0
            
            self.last_temps = temps
        
        except Exception as e:
            self.logger.error(f"Error updating temperatures: {str(e)}")
        
        # Schedule next update in 1 second
        return eventtime + 1.0

    def get_status(self, eventtime: float) -> Dict[str, Any]:
        """
        Get status for Fluidd/Mainsail API.
        
        Args:
            eventtime: Current event time from Klipper
            
        Returns:
            dict: Status information for the UI
        """
        time_left = max(0, self.countdown_end - self.reactor.monotonic()) if self.shutdown_timer is not None else 0

        git_version = self.get_git_version()
        
        return {
            'enabled': self.enabled,
            'active': self.shutdown_timer is not None,
            'countdown': int(time_left),
            'idle_timeout': int(self.idle_timeout),
            'temp_threshold': self.temp_threshold,
            'current_temps': self.last_temps,
            'language': self.lang,
            'diagnostic_mode': self.diagnostic_mode,
            'device_available': self.device_state == DeviceState.AVAILABLE,
            'dry_run_mode': self.dry_run_mode,
            'optimal_method': self.optimal_method.name if self.optimal_method else None,
            'device_capabilities': self.device_capabilities,
            'state': self.state,
            'version': git_version 
        }

    cmd_AUTO_POWEROFF_help = "Configure or trigger automatic printer power off / Configure ou déclenche l'extinction automatique de l'imprimante"

    def cmd_AUTO_POWEROFF(self, gcmd) -> None:
        """
        GCODE command to configure or trigger automatic power off.
        
        Args:
            gcmd: GCODE command object
            
        Returns:
            None
        """
        option = gcmd.get('OPTION', 'status').lower()
        
        # Check which options can work without MCU
        if option in ['language', 'status', 'diagnostic', 'dryrun']:
            pass
        else:
            if not self._is_mcu_connected() and option in ['now', 'start']:
                gcmd.respond_info("MCU communication not possible, cannot execute hardware-related command / Communication MCU impossible, commande liée au matériel non exécutée")
                return
        
        # Handle language option
        if option == 'language':
            lang_value = gcmd.get('VALUE', '').lower()
            if lang_value in [lang.value for lang in Language]:
                self.lang = lang_value
                self._save_persistent_language(self.lang)
                self._load_translations()
                gcmd.respond_info(self.get_text("language_set"))
            else:
                gcmd.respond_info(self.get_text("language_not_recognized", lang_value=lang_value))
            return
        
        # Handle on/off options
        if option == 'on':
            self.enabled = True
            gcmd.respond_info(self.get_text("auto_power_off_enabled"))
        
        elif option == 'off':
            self.enabled = False
            if self.shutdown_timer is not None:
                self.reactor.unregister_timer(self.shutdown_timer)
                self.shutdown_timer = None
            gcmd.respond_info(self.get_text("auto_power_off_disabled"))
        
        elif option == 'now':
            gcmd.respond_info(self.get_text("powering_off"))
            self.reactor.register_callback(lambda e: self._power_off())
        
        elif option == 'start':
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
            if self.shutdown_timer is not None:
                self.reactor.unregister_timer(self.shutdown_timer)
                self.shutdown_timer = None
                gcmd.respond_info(self.get_text("timer_canceled"))
            else:
                gcmd.respond_info(self.get_text("no_active_timer"))
        
        elif option == 'status':
            enabled_status = self.get_text("enabled_status") if self.enabled else self.get_text("disabled_status")
            timer_status = self.get_text("timer_active") if self.shutdown_timer is not None else self.get_text("timer_inactive")
            
            if self.lang == Language.FRENCH.value:
                temps = f"Buse: {self.last_temps.get('hotend', 0):.1f}°C, Lit: {self.last_temps.get('bed', 0):.1f}°C"
            else:
                temps = f"Hotend: {self.last_temps.get('hotend', 0):.1f}°C, Bed: {self.last_temps.get('bed', 0):.1f}°C"
            
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

        elif option == 'reset':
            # Réinitialisation forcée de l'état du module
            self._reset_shutdown_state()
            self._verify_power_device()
            gcmd.respond_info("Réinitialisation de l'état du module effectuée / Module state reset completed")
        
        elif option == 'diagnostic':
            diag_mode = gcmd.get_int('VALUE', 1, minval=0, maxval=1)
            self.diagnostic_mode = bool(diag_mode)
            
            if self.diagnostic_mode:
                gcmd.respond_info(self.get_text("diagnostic_mode_enabled"))
                self.logger.info("Diagnostic mode enabled by user / Mode diagnostique activé par l'utilisateur")
            else:
                gcmd.respond_info(self.get_text("diagnostic_mode_disabled"))
                self.logger.info("Diagnostic mode disabled by user / Mode diagnostique désactivé par l'utilisateur")
        
        elif option == 'dryrun':
            dry_run_value = gcmd.get_int('VALUE', 1, minval=0, maxval=1)
            self.dry_run_mode = bool(dry_run_value)
            
            if self.dry_run_mode:
                gcmd.respond_info(self.get_text("dry_run_enabled"))
                self.logger.info("Dry run mode enabled by user / Mode simulation activé par l'utilisateur")
            else:
                gcmd.respond_info(self.get_text("dry_run_disabled"))
                self.logger.info("Dry run mode disabled by user / Mode simulation désactivé par l'utilisateur")
        
        elif option == 'version':
            gcmd.respond_info(f"Auto Power Off version: {__version__}")
        
        else:
            gcmd.respond_info(self.get_text("option_not_recognized"))


def load_config(config):
    return AutoPowerOff(config)
