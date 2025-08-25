from PySide6.QtWidgets import (
    QApplication, QWidget, QToolButton, QMenu, QVBoxLayout
)
from PySide6.QtCore import Qt, Signal


class CheckableDropdown(QToolButton):
    selectionChanged = Signal(list)  # emits list of selected items

    def __init__(self, text, parent=None):
        super().__init__(parent)

        self.setText(text)
        self.setPopupMode(QToolButton.InstantPopup)

        self.menu_list = QMenu(self)
        self.setMenu(self.menu_list)

        self.action_list = []
        self.items = []

    def setItems(self, items):
        self.menu_list.clear()
        self.action_list.clear()
        self.items = items
        for item in items:
            action = self.menu_list.addAction(item)
            action.setCheckable(True)
            action.toggled.connect(self._emit_selection_changed)
            self.action_list.append(action)  

    def _emit_selection_changed(self):
        """Emit signal when one of the list items is toggled"""
        selected = [a.text() for a in self.action_list if a.isChecked()]
        self.selectionChanged.emit(selected)

    def setSelectedItems(self, items):
        """Programmatically set which items are selected."""
        for action in self.action_list:
            action.setChecked(action.text() in items)
        self._emit_selection_changed()

    def selectedItems(self):
        return [a.text() for a in self.action_list if a.isChecked()]
