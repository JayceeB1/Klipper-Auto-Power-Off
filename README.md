# Klipper Auto Power Off

A Klipper module that automatically powers off your 3D printer after a completed print, once it has cooled down and remained idle for a specified period of time.

![Auto Power Off Panel](images/auto_power_off_panel.png)

## Features

- Automatically shut down your printer after completed prints
- Configurable idle timeout (default: 10 minutes)
- Configurable temperature threshold (default: 40°C)
- Integration with Fluidd for easy control via UI
- Status monitoring for hotend and bed temperatures
- Manual control with GCODE commands
- Works with any GPIO-controlled power device

## Requirements

- Klipper with a properly configured [power GPIO control](https://www.klipper3d.org/Config_Reference.html#output_pin)
- Fluidd (for UI integration)
- A 3D printer with a power control setup

## Installation

### Automatic Installation (Recommended)

1. Download the installation script:
   ```bash
   wget -O install_auto_power_off.sh https://raw.githubusercontent.com/yourusername/klipper-auto-power-off/main/install_auto_power_off.sh
   ```

2. Make it executable:
   ```bash
   chmod +x install_auto_power_off.sh
   ```

3. Run the script:
   ```bash
   ./install_auto_power_off.sh
   ```

4. Follow the on-screen instructions.

### Manual Installation

1. Copy the `auto_power_off.py` script to your Klipper extras directory:
   ```bash
   cp auto_power_off.py ~/klipper/klippy/extras/
   ```

2. Copy the Fluidd panel file:
   ```bash
   mkdir -p ~/printer_data/config/fluidd/
   cp auto_power_off.cfg ~/printer_data/config/fluidd/
   ```

3. Add the following to your `printer.cfg` file:
   ```
   [auto_power_off]
   idle_timeout: 600     # Idle time in seconds before power off (10 minutes)
   temp_threshold: 40    # Temperature threshold in °C (printer considered cool)
   power_device: psu_control  # Name of your power device (must match the [power] section)
   auto_poweroff_enabled: True  # Enable auto power off by default at startup

   [include fluidd/auto_power_off.cfg]  # Include Fluidd panel (comment if you don't use Fluidd)
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

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Inspired by OctoPrint's PSU Control plugin
- Thanks to the Klipper and Fluidd development teams
