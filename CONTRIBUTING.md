# Contributing to Klipper Auto Power Off

Thank you for considering contributing to Klipper Auto Power Off! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by the following code of conduct:

- Be respectful and inclusive of all contributors regardless of background or identity
- Use welcoming and inclusive language
- Be open to different viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to see if the problem has already been reported. When creating a bug report, include as much detailed information as possible to help maintainers reproduce and fix the issue.

#### Bug Report Template

```
**Description:**
A clear and concise description of the bug.

**To Reproduce:**
Steps to reproduce the behavior:
1. Configure '...'
2. Run command '...'
3. See error

**Expected behavior:**
A clear description of what you expected to happen.

**Actual behavior:**
What actually happened instead.

**Screenshots:**
If applicable, add screenshots to help explain your problem.

**Environment:**
 - Klipper version: [e.g., v0.10.0]
 - UI: [e.g., Fluidd, Mainsail]
 - Hardware: [e.g., Raspberry Pi 4, BTT CB1]
 - Power control method: [e.g., GPIO, TPLink Smart Plug]
 - Printer: [e.g., Ender 3, Voron 2.4]

**Additional context:**
Add any other context about the problem here, such as custom configurations.
```

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide a clear and detailed explanation of the feature you'd like to see, including:

- A clear and specific description of the enhancement
- The motivation behind it (why it would be useful)
- How it should work from a user perspective
- Any implementation ideas you may have

### Pull Requests

We actively welcome your pull requests! Here's the process:

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs or added new features, update the documentation
4. Ensure the test suite passes and your code follows the coding conventions
5. Make sure your code is well commented (in both English and French for user-facing strings)
6. Issue that pull request!

#### Pull Request Template

```
**Description:**
Clear description of what this PR addresses or implements.

**Type of change:**
- [ ] Bug fix
- [ ] New feature
- [ ] Enhancement to existing features
- [ ] Documentation update
- [ ] Translation improvement

**Tested on:**
- UI: [e.g., Fluidd, Mainsail, Both]
- Hardware: [e.g., Raspberry Pi 4, BTT CB1]

**Checklist:**
- [ ] I have tested this code with both Fluidd and Mainsail (if applicable)
- [ ] I have added necessary documentation or updated existing documentation
- [ ] I have added/updated translations for both English and French
- [ ] My code follows the coding conventions of this project
```

## Coding Conventions

### Python Code Style

- Follow PEP 8 guidelines
- Use 4 spaces for indentation (no tabs)
- Use descriptive variable and function names
- Maximum line length of 100 characters
- Add docstrings to all functions and classes
- Include comments for complex logic
- For user-facing strings, use bilingual comments if appropriate

### JavaScript Code Style (UI Components)

- Use 2 spaces for indentation
- Use camelCase for variable and function names
- Document functions with JSDoc-style comments
- Keep UI components clean and focused on a single responsibility

### Bilingual Compatibility

For user-facing content:

- Include bilingual comments in Python code where appropriate
- For UI elements, ensure both English and French versions are updated
- When adding new user-facing strings, add them to both language versions

## Testing

Before submitting a pull request, please:

1. Test your changes on both Fluidd and Mainsail interfaces if applicable
2. Verify functionality on different printer setups if possible
3. Test the installation script(s)
4. Check for any regressions in existing functionality

### Recommended Testing Process

1. Install the modified code on a test system
2. Verify the module loads correctly in Klipper
3. Test the basic functionality (enabling/disabling, starting/stopping timers)
4. Test the automatic power-off functionality after a print
5. Test integration with different power control methods if possible

## Documentation and Translation

### Documentation

- Keep README.md and README_FR.md in sync with each other
- Document new features and changes in both files
- Update installation instructions if needed
- Add screenshots for new UI features when appropriate

### Translations

- All user-facing strings should be available in both English and French
- UI panel files should be maintained in both languages
- Keep translations natural rather than literal (focus on meaning over word-for-word translation)
- For new features, implement both language versions simultaneously

## Working with UI Components

### Fluidd Components

- Test changes with the latest Fluidd version
- Follow Vuetify design patterns for UI components
- Ensure the panel renders correctly on both desktop and mobile

### Mainsail Components

- Test changes with the latest Mainsail version
- Follow Mainsail's UI patterns and guidelines
- Ensure compatibility with Mainsail's configuration system

## Getting Help

If you need assistance with your contribution, feel free to:

- Open an issue with questions
- Comment on existing issues for clarification
- Reach out via the project's discussions section

Thank you for your contributions to making Klipper Auto Power Off better for everyone!