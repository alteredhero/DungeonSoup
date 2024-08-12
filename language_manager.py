import os
import json
import logging
import tkinter as tk
from tkinter import messagebox
from data_handler import save_preferences

# Set up logging
logging.basicConfig(filename='app.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

LANGUAGE_FOLDER = "languages"

def load_language(language_file):
    logging.info(f"Loading language from file: {language_file}")
    path = os.path.join(LANGUAGE_FOLDER, language_file)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as file:
            logging.debug(f"Language file {language_file} loaded successfully")
            return json.load(file)
    logging.warning(f"Language file {language_file} not found")
    return {}

def save_language(language_file, data):
    logging.info(f"Saving language to file: {language_file}")
    path = os.path.join(LANGUAGE_FOLDER, language_file)
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)
    logging.debug(f"Language file {language_file} saved successfully")

def get_supported_languages():
    logging.info("Fetching list of supported languages")
    return {
        "English": "en.json",
        "Spanish": "es.json",
        "French": "fr.json",
        "German": "de.json",
        "Japanese": "ja.json",
        "Chinese": "zh.json",
        "Korean": "ko.json"
    }

def change_language(app, language_file):
    """
    Change the application's language and refresh the UI.
    :param app: The main application instance.
    :param language_file: The file path of the selected language file.
    """
    logging.info(f"Changing language to: {language_file}")
    app.language_file = language_file
    app.language = load_language(language_file)
    app.save_preferences()
    logging.debug(f"Language changed to {language_file}, refreshing UI")
    app.refresh_ui()

def apply_language(app, language_file):
    logging.info(f"Applying language: {language_file}")
    app.language_file = os.path.join(LANGUAGE_FOLDER, language_file)
    app.language = load_language(app.language_file)
    save_preferences({"language_file": app.language_file})
    logging.debug(f"Language applied: {language_file}, refreshing UI")

    # Notify the main app to refresh the UI
    app.refresh_ui()
