


# Localization (i18n) of the SIS2VD application

Add localization (i18n) to the existing PySide6 application (SIS2VD)
using the native Qt system (QTranslator + .ts/.qm files), with
an onboarding screen for language selection on first launch.

## Technical context:
- The app already exists in src/main.py and src/ui.py
- Current structure: QMainWindow with the UI widgets described previously

## Step 1: Wrapping existing text

For this step, we need to identify and wrap all visible strings in the
user interface (UI) with the Qt mechanism `self.tr("...")`. This will
allow Qt to localize these texts for different languages.

### Objectives:
- [ ] Go through all .py files in the src/ folder
- [ ] Wrap every string visible in the UI (labels, buttons, tooltips, error
      messages, window titles, placeholder text) with `self.tr("...")`
- [ ] Do NOT wrap strings that are not user-facing (debug logs, dictionary
      keys, file names, paths)
- [ ] Maintain consistency with the existing Qt/Breeze style
- [ ] Use appropriate type hints and comments

### Context:
The texts we need to wrap are those that will be displayed to the end
user. This includes:
- Label texts (QLabel)
- Button texts (QPushButton)
- Tooltips (setToolTip)
- Window titles (setWindowTitle)
- Error and confirmation messages
- Placeholders in input fields

## Step 2: Translation file structure

For this step, we will create the structure needed to manage the
translation files (.ts and .qm) in the project.

### Objectives:
- [ ] Create a `locales/` folder at the project root
- [ ] Prepare the structure for at least two languages: `en` (English,
      default/source language) and `fr` (French)
- [ ] Create the .ts files named `locales/sis2vd_en.ts` and
      `locales/sis2vd_fr.ts`
- [ ] Set up the translation file management system
- [ ] Ensure cross-platform compatibility

### Context:
Qt translation files are split into two types:
- .ts files: source text files containing the strings to be translated
- .qm files: compiled files used by the application at runtime

The `locales/` folder will be used to store everything related to
localization, including the .ts and .qm files.

## Step 3: Language preference system

For this step, we will build a system to manage the user's language
preferences, storing them in a local JSON file.

### Objectives:
- [ ] Create the file src/settings.py
- [ ] Implement a Settings class to manage user preferences
- [ ] Use QStandardPaths.AppDataLocation for a clean, cross-platform path
- [ ] Expose the get_language() / set_language(lang_code) methods
- [ ] Expose the has_completed_onboarding() / set_onboarding_completed() methods
- [ ] Ensure data persists between application launches

### Context:
The preferences system must allow the application to:
- Store the language chosen by the user
- Remember whether the user has already completed onboarding
- Provide a simple mechanism for reading and writing these preferences
- Work cross-platform (Linux, Windows, macOS)

The configuration file will be stored in an appropriate location
depending on the operating system:
- Linux: ~/.local/share/SIS2VD/settings.json
- Windows: %APPDATA%/SIS2VD/settings.json
- macOS: ~/Library/Application Support/SIS2VD/settings.json

## Step 4: Onboarding screen (first launch only)

For this step, we will create an onboarding screen that lets the user
choose their language on the first launch of the application.

### Objectives:
- [ ] Create the file src/onboarding_dialog.py
- [ ] Implement an OnboardingDialog class inheriting from QDialog
- [ ] Create a simple interface with the app logo/title and a welcome message
- [ ] Add a component for selecting the language (QComboBox or buttons)
- [ ] Set English as the default language
- [ ] Implement a "Continue" button that saves the choice via Settings
- [ ] Ensure the dialog cannot be closed without making a choice
- [ ] Close the dialog after the choice is saved

### Context:
The onboarding screen is shown only on the application's first launch.
It lets the user choose their preferred language. The dialog must be
modal and prevent the user from continuing without making a choice.

The UI elements must include:
- An app logo or title
- A welcome message
- A language selector (radio buttons or QComboBox)
- A "Continue" button to confirm the choice

## Step 5: Loading logic in main.py

For this step, we will implement the translation-loading logic in the
application's main file.

### Objectives:
- [ ] Check in main.py whether onboarding has been completed via
      Settings.has_completed_onboarding()
- [ ] If False: show OnboardingDialog before the MainWindow
- [ ] Load the .qm file corresponding to the saved language
- [ ] Install the QTranslator on the QApplication instance before creating
      the MainWindow
- [ ] Handle error cases silently (fallback to English)
- [ ] Ensure loading happens before the main interface is displayed

### Context:
main.py is the application's entry point. It must:
1. Check whether the user has already completed onboarding
2. If not, show the onboarding dialog
3. Load the appropriate translation based on user preferences
4. Create and display the main window

Translation loading must happen before the MainWindow is created, to
avoid untranslated text.

## Step 6: Accessing settings from other screens

For this step, we will implement a simple way to access the language
choice from other screens in the application.

### Objectives:
- [ ] Add a feature to reopen the language selector later
- [ ] Create a "Settings" menu or an option within an existing menu
- [ ] Implement a mechanism to relaunch OnboardingDialog or an equivalent
      dialog
- [ ] Show a "Restart required" message if changing the language requires
      an application restart
- [ ] Ensure consistency with the existing interface

### Context:
Once the user has chosen a language, they may want to change it later.
We need to provide a simple way to access this setting within the
application.

This could be:
- A "Settings" menu in the menu bar
- An option in a context menu
- A button in the main window

The system must handle cases where changing the language requires
restarting the application.

## Step 7: Documentation

For this step, we will create the documentation needed to manage
translations in the project.

### Objectives:
- [ ] Create a locales/README.md file
- [ ] Explain the workflow for adding a new language
- [ ] Document the process for updating translations
- [ ] Explain how to use pyside6-lupdate and pyside6-lrelease
- [ ] Mention the required Qt Linguist tools
- [ ] Update requirements.txt if necessary

### Context:
Documentation is essential to help developers understand how to manage
translations in the project. It must include:

1. The commands used to generate .ts files from the source code
2. How to use Qt Linguist for translations
3. Compiling .ts files into .qm files
4. How to add a new language to the project

The README.md file should explain:
- How to run the translation update tool:
  `pyside6-lupdate src/*.py -ts locales/sis2vd_XX.ts`
- How to open the files in Qt Linguist for translation
- How to compile the files:
  `pyside6-lrelease locales/sis2vd_XX.ts -qm locales/sis2vd_XX.qm`

## Step 8: .ts and .qm files

For this step, we will manage the translation files (.ts and .qm) in
the project.

### Objectives:
- [ ] Create the .ts files for the supported languages
- [ ] Do not attempt to translate the content of the .ts files ourselves
- [ ] Leave the source strings in English, as in the .ts files
- [ ] Do not version the compiled .qm files in git
- [ ] Add the .qm files to .gitignore
- [ ] Document that they must be generated at build time or via GitHub
      Actions

### Context:
.ts files contain the strings to be translated and are automatically
generated from the source code. Translations are done manually in Qt
Linguist.

.qm files are compiled files that must not be versioned, since they are
generated from the .ts files.

The workflow should include:
1. Generating the .ts files with pyside6-lupdate
2. Translating the .ts files in Qt Linguist
3. Compiling the .ts files into .qm with pyside6-lrelease

### User validation:
Please confirm that you want to proceed with Step 8: .ts and .qm files.