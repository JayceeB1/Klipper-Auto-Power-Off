# Klipper Auto Power Off

A Klipper module that automatically powers off your 3D printer after a completed print, once it has cooled down and remained idle for a specified period of time.

![Auto Power Off Panel](images/auto_power_off_panel.png)

## Features

- Automatically shut down your printer after completed prints
- Configurable idle timeout (default: 10 minutes)
- Configurable temperature threshold (default: 40°C)
- Integration with both Fluidd and Mainsail for easy control via UI
- Status monitoring for hotend and bed temperatures
- Manual control with GCODE commands
- Works with any GPIO-controlled power device
- Available in English and French
- Compatible with all Moonraker power device types (GPIO, TP-Link Smartplug, Tasmota, Shelly, etc.)

## Requirements

- Klipper with a properly configured [power GPIO control](https://www.klipper3d.org/Config_Reference.html#output_pin)
- Fluidd or Mainsail (for UI integration)
- A 3D printer with a power control setup

## Support Development

If you find this module useful, consider buying me a coffee to support further development!

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/jayceeB1)

Your support is greatly appreciated and helps keep this project maintained and improved!

## Installation

### Automatic Installation (Recommended)

1. Download the installation script:
   ```bash
   # English version
   wget -O install_auto_power_off.sh https://raw.githubusercontent.com/JayceeB1/klipper-auto-power-off/main/scripts/install_auto_power_off.sh
   
   # French version
   wget -O install_auto_power_off_fr.sh https://raw.githubusercontent.com/JayceeB1/klipper-auto-power-off/main/scripts/install_auto_power_off_fr.sh
   ```

2. Make it executable:
   ```bash
   chmod +x install_auto_power_off.sh
   # or
   chmod +x install_auto_power_off_fr.sh
   ```

3. Run the script:
   ```bash
   ./install_auto_power_off.sh
   # or
   ./install_auto_power_off_fr.sh
   ```

4. Follow the on-screen instructions.

### Manual Installation

1. Copy the `auto_power_off.py` script to your Klipper extras directory:
   ```bash
   cp src/auto_power_off.py ~/klipper/klippy/extras/
   ```

2. Copy the UI panel files based on your interface:
   
   **For Fluidd:**
   ```bash
   mkdir -p ~/printer_data/config/fluidd/
   # English version
   cp ui/fluidd/auto_power_off.cfg ~/printer_data/config/fluidd/
   # French version
   cp ui/fluidd/auto_power_off_fr.cfg ~/printer_data/config/fluidd/auto_power_off.cfg
   ```
   
   **For Mainsail:**
   ```bash
   mkdir -p ~/printer_data/config/mainsail/
   # English version
   cp ui/mainsail/auto_power_off.cfg ~/printer_data/config/mainsail/
   cp ui/mainsail/auto_power_off_panel.cfg ~/printer_data/config/mainsail/
   # French version
   cp ui/mainsail/auto_power_off_fr.cfg ~/printer_data/config/mainsail/
   cp ui/mainsail/auto_power_off_panel_fr.cfg ~/printer_data/config/mainsail/
   ```

3. Add the following to your `printer.cfg` file:
   ```
   [auto_power_off]
   idle_timeout: 600     # Idle time in seconds before power off (10 minutes)
   temp_threshold: 40    # Temperature threshold in °C (printer considered cool)
   power_device: psu_control  # Name of your power device (must match the [power] section)
   auto_poweroff_enabled: True  # Enable auto power off by default at startup

   # For Fluidd:
   [include fluidd/auto_power_off.cfg]
   
   # For Mainsail:
   [include mainsail/auto_power_off.cfg]
   ```

4. Restart Klipper:
   ```bash
   sudo systemctl restart klipper
   ```

## Configuration

The following parameters can be configured in the `[auto_power_off]` section:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `idle_timeout` | 600 | Time in seconds to wait before powering off (after print completed) |
| `temp_threshold` | 40 | Temperature in °C below which it's safe to power off |
| `power_device` | psu_control | Name of your power device (must match the [power] section) |
| `auto_poweroff_enabled` | False | Enable auto power off by default at startup |
| `language` | auto | Language for messages: 'en' for English, 'fr' for French, 'auto' for auto-detection |
| `moonraker_integration` | False | Enable integration with Moonraker's power control (optional) |
| `moonraker_url` | http://localhost:7125 | URL for Moonraker API (optional) |

## Usage

### Fluidd Interface

Once installed, you'll see an "Auto Power Off" panel in your Fluidd interface that allows you to:
- Enable/disable the auto power off feature
- See the countdown timer and current temperatures
- Manually start/cancel the power off timer
- Immediately power off the printer (with confirmation)

### Mainsail Interface

For Mainsail, you'll have access to:
- A set of GCODE commands to control auto power off
- A menu in the interface to access power off functions
- Configurable buttons to control the function (if you set up the GPIOs)

### GCODE Commands

The following GCODE commands are available:

- `AUTO_POWEROFF ON` - Globally enable the function
- `AUTO_POWEROFF OFF` - Globally disable the function
- `AUTO_POWEROFF START` - Manually start the timer
- `AUTO_POWEROFF CANCEL` - Cancel the current timer
- `AUTO_POWEROFF NOW` - Immediately power off the printer
- `AUTO_POWEROFF STATUS` - Display detailed status
- `AUTO_POWEROFF LANGUAGE VALUE=en` - Set language to English
- `AUTO_POWEROFF LANGUAGE VALUE=fr` - Set language to French

### End G-code Integration

To enable auto power off only for specific prints, add this to your slicer's end G-code:

```
AUTO_POWEROFF ON  ; Enable auto power off
AUTO_POWEROFF START  ; Start the countdown timer
```

## Moonraker Integration (Advanced)

Auto Power Off can work in tandem with Moonraker's Power module to offer complete power control:

- **Auto Power Off** handles temperature-based and idle-timeout power off after a print
- **Moonraker Power** can handle power on before printing and support different power device types

This integration allows you to:
- Use SBC GPIO pins or different smart plug types
- Automatically power on the printer when a print is queued
- Automatically restart Klipper after power on
- Maintain protection against power off during printing

### Configuration

1. **Configure the Power module in `moonraker.conf`**:

   ```ini
   [power printer]
   type: gpio                     # Device type: gpio, tplink_smartplug, tasmota, etc.
   pin: gpio27                    # For GPIO only: pin to use
   # address: 192.168.1.123       # For network devices: IP address
   off_when_shutdown: True
   initial_state: off
   on_when_job_queued: True       # Power on when a print is queued
   off_when_job_complete: False   # Let Auto Power Off handle power off
   locked_while_printing: True
   restart_klipper_when_powered: True
   restart_delay: 3
   ```

2. **Enable integration in `printer.cfg`**:

   ```ini
   [auto_power_off]
   idle_timeout: 600              # Idle time in seconds
   temp_threshold: 40             # Temperature threshold in °C
   power_device: printer          # Must match name in [power printer]
   moonraker_integration: True    # Enable Moonraker integration
   moonraker_url: http://localhost:7125  # Moonraker API URL (optional)
   ```

### Expected Behavior

1. When a print is queued, Moonraker powers on the printer.
2. Klipper automatically restarts after power on.
3. The printer cannot be powered off during printing (locked).
4. When the print is complete, Auto Power Off monitors:
   - The configured idle timeout
   - Hotend and bed temperatures
5. Once conditions are met, Auto Power Off powers off the printer.

### Supported Device Types

This integration works with all device types supported by Moonraker, including:
- GPIO pins on Raspberry Pi and other SBCs
- TP-Link Smart Plugs
- Tasmota, Shelly, HomeSeer devices
- And several other options...

See the [Moonraker documentation](https://moonraker.readthedocs.io/en/latest/configuration/#power) for the complete list of options.

### Adding New Languages

The module now supports translations via external language files. To add a new language:

1. Create a new JSON file in the `auto_power_off_langs` directory named after the language code (e.g., `de.json` for German)
2. Copy the structure from an existing language file and translate all the messages
3. Add the new language code to the validation list in the `_configure_language` method
4. The new language will be available using `language: de` in configuration or via GCODE command

## Troubleshooting

If you encounter any issues:

1. Check Klipper logs:
   ```bash
   tail -f /tmp/klippy.log
   ```

2. Verify that your power control is working:
   ```
   QUERY_POWER psu_control  # Replace with your power device name
   ```

3. Check the status of the auto power off module:
   ```
   AUTO_POWEROFF STATUS
   ```

4. Make sure your configuration matches your printer's power setup.

## Language Support

This module is available in:
- English (default)
- French (see [README_FR.md](README_FR.md))

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Inspired by OctoPrint's PSU Control plugin
- Thanks to the Klipper, Fluidd, and Mainsail development teams