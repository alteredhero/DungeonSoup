import tkinter as tk
from tkinter import ttk
import logging
from data_handler import save_dungeon_data

# Set up logging
logging.basicConfig(filename='app.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def apply_theme(root_widget, theme):
    """
    Apply the given theme to the root widget and all of its children.
    :param root_widget: The root widget of the application (usually the main window).
    :param theme: Dictionary containing theme settings.
    """
    logging.info(f"Applying theme to root widget: {root_widget}")
    root_widget.configure(bg=theme.get("bg"))

    # Apply theme to all children widgets
    update_widget_theme(root_widget, theme)

def update_widget_theme(widget, theme):
    for child in widget.winfo_children():
        if isinstance(child, (tk.Frame, tk.LabelFrame, tk.Toplevel)):
            logging.debug(f"Updating Frame/LabelFrame/Toplevel: {child}")
            child.configure(bg=theme.get("bg"))
        elif isinstance(child, tk.Label):
            logging.debug(f"Updating Label: {child}")
            child.configure(bg=theme.get("bg"), fg=theme.get("fg", "#000000"))
        elif isinstance(child, tk.Button):
            logging.debug(f"Updating Button: {child}")
            child.configure(bg=theme.get("button_bg", theme.get("bg")), fg=theme.get("fg", "#000000"))
        elif isinstance(child, tk.Entry):
            logging.debug(f"Updating Entry: {child}")
            child.configure(bg=theme.get("entry_bg", theme.get("bg")), fg=theme.get("fg", "#000000"))
        elif isinstance(child, tk.Menu):
            logging.debug(f"Updating Menu: {child}")
            child.configure(bg=theme.get("menu_bg", theme.get("bg")), fg=theme.get("fg", "#000000"))
        elif isinstance(child, tk.Checkbutton):
            logging.debug(f"Updating Checkbutton: {child}")
            child.configure(bg=theme.get("bg"), fg=theme.get("fg", "#000000"), selectcolor=theme.get("button_bg", theme.get("bg")))
        elif isinstance(child, ttk.Treeview):
            logging.debug(f"Updating Treeview: {child}")
            update_treeview_theme(child, theme)
        elif isinstance(child, ttk.Button):
            logging.debug(f"Updating ttk.Button: {child}")
            style = ttk.Style()
            style.configure("TButton", background=theme.get("button_bg", theme.get("bg")), foreground=theme.get("fg", "#000000"))
        elif isinstance(child, ttk.Label):
            logging.debug(f"Updating ttk.Label: {child}")
            style = ttk.Style()
            style.configure("TLabel", background=theme.get("bg"), foreground=theme.get("fg", "#000000"))

        # Recurse into child widgets
        update_widget_theme(child, theme)

def apply_theme_to_new_window(window, theme):
    logging.info(f"Applying theme to new window: {window}")
    
    # Treat the new window as the root widget and apply the theme
    apply_theme(window, theme)

    # Force window to redraw and update all widgets
    window.update_idletasks()

def update_treeview_theme(treeview, theme):
    logging.info(f"Updating Treeview theme for: {treeview}")
    style = ttk.Style()

    # Configure the general style of the Treeview
    style.configure("Treeview",
                    background=theme.get("bg"),
                    foreground=theme.get("fg", "#000000"),
                    fieldbackground=theme.get("bg"))

    # Configure the row colors for the Treeview
    style.map("Treeview", background=[("selected", theme.get("selected_bg", "#3399ff"))])

    # Configure the alternating row colors (odd and even rows)
    treeview.tag_configure("evenrow", background=theme.get("tree_evenrow_bg", "#ffffff"))
    treeview.tag_configure("oddrow", background=theme.get("tree_oddrow_bg", "#f9f9f9"))

    # Configure the "unlocked" tag style
    treeview.tag_configure("unlocked", background=theme.get("unlocked_bg", "lightgreen"), foreground=theme.get("disabled_fg", "#888888"))

    # Apply the style to the Treeview
    treeview.configure(style="Treeview")

def update_locked_state(treeview):
    """
    Update the visual state of locked/unlocked items in the Treeview.
    This method will iterate through all items and update their color based on their status.
    """
    logging.info("Updating locked state for Treeview.")

    # Get all top-level items
    top_level_items = treeview.get_children()
    
    # Iterate over all top-level items and their descendants
    for item in top_level_items:
        update_item_color(treeview, item)
        
    logging.info("Finished updating locked state.")

def update_item_color(treeview, item):
    # Fetch the values of the item (assuming the third column is 'Status')
    values = treeview.item(item, 'values')
    
    # Print or log the values to verify the function is working as expected
    print(f"Processing item: {item}, Values: {values}")
    logging.debug(f"Processing item: {item}, Values: {values}")

    if len(values) > 3 and values[3] == 'Unlocked':
        # Apply the 'unlocked' tag which turns the line green and disables it
        treeview.item(item, tags=("unlocked",))
        logging.debug(f"Item {item} is unlocked and marked green.")
    else:
        logging.debug(f"Item {item} is not unlocked, no color change applied.")
        
    # Recurse through child items and update their state
    for child in treeview.get_children(item):
        update_item_color(treeview, child)

def apply_even_odd_tags(treeview, data):
    for expansion in data:
        expansion_id = treeview.get_children()[0]  # Get the expansion item from the treeview

        # Now process each duty type under this expansion
        for duty_type in treeview.get_children(expansion_id):
            row_count = 0  # Reset row count for each duty type

            for duty_index, duty_item_id in enumerate(treeview.get_children(duty_type)):
                tags = treeview.item(duty_item_id, 'tags')

                # Only apply evenrow/oddrow tags if the duty is not unlocked
                if 'unlocked' not in tags:
                    tag = 'evenrow' if row_count % 2 == 0 else 'oddrow'
                    treeview.item(duty_item_id, tags=(tag,))
                    row_count += 1  # Increment row count only for non-unlocked items
                else:
                    tag = 'unlocked'
                    treeview.item(duty_item_id, tags=('unlocked',))

                # Update the JSON data with the correct tag
                duty_name = treeview.item(duty_item_id, 'text')
                update_tags_in_json(data, expansion['expansion'], treeview.item(duty_type, 'text'), duty_name, tag)

def apply_even_odd_tags_recursive(treeview, item, idx):
    """
    Recursively apply even/odd tags to child items in the Treeview.
    """
    for child_idx, child in enumerate(treeview.get_children(item)):
        # Apply even/odd tags but don't overwrite the "unlocked" tag
        tags = treeview.item(child, 'tags')
        if "unlocked" not in tags:
            row_tag = "evenrow" if (idx + child_idx) % 2 == 0 else "oddrow"
            treeview.item(child, tags=(row_tag,))
        apply_even_odd_tags_recursive(treeview, child, idx + child_idx)

def update_tags_in_json(data, expansion_name, duty_type_name, duty_name, new_tag):
    """
    Update the tags in the JSON data for a specific duty.
    :param data: The JSON data.
    :param expansion_name: The name of the expansion.
    :param duty_type_name: The name of the duty type.
    :param duty_name: The name of the duty.
    :param new_tag: The new tag to apply (either 'evenrow' or 'oddrow').
    """
    for expansion in data:
        if expansion['expansion'] == expansion_name:
            for duty_type in expansion['duties']:
                if duty_type['type'] == duty_type_name:
                    for duty in duty_type['duties']:
                        if duty['Name'] == duty_name:
                            # Remove 'evenrow' and 'oddrow' tags if they exist
                            duty['Tags'] = [tag for tag in duty.get('Tags', []) if tag not in ('evenrow', 'oddrow')]
                            # Add the new tag
                            duty['Tags'].append(new_tag)
                            return
