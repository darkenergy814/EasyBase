undo_button = ["Ctrl+z"]
prev_button = ["a", "Left"]
next_button = ["d", "Right"]
checkbox_button = ["Space"]

shortcut_map = {
    "undo_button": (undo_button, "remove_landmark"),
    "prev_button": (prev_button, "prev_clicked"),
    "next_button": (next_button, "next_clicked"),
    "checkbox_button": (checkbox_button, "toggle_checkbox"),
}