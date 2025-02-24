#!/bin/bash
# Global installation script for Klipper Auto Power Off module
# Usage: bash install_auto_power_off.sh

# Colors for messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to display formatted messages
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if script is run as root
if [ "$EUID" -eq 0 ]; then
    print_error "Do not run this script as root (sudo). Use your normal user."
    exit 1
fi

# Check if Klipper is installed
if [ ! -d ~/klipper ]; then
    print_error "Klipper directory not found in your home directory."
    print_error "Make sure Klipper is installed before running this script."
    exit 1
fi

# Create Klipper extras directory if needed
print_status "Checking required directories..."
mkdir -p ~/klipper/klippy/extras
print_success "Extras directory checked."

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
    print_error "Could not automatically find the configuration directory."
    echo "Please enter the full path to your Klipper configuration directory:"
    read -r PRINTER_CONFIG_DIR
    
    if [ ! -d "$PRINTER_CONFIG_DIR" ]; then
        print_error "Directory does not exist. Installation canceled."
        exit 1
    fi
fi

print_success "Configuration directory found: $PRINTER_CONFIG_DIR"

# Create directory for Fluidd
mkdir -p $PRINTER_CONFIG_DIR/fluidd
print_success "Fluidd directory created."

# Create Python module
print_status "Creating Python module auto_power_off.py..."
cat > ~/klipper/klippy/extras/auto_power_off.py << 'EOF'
# auto_power_off.py
# Automatic power off script for 3D printers running Klipper
# Place in the ~/klipper/klippy/extras/ folder

import logging
import threading
import time

class AutoPowerOff:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.reactor = self.printer.get_reactor()
        
        # Configuration parameters
        self.idle_timeout = config.getfloat('idle_timeout', 600.0)  # Idle time in seconds (10 min default)
        self.temp_threshold = config.getfloat('temp_threshold', 40.0)  # Temperature threshold in °C
        self.power_device = config.get('power_device', 'psu_control')  # Name of your power device
        self.enabled = config.getboolean('auto_poweroff_enabled', False)  # Default enabled/disabled state
        
        # Register for events
        self.printer.register_event_handler("klippy:ready", self._handle_ready)
        self.printer.register_event_handler("print_stats:complete", self._handle_print_complete)
        
        # State variables
        self.shutdown_timer = None
        self.is_checking_temp = False
        self.countdown_end = 0
        self.last_temps = {"hotend": 0, "bed": 0}
        
        # Register gcode commands
        gcode = self.printer.lookup_object('gcode')
        gcode.register_command('AUTO_POWEROFF', self.cmd_AUTO_POWEROFF,
                              desc=self.cmd_AUTO_POWEROFF_help)
                              
        # Register for Fluidd/Mainsail status API
        self.printer.register_event_handler("klippy:connect", 
                                           self._handle_connect)
        
        # Logging
        self.logger = logging.getLogger('auto_power_off')
        self.logger.setLevel(logging.INFO)
    
    def _handle_connect(self):
        """Called on initial connection"""
        # Register the object to make it accessible via API
        self.printer.add_object("auto_power_off", self)
    
    def _handle_ready(self):
        """Called when Klipper is ready"""
        self.logger.info("Auto Power Off: Module initialized")
        
        # Set up periodic temperature checker
        self.reactor.register_timer(self._update_temps, self.reactor.monotonic() + 1)
    
    def _handle_print_complete(self):
        """Called when print is complete"""
        if not self.enabled:
            self.logger.info("Print complete, but auto power off is disabled")
            return
            
        self.logger.info("Print complete, starting power-off timer")
        
        # Cancel any existing timer
        if self.shutdown_timer is not None:
            self.reactor.unregister_timer(self.shutdown_timer)
        
        # Start the idle timer
        waketime = self.reactor.monotonic() + self.idle_timeout
        self.countdown_end = self.reactor.monotonic() + self.idle_timeout
        self.shutdown_timer = self.reactor.register_timer(self._check_conditions, waketime)
    
    def _check_conditions(self, eventtime):
        """Check if conditions for power off are met"""
        # Check current print state
        print_stats = self.printer.lookup_object('print_stats', None)
        if print_stats and print_stats.get_status(eventtime)['state'] != 'complete':
            self.logger.info("Print in progress or resumed, canceling shutdown")
            self.shutdown_timer = None
            return self.reactor.NEVER
        
        # Check if printer is truly idle
        idle_timeout = self.printer.lookup_object('idle_timeout')
        if idle_timeout.get_status(eventtime)['state'] != 'Idle':
            self.logger.info("Printer not idle, postponing shutdown")
            return eventtime + 60.0  # Check again in 60 seconds
        
        # Check temperatures
        heaters = self.printer.lookup_object('heaters')
        hotend = self.printer.lookup_object('extruder').get_heater()
        try:
            bed = self.printer.lookup_object('heater_bed').get_heater()
            bed_temp = heaters.get_status(eventtime)[bed.get_name()]['temperature']
        except:
            bed_temp = 0.0
            
        hotend_temp = heaters.get_status(eventtime)[hotend.get_name()]['temperature']
        
        if max(hotend_temp, bed_temp) > self.temp_threshold:
            self.logger.info(f"Temperatures too high (Hotend: {hotend_temp:.1f}, Bed: {bed_temp:.1f}), postponing shutdown")
            return eventtime + 60.0  # Check again in 60 seconds
        
        # All conditions met, power off the printer
        self._power_off()
        self.shutdown_timer = None
        return self.reactor.NEVER
    
    def _power_off(self):
        """Power off the printer"""
        self.logger.info("Conditions met, powering off the printer")
        
        try:
            # Access the power controller and turn it off
            power_device = self.printer.lookup_object('power ' + self.power_device)
            power_device.set_power(0)
            self.logger.info("Printer powered off successfully")
        except Exception as e:
            self.logger.error(f"Error during power off: {str(e)}")
    
    def _update_temps(self, eventtime):
        """Update temperatures for status API"""
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
            self.logger.error(f"Error updating temperatures: {str(e)}")
            
        # Schedule next update in 1 second
        return eventtime + 1.0
        
    def get_status(self, eventtime):
        """Get status for Fluidd/Mainsail API"""
        time_left = max(0, self.countdown_end - eventtime) if self.shutdown_timer is not None else 0
        
        return {
            'enabled': self.enabled,
            'active': self.shutdown_timer is not None,
            'countdown': int(time_left),
            'idle_timeout': int(self.idle_timeout),
            'temp_threshold': self.temp_threshold,
            'current_temps': self.last_temps
        }
        
    cmd_AUTO_POWEROFF_help = "Configure or trigger automatic printer power off"
    def cmd_AUTO_POWEROFF(self, gcmd):
        """GCODE command to configure or trigger automatic power off"""
        option = gcmd.get('OPTION', 'status')
        
        if option.lower() == 'on':
            # Globally enable auto power off
            self.enabled = True
            gcmd.respond_info("Auto power off globally enabled")
                
        elif option.lower() == 'off':
            # Globally disable auto power off
            self.enabled = False
            if self.shutdown_timer is not None:
                self.reactor.unregister_timer(self.shutdown_timer)
                self.shutdown_timer = None
            gcmd.respond_info("Auto power off globally disabled")
                
        elif option.lower() == 'now':
            # Trigger power off immediately
            gcmd.respond_info("Powering off printer...")
            # Small delay to allow gcode response to be sent
            self.reactor.register_callback(lambda e: self._power_off())
        
        elif option.lower() == 'start':
            # Start the idle timer
            if not self.enabled:
                gcmd.respond_info("Auto power off is globally disabled")
                return
            if self.shutdown_timer is None:
                waketime = self.reactor.monotonic() + self.idle_timeout
                self.countdown_end = self.reactor.monotonic() + self.idle_timeout
                self.shutdown_timer = self.reactor.register_timer(self._check_conditions, waketime)
                gcmd.respond_info("Auto power off timer started")
            else:
                gcmd.respond_info("Auto power off timer already active")
                
        elif option.lower() == 'cancel':
            # Cancel the idle timer
            if self.shutdown_timer is not None:
                self.reactor.unregister_timer(self.shutdown_timer)
                self.shutdown_timer = None
                gcmd.respond_info("Auto power off timer canceled")
            else:
                gcmd.respond_info("No active auto power off timer")
            
        elif option.lower() == 'status':
            # Display current status
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
            gcmd.respond_info("Unrecognized option. Use ON, OFF, START, CANCEL, NOW, or STATUS")

def load_config(config):
    return AutoPowerOff(config)
EOF
print_success "Python module created."

# Create Fluidd configuration file
print_status "Creating Fluidd panel..."
cat > $PRINTER_CONFIG_DIR/fluidd/auto_power_off.cfg << 'EOF'
<!-- auto_power_off.cfg - Fluidd panel for automatic power off -->
<!-- Save this file in ~/printer_data/config/fluidd/auto_power_off.cfg -->

{% set auto_power_off = printer['auto_power_off'] %}

<v-card>
  <v-card-title class="blue-grey darken-1 white--text">
    <v-icon class="white--text">mdi-power-plug-off</v-icon>
    Auto Power Off
  </v-card-title>
  <v-card-text class="py-3">
    <v-layout align-center>
      <v-flex>
        <p class="mb-0">Global status:</p>
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
      Printer will automatically power off in <strong>{{ formatTime(auto_power_off.countdown) }}</strong>
    </p>
    <p v-else class="mb-2 mt-0">
      <v-icon small color="gray">mdi-timer-off-outline</v-icon>
      No active power off timer
    </p>

    <p class="mb-2">
      <v-icon small color="red">mdi-thermometer</v-icon>
      Hotend temperature: <strong>{{ auto_power_off.current_temps.hotend.toFixed(1) }}°C</strong> 
      | Bed: <strong>{{ auto_power_off.current_temps.bed.toFixed(1) }}°C</strong>
    </p>

    <p class="mb-2">
      <v-icon small color="blue">mdi-alert-circle-outline</v-icon>
      Power off will trigger when temperatures are below <strong>{{ auto_power_off.temp_threshold }}°C</strong>
    </p>

    <v-alert
      v-if="auto_power_off.current_temps.hotend > auto_power_off.temp_threshold || auto_power_off.current_temps.bed > auto_power_off.temp_threshold"
      dense
      text
      type="warning"
      class="mt-2 mb-2"
    >
      Temperatures are still too high for power off
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
        Start
      </v-btn>
      <v-btn
        small
        color="error"
        text
        :disabled="!auto_power_off.active"
        @click="sendGcode('AUTO_POWEROFF CANCEL')"
      >
        <v-icon small class="mr-1">mdi-timer-off-outline</v-icon>
        Cancel
      </v-btn>
      <v-spacer></v-spacer>
      <v-btn
        small
        color="error"
        @click="confirmShutdown"
      >
        <v-icon small class="mr-1">mdi-power</v-icon>
        Power Off Now
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
        this.$store.dispatch('server/addEvent', { message: `Auto power off ${this.auto_power_off_enabled ? 'enabled' : 'disabled'}`, type: 'complete' })
        this.$socket.emit('printer.gcode.script', { script: cmd })
      },
      confirmShutdown() {
        this.$store.dispatch('power/createConfirmDialog', { 
          title: 'Power Off Printer',
          text: 'Are you sure you want to power off the printer now?',
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
print_success "Fluidd panel created."

# Ask user if they want to add the configuration to printer.cfg
print_status "Modifying printer.cfg file..."
CONFIG_FILE="$PRINTER_CONFIG_DIR/printer.cfg"

if [ ! -f "$CONFIG_FILE" ]; then
    print_error "printer.cfg file not found at location: $CONFIG_FILE"
    print_warning "You will need to manually add the configuration to your printer.cfg file."
else
    echo "Do you want to automatically add the configuration to the printer.cfg file? [y/N]"
    read -r ADD_CONFIG
    
    if [[ "$ADD_CONFIG" =~ ^[yY][eE]?[sS]?$ ]]; then
        # Check if [auto_power_off] section already exists
        if grep -q "\[auto_power_off\]" "$CONFIG_FILE"; then
            print_warning "The [auto_power_off] section already exists in printer.cfg."
            print_warning "Please check and update the configuration manually."
        else
            # Add configuration to file
            cat >> "$CONFIG_FILE" << 'EOL'

#
# Auto Power Off Configuration
#
[auto_power_off]
idle_timeout: 600     # Idle time in seconds before power off (10 minutes)
temp_threshold: 40    # Temperature threshold in °C (printer considered cool)
power_device: psu_control  # Name of your power device (must match the [power] section)
auto_poweroff_enabled: True  # Enable auto power off by default at startup

[include fluidd/auto_power_off.cfg]  # Include Fluidd panel (comment out if you don't use Fluidd)
EOL
            print_success "Configuration added to printer.cfg file."
        fi
    else
        print_warning "Configuration not added. You will need to add it manually."
    fi
fi

# Ask user if they want to restart Klipper
echo "Do you want to restart Klipper now to apply the changes? [y/N]"
read -r RESTART_KLIPPER

if [[ "$RESTART_KLIPPER" =~ ^[yY][eE]?[sS]?$ ]]; then
    print_status "Restarting Klipper..."
    sudo systemctl restart klipper
    print_success "Klipper restarted."
    
    echo "Wait a few seconds for Klipper to fully restart..."
    sleep 5
    
    # Check if the module was loaded correctly
    if grep -q "Auto Power Off: Module initialized" /tmp/klippy.log; then
        print_success "The Auto Power Off module was loaded successfully!"
    else
        print_warning "Could not verify module loading. Please check Klipper logs."
    fi
else
    print_warning "Klipper was not restarted. Please restart it manually to apply the changes."
    echo "Command to restart: sudo systemctl restart klipper"
fi

echo ""
print_success "Installation complete!"
echo ""
echo -e "${GREEN}=== How to Use ====${NC}"
echo "1. The Auto Power Off panel will be available in the Fluidd interface"
echo "2. The module will automatically activate at the end of each print if configured so"
echo "3. Available GCODE commands:"
echo "   - AUTO_POWEROFF ON    - Globally enable the function"
echo "   - AUTO_POWEROFF OFF   - Globally disable the function"
echo "   - AUTO_POWEROFF START - Manually start the timer"
echo "   - AUTO_POWEROFF CANCEL - Cancel the current timer"
echo "   - AUTO_POWEROFF NOW   - Immediately power off the printer"
echo "   - AUTO_POWEROFF STATUS - Display detailed status"
echo ""
echo "If you encounter any issues, check the Klipper logs with: tail -f /tmp/klippy.log"
echo ""
