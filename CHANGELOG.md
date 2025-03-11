# Changelog

All notable changes to the Klipper Auto Power Off project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.8] - 2025-03-11

### Added
* New command `AUTO_POWEROFF RESET` to force reset module's internal state
* Periodic device state verification to detect manual power-on
* Timeout mechanism to avoid stuck shutdown state
* Shutdown start timestamp tracking

### Fixed
* Issue preventing power off after manual power-on of the device
* Improved error handling with state reset at each potential failure point
* Stuck shutdown state detection and automatic recovery
* Better handling of device state changes

## [2.0.7] - 2025-03-11

### Fixed
* Install script adds automatically auto_power_off service to moonraker.asvc if the file exists

## [2.0.5] - 2025-03-11

### Added
* Git version detection system to avoid "inferred" versions
* Version exposure in status API for Fluidd/Mainsail interfaces
* Automatic recovery function for corrupted Git repositories

### Fixed
* Correction of case-sensitivity issues in Git repository URLs
* Improved error handling for divergent repository recovery
* Automatic repair of incorrect repository references

### Improved
* More detailed diagnostics for Git repository issues
* Better version persistence between restarts

## [2.0.4] - 2025-03-11

### Fixed
Important Note for Versions Before 2.0.4

If you're using a version before 2.0.4 and experiencing auto-update issues, please be aware that there was a case-sensitivity issue with the GitHub repository URL. The correct URL is https://github.com/JayceeB1/Klipper-Auto-Power-Off.git (with capital K). 
The latest install script will automatically fix this issue.

## [2.0.3] - 2025-03-10

### Fixed
- Improved update manager integration with better error handling
- Fixed repository path detection and initialization
- Added proper cleanup of old update_manager configurations
- Enhanced git repository initialization and file tracking
- Improved user interaction for repository path selection
- Fixed issues with untracked files in the local repository

## [2.0.1] - [2.0.2] - 2025-03-10

### Fixed
- [update_manager auto_power_off] was not added to moonraker.conf when updating manually

## [2.0.0] - 2025-03-10

### Added
- Type annotations throughout the codebase for better maintainability
- Comprehensive exception hierarchy for better error handling
- New enumerations for power off methods, device states, and printer states
- Enhanced diagnostics with detailed logging of error conditions
- Improved network device connectivity checks with configurable retry mechanism
- State tracking to prevent redundant shutdown attempts
- Detection of printer state via multiple sources for better reliability
- Support for clean extension to other languages
- Moonraker update manager integration for seamless updates via the web interface
- Unified install/update script handling both fresh installations and updates
- Automatic backup creation before updates
- Local Git repository creation for Moonraker to manage updates efficiently

### Changed
- Refactored code structure for better maintainability
- Enhanced error reporting with more specific error types
- Improved Moonraker integration with better API error handling
- More robust language detection and persistence
- Better temperature monitoring with fall-back mechanisms
- More informative user notifications
- Enhanced documentation with additional examples

### Fixed
- Issues with network device connectivity checks
- Improved error handling during shutdown process
- More robust MCU status checking
- Potential race conditions during shutdown
- Temperature reading edge cases
- Language detection in various environments

## [1.2.0] - 2024-12-15

### Added
- Network device connectivity testing before power off
- Configurable retries for network devices
- Dry run mode for testing without actual power off
- Enhanced status reporting in Fluidd/Mainsail UI

### Changed
- Improved Moonraker integration
- Better error handling for API calls
- Enhanced temperature monitoring

### Fixed
- Issues with temperature sensing on some printer configurations
- Race conditions during shutdown process

## [1.1.0] - 2024-08-20

### Added
- French language support
- Auto-detection of language from system settings
- Configurable temperature thresholds for different components
- Support for chamber temperature monitoring
- Improved diagnostics

### Changed
- Enhanced Moonraker integration
- Better fallback mechanisms when API calls fail
- UI improvements for Fluidd and Mainsail

### Fixed
- Issues with some smart plug types
- Temperature reporting in UI
- Timer cancellation bugs

## [1.0.0] - 2024-04-10

### Added
- Initial release
- Automatic power off based on temperature and idle time
- Support for Fluidd and Mainsail interfaces
- GCODE commands for manual control
- Configurable timeout and temperature threshold
- Moonraker integration for various power device types
- Support for GPIO and network-based power control