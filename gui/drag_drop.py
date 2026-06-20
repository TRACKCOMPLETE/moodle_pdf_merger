from pathlib import Path
from tkinterdnd2 import DND_FILES


class DragDropHandler:
    def __init__(self, widget, callback):
        self.widget = widget
        self.callback = callback

        self.widget.drop_target_register(DND_FILES)
        self.widget.dnd_bind("<<Drop>>", self._on_drop)

    def _on_drop(self, event):
        paths = self.widget.tk.splitlist(event.data)

        for path in paths:
            path = Path(path)

            if path.suffix.lower() != ".zip":
                continue

            self.callback(path)