# Localization (i18n) Documentation

This directory contains all translation files for the SIS2VD application.

## Translation Workflow

### Adding a New Language

To add support for a new language:

1. Create a new .ts file following the naming convention: `sis2vd_[language_code].ts`
2. Run the update command to populate the file with strings from the source code
3. Translate the strings using Qt Linguist or another translation tool

### Updating Translations

The translation files are generated from the source code using Qt's lupdate tool:

```bash
pyside6-lupdate src/*.py -ts locales/sis2vd_XX.ts
```

Where `XX` is the language code (e.g., `en`, `fr`).

### Compiling Translations

After translating the .ts files, compile them into .qm files using:

```bash
pyside6-lrelease locales/sis2vd_XX.ts -qm locales/sis2vd_XX.qm
```

## File Structure

- `sis2vd_en.ts` - English translation source file
- `sis2vd_fr.ts` - French translation source file
- `sis2vd_XX.ts` - Additional language files (placeholder)
- `sis2vd_XX.qm` - Compiled translation files (not versioned)

## Notes

- The .qm files are compiled binary files and should not be versioned.
- Translation files (.ts) contain the source strings that need to be translated.
- The application will automatically load the appropriate translation based on system locale.