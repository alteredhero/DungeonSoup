import json
import logging
import os

# Initialize logging
logging.basicConfig(filename='app.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def load_dungeon_data(file_path):
    """
    Load dungeon data from a JSON file.
    :param file_path: The path to the JSON file containing dungeon data.
    :return: A dictionary containing the loaded dungeon data.
    """
    logging.info(f"Loading dungeon data from {file_path}.")
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        logging.info(f"Dungeon data loaded successfully from {file_path}.")
        return data
    except Exception as e:
        logging.error(f"Failed to load dungeon data from {file_path}: {e}")
        return {}

def save_dungeon_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logging.info(f"Dungeon data saved to {file_path}")

def load_themes(file_path):
    """
    Load themes from a JSON file.
    :param file_path: The path to the JSON file containing themes.
    :return: A dictionary containing the loaded themes.
    """
    logging.info(f"Loading themes from {file_path}.")
    try:
        with open(file_path, 'r') as f:
            themes = json.load(f)
        logging.info(f"Themes loaded successfully from {file_path}.")
        return themes
    except Exception as e:
        logging.error(f"Failed to load themes from {file_path}: {e}")
        return {}

def save_themes(file_path, themes):
    """
    Save themes to a JSON file.
    :param file_path: The path to the JSON file where the themes will be saved.
    :param themes: The themes to be saved.
    """
    logging.info(f"Saving themes to {file_path}.")
    try:
        with open(file_path, 'w') as f:
            json.dump(themes, f, indent=4)
        logging.info(f"Themes saved successfully to {file_path}.")
    except Exception as e:
        logging.error(f"Failed to save themes to {file_path}: {e}")

def load_preferences():
    """
    Load user preferences from a JSON file.
    :return: A dictionary containing the loaded preferences.
    """
    logging.info("Loading user preferences.")
    try:
        with open('preferences.json', 'r') as f:
            preferences = json.load(f)
        logging.info("User preferences loaded successfully.")
        return preferences
    except Exception as e:
        logging.error(f"Failed to load preferences: {e}")
        return {}

def save_preferences(preferences):
    """
    Save user preferences to a JSON file.
    :param preferences: The preferences to be saved.
    """
    logging.info("Saving user preferences.")
    try:
        with open('preferences.json', 'w') as f:
            json.dump(preferences, f, indent=4)
        logging.info("User preferences saved successfully.")
    except Exception as e:
        logging.error(f"Failed to save preferences: {e}")

def update_status_in_data(data, duty_name, new_status):
    """
    Update the status of a specific duty in the data.
    :param data: The entire data structure containing all duties.
    :param duty_name: The name of the duty to update.
    :param new_status: The new status to apply to the duty.
    """
    logging.info(f"Updating status for duty: {duty_name} to {new_status}.")
    for expansion in data:
        for duty_type in expansion['duties']:
            for duty in duty_type['duties']:
                if duty['Name'] == duty_name:
                    duty['Status'] = new_status
                    logging.info(f"Status for {duty_name} updated to {new_status}.")
                    return
    logging.warning(f"Duty {duty_name} not found. Status update failed.")

def save_state(file_path, state_data):
    """
    Save the application state to a JSON file.
    :param file_path: The path to the JSON file where the state will be saved.
    :param state_data: The state data to be saved.
    """
    logging.info(f"Saving application state to {file_path}.")
    try:
        with open(file_path, 'w') as f:
            json.dump(state_data, f, indent=4)
        logging.info(f"Application state saved successfully to {file_path}.")
    except Exception as e:
        logging.error(f"Failed to save application state to {file_path}: {e}")

def get_image_path(image_folder, expansion, duty_type, unlock_text):
    """
    Construct the path to the image file based on the provided expansion, duty type, and unlock text.
    :param image_folder: Root folder where all images are stored.
    :param expansion: The expansion name.
    :param duty_type: The type of duty (Dungeons, Trials, Raids).
    :param unlock_text: The unlock text from the duty.
    :return: The full path to the image file, or None if the image doesn't exist.
    """
    # Sanitize the unlock text to create the image filename
    image_name = "".join(c for c in unlock_text if c.isalnum()).lower() + ".jpg"
    
    # Construct the image path
    image_path = os.path.join(image_folder, expansion, duty_type, image_name)
    
    # Check if the image exists
    if os.path.exists(image_path):
        return image_path
    else:
        return None
