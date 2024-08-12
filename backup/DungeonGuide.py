import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog, colorchooser
import os
import logging
from PIL import Image, ImageTk
import re
from data_handler import load_dungeon_data, save_dungeon_data, load_themes, save_themes, load_preferences, save_preferences, update_status_in_data, get_image_path
from theme_manager import apply_theme, update_locked_state, apply_theme_to_new_window, apply_even_odd_tags
from language_manager import change_language, load_language, get_supported_languages

# Initialize logging
logging.basicConfig(filename='app.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class DungeonTracker(tk.Tk):
    def __init__(self, data, data_file, image_folder, themes_file, language_file):
        super().__init__()
        logging.info("Initializing DungeonTracker application.")
        self.title("FFXIV Duty Tracker")
        self.geometry("1000x700")

        # Initialization of necessary variables
        self.data = data
        self.data_file = data_file
        self.image_folder = image_folder
        self.themes_file = themes_file

        # Load themes and preferences
        self.themes = load_themes(themes_file)
        self.preferences = load_preferences()
        self.current_theme = self.preferences.get('current_theme', list(self.themes.keys())[0] if self.themes else "default")
        self.custom_theme = None

        logging.info(f"Loaded theme: {self.current_theme}")

        # Load language settings
        self.language = load_language(language_file)
        self.language_file = language_file

        # Create the UI elements
        self.create_widgets()

        # Load saved filters
        self.load_filters()

        # Apply the current theme
        apply_theme(self, self.themes.get(self.current_theme, self.default_theme()))

        # Apply the initial locked state colors
        update_locked_state(self.tree)

        logging.info("DungeonTracker initialization complete.")

    def create_widgets(self):
        logging.info("Creating UI widgets.")
        self.create_menu()

        control_frame = tk.Frame(self)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        search_label = tk.Label(control_frame, text=self.language.get("label_search", "Search"))
        search_label.pack(side=tk.LEFT)

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.update_tree)
        search_entry = tk.Entry(control_frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=5)

        reset_button = tk.Button(control_frame, text=self.language.get("button_reset", "Reset"), command=self.reset_status)
        reset_button.pack(side=tk.LEFT, padx=5)

        clear_filters_button = tk.Button(control_frame, text=self.language.get("button_clear_filters", "Clear Filters"), command=self.clear_filters)
        clear_filters_button.pack(side=tk.LEFT, padx=5)

        expand_button = tk.Button(control_frame, text=self.language.get("button_expand_all", "Expand All"), command=self.expand_all)
        expand_button.pack(side=tk.LEFT, padx=5)

        collapse_button = tk.Button(control_frame, text=self.language.get("button_collapse_all", "Collapse All"), command=self.collapse_all)
        collapse_button.pack(side=tk.LEFT, padx=5)

        filter_button = tk.Button(control_frame, text=self.language.get("button_filters", "Filters"), command=self.toggle_filters)
        filter_button.pack(side=tk.LEFT, padx=5)

        toggle_theme_button = tk.Button(control_frame, text=self.language.get("button_toggle_theme", "Toggle Theme"), command=self.open_theme_selector)
        toggle_theme_button.pack(side=tk.LEFT, padx=5)

        self.filter_frame = tk.Frame(self)
        self.filter_frame.pack(fill=tk.X, padx=10, pady=5)
        self.filter_frame.pack_forget()  # Hide by default

        filter_label = tk.Label(self.filter_frame, text=self.language.get("label_filters", "Filters:"))
        filter_label.pack(side=tk.TOP, anchor=tk.W)

        self.filters = {
            "Expansion": ["A Realm Reborn", "Heavensward", "Stormblood", "Shadowbringers", "Endwalker", "Dawntrail"],
            "Level": ["10-15", "15-20", "20-25", "25-30", "35-40", "45-50", "50-55", "55-60", "65-70", "75-80", "85-90", "90-95", "95-100"],
            "Quest Type": ["Main Quest", "Feature Quest"],
            "Duty Type": ["Dungeons", "Trials", "Raids", "Guildhests"],
            "Status": ["Locked", "Unlocked"]
        }

        self.filter_vars = {k: {item: tk.BooleanVar() for item in v} for k, v in self.filters.items()}

        for category, items in self.filter_vars.items():
            cat_frame = tk.Frame(self.filter_frame)
            cat_frame.pack(side=tk.LEFT, padx=10)
            cat_label = tk.Label(cat_frame, text=self.language.get(category, category) + ":")
            cat_label.pack(side=tk.TOP, anchor=tk.W)
            for item, var in items.items():
                chk = tk.Checkbutton(cat_frame, text=item, variable=var, command=self.on_filter_change)
                chk.pack(side=tk.TOP, anchor=tk.W)

        self.tree = ttk.Treeview(self, columns=("Level", "Unlock", "Status"), show="tree headings")
        # self.tree = ttk.Treeview(self, columns=("Level", "Unlock", "Status", "Tags"), show="tree headings") ### For debugging with "Tags"

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tree.heading("#0", text=self.language.get("heading_duty", "Duty"), anchor=tk.W)
        self.tree.heading("Level", text=self.language.get("heading_level", "Level"), anchor=tk.W)
        self.tree.heading("Unlock", text=self.language.get("heading_unlock", "Unlock"), anchor=tk.W)
        self.tree.heading("Status", text=self.language.get("heading_status", "Status"), anchor=tk.W)
        # self.tree.heading("Tags", text=self.language.get("heading_tags", "Tags"), anchor=tk.W)

        self.tree.column("#0", width=300, anchor=tk.W)
        self.tree.column("Level", width=60, anchor=tk.W)
        self.tree.column("Unlock", width=400, anchor=tk.W)
        self.tree.column("Status", width=100, anchor=tk.W)
        # self.tree.column("Tags", width=200, anchor=tk.W)

        self.insert_duties()

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_context_menu)

        # Define the context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label=self.language.get("unlock", "Unlock"), command=self.unlock_duty)
        self.context_menu.add_command(label=self.language.get("info", "Info"), command=self.show_info)

        logging.info("UI widgets created.")

    def _on_mousewheel(self, event):
        self.tree

    def clear_filters(self):
        logging.info("Clearing all filters.")
        for category, items in self.filter_vars.items():
            for item, var in items.items():
                var.set(False)
        self.update_tree()  # Refresh the treeview to show all items

    def create_menu(self):
        logging.info("Creating menu bar.")
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.language.get("menu_file", "File"), menu=file_menu)
        file_menu.add_command(label=self.language.get("menu_export_theme", "Export Theme"), command=self.export_theme)
        file_menu.add_command(label=self.language.get("menu_import_theme", "Import Theme"), command=self.import_theme)
        file_menu.add_command(label=self.language.get("menu_create_theme", "Create Theme"), command=self.open_theme_creator)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.language.get("menu_help", "Help"), menu=help_menu)
        help_menu.add_command(label=self.language.get("menu_change_language", "Change Language"), command=self.create_language_selection_window)
        help_menu.add_command(label=self.language.get("menu_app_help", "Application Help"), command=self.open_help_window)

        logging.info("Menu bar created.")

    def on_filter_change(self):
        logging.debug("Filter changed.")
        self.update_tree()
        self.save_preferences()

    def refresh_ui(self):
        logging.info("Refreshing UI.")
        self.destroy()
        data = load_dungeon_data(self.data_file)
        app = DungeonTracker(data, self.data_file, self.image_folder, self.themes_file, self.language_file)
        app.mainloop()

    def save_preferences(self):
        logging.info("Saving user preferences.")
        preferences = {
            "current_theme": self.current_theme,
            "filters": {k: {item: var.get() for item, var in v.items()} for k, v in self.filter_vars.items()},
            "language_file": self.language_file
        }
        save_preferences(preferences)
        logging.debug(f"Preferences saved: {preferences}")

    def load_filters(self):
        logging.info("Loading filters.")
        saved_filters = self.preferences.get('filters', {})
        for category, items in saved_filters.items():
            if isinstance(items, list):  # Check if 'items' is a list
                for item in items:
                    if category in self.filter_vars and item in self.filter_vars[category]:
                        self.filter_vars[category][item].set(True)
            else:
                for item, value in items.items():
                    if category in self.filter_vars and item in self.filter_vars[category]:
                        self.filter_vars[category][item].set(value)
        self.update_tree()
        logging.info("Filters loaded.")

    def toggle_filters(self):
        logging.debug("Toggling filter panel.")
        if self.filter_frame.winfo_ismapped():
            self.filter_frame.pack_forget()
        else:
            self.filter_frame.pack(fill=tk.X, padx=10, pady=5)

    def expand_all(self):
        logging.info("Expanding all tree nodes.")
        for item in self.tree.get_children():
            self.tree.item(item, open=True)
            for sub_item in self.tree.get_children(item):
                self.tree.item(sub_item, open=True)
        logging.info("All tree nodes expanded.")

    def collapse_all(self):
        logging.info("Collapsing all tree nodes.")
        for item in self.tree.get_children():
            self.tree.item(item, open=False)
            for sub_item in self.tree.get_children(item):
                self.tree.item(sub_item, open=False)
        logging.info("All tree nodes collapsed.")

    def insert_duties(self):
        logging.info("Inserting duties into the treeview.")
        for expansion in self.data:
            exp_id = self.tree.insert("", "end", text=expansion["expansion"], open=True, tags=("expansion",))
            for duty_type in expansion["duties"]:
                type_id = self.tree.insert(exp_id, "end", text=duty_type["type"], open=True)
                for i, duty in enumerate(duty_type["duties"]):
                    # Initial insert without applying even/odd row tags
                    tags = duty.get("Tags", [])
                    self.tree.insert(type_id, "end", text=duty["Name"],
                                    values=(duty["Level"], duty["Unlock"], duty["Status"]),
                                    tags=tags)
        
        # Apply even/odd tags after all items are inserted
        apply_even_odd_tags(self.tree, self.data)

        logging.info("Duties inserted and even/odd tags applied.")

    def toggle_unlock(self, item):
        logging.debug(f"Toggling unlock status for item: {self.tree.item(item, 'text')}")

        values = self.tree.item(item, "values")
        current_status = values[2]

        new_status = "Unlocked" if current_status == "Locked" else "Locked"

        # Update the tags: add 'unlocked' and remove 'evenrow'/'oddrow' if unlocking
        tags = list(self.tree.item(item, "tags"))
        if new_status == "Unlocked":
            if "evenrow" in tags:
                tags.remove("evenrow")
            if "oddrow" in tags:
                tags.remove("oddrow")
            if "unlocked" not in tags:
                tags.append("unlocked")
        else:
            # When locking again, determine the correct even/odd tag
            if "unlocked" in tags:
                tags.remove("unlocked")
            row_index = self.tree.index(item)
            tag = "evenrow" if row_index % 2 == 0 else "oddrow"
            tags = [tag]

        # Apply the updated tags to the Treeview item
        self.tree.item(item, tags=tags)

        # Update the status in the Treeview values
        self.tree.item(item, values=(values[0], values[1], new_status))

        # Update the JSON data with the new status and tags
        self.update_json_data(item, new_status, tags)

        # Save the updated JSON data to the file
        save_dungeon_data(self.data_file, self.data)

        logging.info(f"Item {self.tree.item(item, 'text')} status toggled to {new_status}.")

    def update_json_data(self, item, new_status, new_tags):
        """
        Update the JSON data for the specific item to reflect the new status and tags.
        """
        for expansion in self.data:
            for duty_type in expansion["duties"]:
                for duty in duty_type["duties"]:
                    if duty["Name"] == self.tree.item(item, "text"):
                        duty["Status"] = new_status
                        duty["Tags"] = new_tags
                        logging.debug(f"Updated JSON for {duty['Name']}: Status={new_status}, Tags={new_tags}")
                        return

    def reset_status(self):
        logging.info("Resetting status of all duties to 'Locked'.")
        for expansion in self.data:
            for duty_type in expansion['duties']:
                for duty in duty_type['duties']:
                    duty["Status"] = "Locked"
                    duty["Tags"] = []

        for item in self.tree.get_children():
            self.tree.item(item, open=True)
            for sub_item in self.tree.get_children(item):
                self.tree.item(sub_item, open=True)
                for duty_item in self.tree.get_children(sub_item):
                    self.tree.item(duty_item, values=(self.tree.item(duty_item, "values")[0],
                                                    self.tree.item(duty_item, "values")[1],
                                                    "Locked"))
                    row_index = self.tree.index(duty_item)
                    tag = "evenrow" if row_index % 2 == 0 else "oddrow"
                    self.tree.item(duty_item, tags=[tag])
                    # Update the JSON data to reflect the status and tags
                    self.update_json_data(duty_item, "Locked", [tag])

        save_dungeon_data(self.data_file, self.data)
        self.update_tree()
        logging.info("Status of all duties reset to 'Locked'.")

    def update_tree(self, *args):
        logging.info("Updating the treeview with current filters and search query.")
        search_query = self.search_var.get().lower()

        selected_filters = {
            category: {item for item, var in items.items() if var.get()}
            for category, items in self.filter_vars.items()
        }

        for item in self.tree.get_children():
            self.tree.delete(item)

        for expansion in self.data:
            if selected_filters["Expansion"] and expansion["expansion"] not in selected_filters["Expansion"]:
                continue
            exp_id = self.tree.insert("", "end", text=expansion["expansion"], open=True, tags=("expansion",))
            for duty_type in expansion["duties"]:
                if selected_filters["Duty Type"] and duty_type["type"] not in selected_filters["Duty Type"]:
                    continue
                type_id = self.tree.insert(exp_id, "end", text=duty_type["type"], open=True)
                for i, duty in enumerate(duty_type["duties"]):
                    if selected_filters["Quest Type"] and duty["Quest Type"] not in selected_filters["Quest Type"]:
                        continue
                    if selected_filters["Status"] and duty["Status"] not in selected_filters["Status"]:
                        continue
                    level_range = self.get_level_range(duty["Level"])
                    if selected_filters["Level"] and level_range not in selected_filters["Level"]:
                        continue
                    duty_name = duty["Name"].lower()
                    if self.match_query(duty_name, search_query):
                        tags = duty.get("Tags", [])
                        item = self.tree.insert(type_id, "end", text=duty["Name"],
                                                values=(duty["Level"], duty["Unlock"], duty["Status"], ", ".join(tags)),
                                                tags=tags)
                if not self.tree.get_children(type_id):
                    self.tree.delete(type_id)
            if not self.tree.get_children(exp_id):
                self.tree.delete(exp_id)
        logging.info("Treeview update complete.")
        apply_even_odd_tags(self.tree, self.data)
        update_locked_state(self.tree)

    def get_level_range(self, level):
        level = int(level)
        ranges = ["10-15", "15-20", "20-25", "25-30", "35-40", "45-50", "50-55", "55-60", "65-70", "75-80", "85-90", "90-95", "95-100"]
        for r in ranges:
            start, end = map(int, r.split('-'))
            if start <= level <= end:
                return r
        return ""

    def match_query(self, text, query):
        if query == "":
            return True
        if "*" in query:
            pattern = re.compile(query.replace("*", ".*"))
            return pattern.search(text) is not None
        if '"' in query:
            parts = query.split('"')
            return any(part in text for part in parts if part)
        return query in text

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
        logging.debug(f"Context menu shown for item: {self.tree.item(item, 'text')}")

    def unlock_duty(self):
        item = self.tree.selection()[0]
        logging.debug(f"Unlocking duty for item: {self.tree.item(item, 'text')}")
        self.toggle_unlock(item)

    def create_language_selection_window(self):
        logging.info("Creating language selection window.")
        language_selector = tk.Toplevel(self)
        language_selector.title("Select Language")

        # Create widgets first
        buttons = []
        languages = get_supported_languages()

        for lang_name, lang_file in languages.items():
            button = tk.Button(language_selector, text=lang_name, command=lambda lf=lang_file: change_language(self, lf))
            button.pack(fill=tk.X, padx=10, pady=5)
            buttons.append(button)

        # Apply the current theme to the new window after all widgets are created
        apply_theme_to_new_window(language_selector, self.themes.get(self.current_theme, self.default_theme()))

        # Explicitly update all buttons with the theme
        for button in buttons:
            button.configure(bg=self.themes[self.current_theme].get("button_bg", "#f0f0f0"),
                            fg=self.themes[self.current_theme].get("fg", "#000000"))

        logging.info("Language selection window created.")
    
    def open_help_window(self):
        logging.info("Opening help window.")
        help_window = tk.Toplevel(self)
        help_window.title(self.language.get("help_window_title", "Application Help"))

        # Create widgets first
        text_widget = tk.Text(help_window, wrap=tk.WORD, height=20, width=80)
        text_widget.insert(tk.END, """
            Welcome to the FFXIV Duty Tracker!

            Navigation:
            - Use the search bar to filter duties by name.
            - Expand All: Expands all categories in the list.
            - Collapse All: Collapses all categories in the list.
            - Filters: Allows you to filter duties by expansion, level, quest type, duty type, and status.
            - Toggle Theme: Allows you to change the current theme.

            Changing Settings:
            - Use the File menu to export or import themes, or create a new theme.
            - Use the Help menu to change the application language or view this help guide.

            Button Functions:
            - Search: Type in the search bar and results will filter automatically.
            - Reset: Resets the status of all duties to 'Locked'.
            - Expand All: Expands all nodes in the tree view.
            - Collapse All: Collapses all nodes in the tree view.
            - Filters: Toggle visibility of the filter options.
            - Toggle Theme: Opens a window to select a different theme.

            Right-click on a duty in the list to view additional options, such as unlocking the duty or viewing more information about it.
        """)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(padx=10, pady=10)

        close_button = tk.Button(help_window, text=self.language.get("close", "Close"), command=help_window.destroy)
        close_button.pack(pady=10)

        # Apply the current theme to the new window after all widgets are created
        apply_theme_to_new_window(help_window, self.themes.get(self.current_theme, self.default_theme()))

        # Explicitly update the button with the theme
        close_button.configure(bg=self.themes[self.current_theme].get("button_bg", "#f0f0f0"),
                            fg=self.themes[self.current_theme].get("fg", "#000000"))

        logging.info("Help window opened.")

    def show_info(self):
        item = self.tree.selection()[0]
        duty_name = self.tree.item(item, "text")
        logging.info(f"Showing info for duty: {duty_name}")

        # Fetch the image corresponding to the selected duty
        unlock_text = self.tree.item(item, "values")[1]
        image_name = "".join(c for c in unlock_text if c.isalnum()).lower() + ".jpg"
        
        # Construct the path based on folder structure and expansion
        parent_type_id = self.tree.parent(item)
        parent_expansion_id = self.tree.parent(parent_type_id)
        expansion = self.tree.item(parent_expansion_id, "text")
        duty_type = self.tree.item(parent_type_id, "text")

        image_path = os.path.join(self.image_folder, expansion, duty_type, image_name)

        if not os.path.exists(image_path):
            messagebox.showinfo(self.language.get("info", "Info"), self.language.get("no_image_found", "No image found for this duty."))
            logging.warning(f"No image found for duty: {duty_name} at {image_path}")
            return

        info_window = tk.Toplevel(self)
        info_window.title(duty_name)

        # Create widgets first
        img = Image.open(image_path)
        photo = ImageTk.PhotoImage(img)
        img_label = tk.Label(info_window, image=photo)
        img_label.image = photo  # Keep a reference to avoid garbage collection
        img_label.pack()

        close_button = tk.Button(info_window, text=self.language.get("close", "Close"), command=info_window.destroy)
        close_button.pack(pady=10)

        # Apply the theme to the new window after all widgets are created
        apply_theme_to_new_window(info_window, self.themes.get(self.current_theme, self.default_theme()))

        # Explicitly update the button with the theme
        close_button.configure(bg=self.themes[self.current_theme].get("button_bg", "#f0f0f0"),
                            fg=self.themes[self.current_theme].get("fg", "#000000"))

        logging.info(f"Info window opened for duty: {duty_name}")

    def open_theme_selector(self):
        logging.info("Opening theme selector.")
        theme_selector = tk.Toplevel(self)
        theme_selector.title(self.language.get("select_theme", "Select Theme"))

        # Create widgets first
        buttons = []
        for theme_name in self.themes:
            button = tk.Button(theme_selector, text=theme_name, command=lambda tn=theme_name: self.change_theme(tn))
            button.pack(fill=tk.X, padx=10, pady=5)
            buttons.append(button)

        # Apply the current theme to the new window after all widgets are created
        apply_theme_to_new_window(theme_selector, self.themes.get(self.current_theme, self.default_theme()))

        # Explicitly update all buttons with the theme
        for button in buttons:
            button.configure(bg=self.themes[self.current_theme].get("button_bg", "#f0f0f0"),
                            fg=self.themes[self.current_theme].get("fg", "#000000"))

        logging.info("Theme selector opened.")

    def change_theme(self, theme_name):
        logging.info(f"Changing theme to: {theme_name}")
        self.current_theme = theme_name
        apply_theme(self, self.themes.get(theme_name, self.default_theme()))
        self.save_preferences()
        logging.info(f"Theme changed to: {theme_name}")

    def open_theme_creator(self):
        logging.info("Opening theme creator.")
        theme_creator = tk.Toplevel(self)
        theme_creator.title(self.language.get("create_theme", "Create Theme"))

        # Create the widgets first
        theme_name_label = tk.Label(theme_creator, text=self.language.get("theme_name", "Theme Name"))
        theme_name_label.pack(padx=10, pady=5)
        
        theme_name_entry = tk.Entry(theme_creator)
        theme_name_entry.pack(padx=10, pady=5)

        color_attributes = ["bg", "fg", "button_bg", "entry_bg", "menu_bg", "selected_bg"]
        color_buttons = {}

        def pick_color(attribute):
            color = tk.colorchooser.askcolor()[1]  # This opens the color chooser
            if color:
                color_buttons[attribute].configure(bg=color)
                theme[attribute] = color
                apply_theme(self, theme)  # Apply preview to the main window

        theme = {}  # Temporary theme dictionary to hold changes
        for attribute in color_attributes:
            attr_label = tk.Label(theme_creator, text=self.language.get(attribute, attribute))
            attr_label.pack(padx=10, pady=5)
            
            color_button = tk.Button(theme_creator, text=self.language.get("select_color", "Select Color"),
                                    command=lambda a=attribute: pick_color(a))
            color_button.pack(padx=10, pady=5)
            color_buttons[attribute] = color_button

        save_button = tk.Button(theme_creator, text=self.language.get("save_theme", "Save Theme"),
                                command=lambda: self.save_new_theme(theme_name_entry.get(), theme, theme_creator))
        save_button.pack(padx=10, pady=10)

        cancel_button = tk.Button(theme_creator, text=self.language.get("cancel", "Cancel"),
                                command=theme_creator.destroy)
        cancel_button.pack(padx=10, pady=5)

        # Apply the theme to the new window after all widgets are created
        apply_theme_to_new_window(theme_creator, self.themes.get(self.current_theme, self.default_theme()))

        logging.info("Theme creator opened.")

    def export_theme(self):
        logging.info("Exporting current theme.")
        theme_name = self.current_theme
        if theme_name not in self.themes:
            messagebox.showerror(self.language.get("error", "Error"), self.language.get("theme_not_found", "Theme not found."))
            logging.error(f"Theme not found for export: {theme_name}")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".json",
                                                 filetypes=[("JSON Files", "*.json")],
                                                 title=self.language.get("save_theme_as", "Save Theme As"))
        if file_path:
            theme_data = self.themes[theme_name]
            save_themes(file_path, {theme_name: theme_data})
            messagebox.showinfo(self.language.get("success", "Success"), self.language.get("theme_exported", "Theme exported successfully."))
            logging.info(f"Theme exported: {theme_name} to {file_path}")

    def import_theme(self):
        logging.info("Importing theme.")
        file_path = filedialog.askopenfilename(defaultextension=".json",
                                               filetypes=[("JSON Files", "*.json")],
                                               title=self.language.get("import_theme", "Import Theme"))
        if file_path:
            imported_themes = load_themes(file_path)
            if imported_themes:
                self.themes.update(imported_themes)
                self.save_preferences()
                messagebox.showinfo(self.language.get("success", "Success"), self.language.get("theme_imported", "Theme imported successfully."))
                logging.info(f"Themes imported from: {file_path}")
            else:
                messagebox.showerror(self.language.get("error", "Error"), self.language.get("import_failed", "Failed to import theme."))
                logging.error("Failed to import themes from the file.")

    def toggle_item(self, item):
        logging.debug(f"Toggling item: {item}")
        self.tree.item(item, open=not self.tree.item(item, "open"))

    def on_double_click(self, event):
        item = self.tree.selection()[0]
        logging.info(f"Double-clicked on item: {self.tree.item(item, 'text')}")
        self.toggle_unlock(item)

    def default_theme(self):
        logging.debug("Loading default theme.")
        return {
            "bg": "#f0f0f0",
            "fg": "#000000",
            "tree_evenrow_bg": "#ffffff",
            "tree_oddrow_bg": "#f9f9f9",
            "unlocked_bg": "#d0ffd6",
            "disabled_bg": "#cccccc",
            "disabled_fg": "#888888",
            "button_bg": "#f0f0f0",
            "entry_bg": "#ffffff",
            "menu_bg": "#f0f0f0",
            "selected_bg": "#3399ff"
        }

if __name__ == "__main__":
    data_file = "duties.json"
    themes_file = "themes.json"
    language_file = "en.json"
    image_folder = "QuestInfo"

    data = load_dungeon_data(data_file)
    app = DungeonTracker(data, data_file, image_folder, themes_file, language_file)
    app.mainloop()
