# Klipper Auto Power Off

A Klipper module that automatically powers off your 3D printer after a completed print, once it has cooled down and remained idle for a specified period of time.

![Auto Power Off Panel](images/auto_power_off_panel.png)

## Support Development

If you find this module useful, consider buying me a coffee to support further development!

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/jayceeb1)

Your support is greatly appreciated and helps keep this project maintained and improved!

## Features

- Automatically shut down your printer after completed prints
- Configurable idle timeout (default: 10 minutes)
- Configurable temperature threshold (default: 40°C)
- Integration with both Fluidd and Mainsail for easy control via UI
- Status monitoring for hotend and bed temperatures
- Manual control with GCODE commands
- Works with any GPIO-controlled power device
- Available in English and French

## Requirements

- Klipper with a properly configured [power GPIO control](https://www.klipper3d.org/Config_Reference.html#output_pin)
- Fluidd or Mainsail (for UI integration)
- A 3D printer with a power control setup

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

### End G-code Integration

To enable auto power off only for specific prints, add this to your slicer's end G-code:

```
AUTO_POWEROFF ON  ; Enable auto power off
AUTO_POWEROFF START  ; Start the countdown timer
```

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
