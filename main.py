import yaml
import re
import copy
import logging
from ipaddress import IPv4Network
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import (
    QAction,
    QIcon,
    QColor,
    QIntValidator,
    QRegularExpressionValidator,
    QPainter,
)
import databuilder

logging.basicConfig(level=logging.INFO)


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def data(self, index, role):
        item = self._data[index.row()][index.column()]

        if role == Qt.ItemDataRole.DisplayRole:
            out = ""
            for key, value in item.items():
                if key not in ["spansize", "color"]:
                    if key == "network":
                        logging.debug(f"Network is {value}")
                        out += f"{value}\n"
                    else:
                        out += f"{key}: {value}\n"
            return out

        if role == Qt.ItemDataRole.BackgroundRole:
            value = self._data[index.row()][index.column()]
            if clr := item.get("color"):
                logging.debug(f"color = {clr}")
                return QColor(clr)

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])


class SubnetView(QtWidgets.QWidget):
    """Individual subnet view widget for displaying one subnet"""

    # Class-level validator singleton
    _matchcidr = QRegularExpression(
        r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}"
        r"([0-9]|[1-9][0-9]|1[0-9]{2}|"
        r"2[0-4][0-9]|25[0-5])(\/(3[0-2]|[1-2][0-9]|[0-9]))$"
    )
    _cidr_validator = None

    @classmethod
    def get_cidr_validator(cls):
        """Get singleton CIDR validator"""
        if cls._cidr_validator is None:
            cls._cidr_validator = QRegularExpressionValidator(cls._matchcidr)
        return cls._cidr_validator

    def __init__(self, parent_window, subnet_name="New Subnet"):
        super().__init__()
        self.parent_window = parent_window
        self.subnet_name = subnet_name
        self.zero32 = QIntValidator(0, 32)
        self.auto_update = True

        self.fields = {}
        self.networks = {}
        self.uFieldsCntrls = {}
        self.data = []
        self.model = None
        self.compiled_patterns = {}  # Cache for compiled regex patterns
        self.span_info = []  # Cache for span positions

        self.setup_ui()

    def setup_ui(self):
        """Setup the UI components for this subnet view"""
        # Table view
        self.table = QtWidgets.QTableView()
        self.table.clicked.connect(self.show_selection)

        # Network Configuration Group
        network_group = QtWidgets.QGroupBox("Network Configuration")
        network_layout = QtWidgets.QGridLayout()

        self.labelNetwork = QtWidgets.QLabel("Network:")
        self.displayNetwork = QtWidgets.QLineEdit("192.168.1.0/24")
        self.displayNetwork.setMaxLength(18)
        self.displayNetwork.setValidator(self.get_cidr_validator())

        self.labelStart = QtWidgets.QLabel("Start Prefix:")
        self.displayStart = QtWidgets.QLineEdit("24")
        self.displayStart.setMaxLength(2)
        self.displayStart.setMaximumWidth(40)
        self.displayStart.setValidator(self.zero32)

        self.labelEnd = QtWidgets.QLabel("End Prefix:")
        self.displayEnd = QtWidgets.QLineEdit("26")
        self.displayEnd.setMaximumWidth(40)
        self.displayEnd.setMaxLength(2)
        self.displayEnd.setValidator(self.zero32)

        self.btnGenerate = QtWidgets.QPushButton("Generate")
        self.btnGenerate.clicked.connect(self.generate)

        network_layout.addWidget(self.labelNetwork, 0, 0)
        network_layout.addWidget(self.displayNetwork, 0, 1, 1, 2)
        network_layout.addWidget(self.labelStart, 1, 0)
        network_layout.addWidget(self.displayStart, 1, 1)
        network_layout.addWidget(self.labelEnd, 1, 2)
        network_layout.addWidget(self.displayEnd, 1, 3)
        network_layout.addWidget(self.btnGenerate, 2, 0, 1, 4)
        network_group.setLayout(network_layout)

        # Selected Subnet Group
        subnet_group = QtWidgets.QGroupBox("Selected Subnet")
        subnet_layout = QtWidgets.QVBoxLayout()

        cidr_layout = QtWidgets.QHBoxLayout()
        self.label_cidr = QtWidgets.QLabel("CIDR:")
        self.cidr = QtWidgets.QLineEdit()
        self.cidr.setReadOnly(True)
        cidr_layout.addWidget(self.label_cidr)
        cidr_layout.addWidget(self.cidr)

        button_layout = QtWidgets.QHBoxLayout()
        self.updateIcon = QIcon("icons/block--arrow.png")
        self.updateBtn = QtWidgets.QPushButton(self.updateIcon, "Update")
        self.updateBtn.clicked.connect(self.update_networks_data)

        self.deleteIcon = QIcon("icons/cross.png")
        self.deleteBtn = QtWidgets.QPushButton(self.deleteIcon, "Delete")
        self.deleteBtn.clicked.connect(self.delete_record)

        self.plusIcon = QIcon("icons/application-plus-black.png")
        self.plusBtn = QtWidgets.QPushButton(self.plusIcon, "Add Field")
        self.plusBtn.clicked.connect(self.add_user_field)

        button_layout.addWidget(self.updateBtn)
        button_layout.addWidget(self.deleteBtn)
        button_layout.addWidget(self.plusBtn)

        subnet_layout.addLayout(cidr_layout)
        subnet_layout.addLayout(button_layout)
        subnet_group.setLayout(subnet_layout)

        # Fields Group
        fields_group = QtWidgets.QGroupBox("Subnet Details")
        self.fieldlayout = QtWidgets.QFormLayout()
        fields_group.setLayout(self.fieldlayout)

        # Left panel - combine all sections vertically
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(network_group)
        left_layout.addWidget(subnet_group)
        left_layout.addWidget(fields_group)
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(350)

        # Main layout - simple horizontal split
        main_layout = QtWidgets.QHBoxLayout()
        main_layout.addWidget(left_panel)
        main_layout.addWidget(self.table, 1)  # Table gets stretch factor

        self.setLayout(main_layout)

    def add_user_fields_to_form(self):
        logging.debug("add_user_fields_to_form()")
        self.update_user_fields()
        for key, value in self.uFieldsCntrls.items():
            self.fieldlayout.addRow(key, value)

    def update_user_fields(self):
        logging.debug("update_user_fields()")
        for fieldname in self.fields.keys():
            if self.fields[fieldname]["controlType"] == "lineEdit":
                self.uFieldsCntrls[fieldname] = QtWidgets.QLineEdit()
                self.uFieldsCntrls[fieldname].editingFinished.connect(self.autoUpdate)
            if self.fields[fieldname]["controlType"] == "checkbox":
                self.uFieldsCntrls[fieldname] = QtWidgets.QCheckBox()

    def clear_user_layout(self):
        logging.debug("clear_user_layout")
        rowCount = self.fieldlayout.rowCount()
        for x in range(rowCount - 1, -1, -1):
            self.fieldlayout.removeRow(x)

    def compile_field_patterns(self):
        """Compile regex patterns for all fields for better performance"""
        self.compiled_patterns = {}
        for field_name, field_data in self.fields.items():
            colormap = field_data.get("colorMap", {})
            if colormap:
                self.compiled_patterns[field_name] = {
                    pattern: re.compile(pattern) for pattern in colormap.keys()
                }

    def check_field(self, cidr: dict):
        logging.debug("check_field()")
        for fieldname in self.networks.get(cidr).keys():
            if fieldname not in self.fields.keys():
                entry = {
                    fieldname: {
                        "controlType": "lineEdit",
                        "colorMap": {},
                        "show": False,
                    }
                }
                self.fields.update(entry)

    def find_fields(self):
        logging.debug("find_fields()")
        for cidr in self.networks.keys():
            self.check_field(cidr)

    def update_networks_data(self):
        logging.debug("update_networks_data()")
        if self.cidr:
            net = self.cidr.text()
            logging.debug(f"update_networks_data: updating {net}")
            self.networks[net] = {}
            logging.debug("update_networks_data: iterating over form fields")
            for fldname, val in self.uFieldsCntrls.items():
                newvalue = val.text()
                logging.debug(f"newvalue is {newvalue}")
                logging.debug(f"update_networks_data: {fldname} is {newvalue}")
                if self.fields[fldname]["controlType"] == "lineEdit":
                    self.networks[net][fldname] = newvalue
                    logging.debug(f" networks is now: {self.networks}")
                elif self.fields[fldname]["controlType"] == "checkbox":
                    if val.checkState() == Qt.CheckState.Checked:
                        self.fields[net][fldname] = True

    def add_user_field(self):
        logging.debug("add_user_fields()")
        newName, ok = QtWidgets.QInputDialog.getText(self, "New field name", "Name")
        if newName and ok:
            fieldData = {
                "controlType": "lineEdit",
                "colorMap": {},
                "colorWeight": 1,
                "show": False,
            }
            self.fields[newName] = fieldData
            logging.debug(f"self.fields is now {self.fields}")
            self.uFieldsCntrls[newName] = QtWidgets.QLineEdit()
            self.fieldlayout.addRow(newName, self.uFieldsCntrls[newName])
            self.uFieldsCntrls[newName].editingFinished.connect(self.autoUpdate)
            logging.debug(f"fields[{newName}] is {self.fields[newName]}")
            # Recompile patterns when field added
            self.compile_field_patterns()

    def delete_record(self):
        logging.debug("delete_record()")
        key = self.cidr.text()
        if self.networks.get(key):
            self.networks.pop(key)
        self.clearUfields()

    def autoUpdate(self):
        logging.debug("autoUpdate()")
        if self.auto_update:
            self.update_networks_data()

    def clearUfields(self):
        logging.debug("clearufields()")
        for key in self.uFieldsCntrls.keys():
            if type(self.uFieldsCntrls.get(key)) == QtWidgets.QLineEdit:
                self.uFieldsCntrls[key].setText("")
            elif type(self.fields.get(key)) == QtWidgets.QCheckBox:
                self.uFieldsCntrls[key] == Qt.CheckState.Unchecked

    def getcellvalue(self):
        cellValue = self.table.selectedIndexes()[0]
        selectedDisplay = self.model.data(cellValue, Qt.ItemDataRole.DisplayRole)
        selected_cidr = selectedDisplay.split()[0]
        return selected_cidr

    def show_selection(self):
        logging.debug("show_selection()")
        self.clearUfields()
        cellValue = self.getcellvalue()
        self.cidr.setText(cellValue)
        data = self.networks.get(cellValue, {})
        logging.debug(f"show_selection: Populating user fields with {data}")
        logging.debug(f"Into these user fields {self.uFieldsCntrls.keys()}")
        for name in data:
            if type(self.uFieldsCntrls.get(name)) == QtWidgets.QLineEdit:
                text = data.get(name, "")
                self.uFieldsCntrls[name].setText(text)
            if type(self.uFieldsCntrls.get(name)) == QtWidgets.QCheckBox:
                val = data.get(name, Qt.CheckState.Unchecked)
                self.uFieldsCntrls[name].setCheckState(val)

    def setFillcolor(
        self, fieldName: str, value_in: str, currentColor: str, currentWeight: int
    ) -> tuple:
        logging.debug("setFillcolor()")
        logging.debug(f"inbound color and weight is {currentColor} {currentWeight}")
        logging.debug(f"Getting color for {fieldName}")
        color = ""
        weight = 0
        colormap = self.fields[fieldName]["colorMap"]
        for pattern in colormap.keys():
            if re.match(rf"{pattern}", value_in):
                logging.debug(f"match on {pattern}")
                color = self.fields[fieldName]["colorMap"].get(pattern)
                logging.debug(f"color is {color}")
                weight = self.fields[fieldName].get("colorWeight")
                logging.debug(f"weight is {weight}")
            if color and (weight > currentWeight):
                logging.debug(f"color and weight are now {color} {weight}")
                return (color, weight)
        else:
            logging.debug(f"color and weight remain {currentColor} {weight}")
            return (currentColor, currentWeight)

    def getCidrDetails(self, cidr, cell) -> dict:
        return cell.get("network", {})

    def setCellColor(self, property, value, cell):
        fillweight = 0
        cell["color"], weight = self.setFillcolor(
            property, value, cell.get("color"), fillweight
        )

    def updateCell(self):
        """Update cells with network data and colors"""
        # Early exit if no network data
        if not self.networks:
            return

        for row in self.data:
            for cell in row:
                # Use walrus operator for efficiency
                if cellNetwork := cell.get("network"):
                    if networkdetails := self.networks.get(cellNetwork):
                        for property, value in networkdetails.items():
                            # Cache field lookup
                            field_info = self.fields.get(property, {})
                            if field_info.get("show", False):
                                cell[property] = value
                            self.setCellColor(property, value, cell)

    def generate(self):
        logging.debug("generate()")
        start = int(self.displayStart.text())
        end = int(self.displayEnd.text())
        net = IPv4Network(self.displayNetwork.text(), strict=False)
        net = databuilder.check_cidr(net, start)

        # Get data and span info from optimized builder
        self.data, self.span_info = databuilder.build_display_list(net, start, end)
        self.updateCell()

        # Update model in place instead of recreating
        if self.model is None:
            self.model = TableModel(self.data)
            self.table.setModel(self.model)
        else:
            self.model._data = self.data
            self.model.layoutChanged.emit()

        # Clear and set spans using cached info
        self.table.clearSpans()
        for row, col, span in self.span_info:
            self.table.setSpan(row, col, span, 1)

    def load_data(self, fields, networks):
        """Load field and network data into this view"""
        self.clear_user_layout()
        self.fields = fields
        self.networks = networks
        self.find_fields()
        self.add_user_fields_to_form()
        # Compile patterns after loading for performance
        self.compile_field_patterns()

    def get_data(self):
        """Return the current fields and networks data"""
        return {"fields": self.fields, "networks": self.networks}


class FieldColorSettingsDialog(QtWidgets.QDialog):
    """Dialog for managing field and color settings"""

    def __init__(self, subnet_view, parent=None):
        super().__init__(parent)
        self.subnet_view = subnet_view
        self.setWindowTitle("Field & Color Settings")
        self.setMinimumSize(700, 500)
        self.setup_ui()

    def setup_ui(self):
        """Setup the settings dialog UI"""
        layout = QtWidgets.QVBoxLayout()

        # Field selector
        field_group = QtWidgets.QGroupBox("Select Field")
        field_layout = QtWidgets.QHBoxLayout()

        self.field_combo = QtWidgets.QComboBox()
        self.field_combo.addItems(self.subnet_view.fields.keys())
        self.field_combo.currentTextChanged.connect(self.load_field_settings)

        add_field_btn = QtWidgets.QPushButton("Add New Field")
        add_field_btn.clicked.connect(self.add_new_field)

        field_layout.addWidget(QtWidgets.QLabel("Field:"))
        field_layout.addWidget(self.field_combo, 1)
        field_layout.addWidget(add_field_btn)
        field_group.setLayout(field_layout)

        # Field properties group
        props_group = QtWidgets.QGroupBox("Field Properties")
        props_layout = QtWidgets.QFormLayout()

        self.show_checkbox = QtWidgets.QCheckBox()
        self.weight_spin = QtWidgets.QSpinBox()
        self.weight_spin.setRange(0, 100)

        props_layout.addRow("Show in cells:", self.show_checkbox)
        props_layout.addRow("Color weight:", self.weight_spin)
        props_group.setLayout(props_layout)

        # Color mapping group
        color_group = QtWidgets.QGroupBox("Color Patterns")
        color_layout = QtWidgets.QVBoxLayout()

        # Color mapping table
        self.color_table = QtWidgets.QTableWidget()
        self.color_table.setColumnCount(3)
        self.color_table.setHorizontalHeaderLabels(
            ["Pattern (regex)", "Color", "Actions"]
        )
        self.color_table.horizontalHeader().setStretchLastSection(False)
        self.color_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.color_table.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self.color_table.horizontalHeader().setSectionResizeMode(
            2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )

        add_color_btn = QtWidgets.QPushButton("Add Color Pattern")
        add_color_btn.clicked.connect(self.add_color_pattern)

        color_layout.addWidget(self.color_table)
        color_layout.addWidget(add_color_btn)
        color_group.setLayout(color_layout)

        # Dialog buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_and_accept)
        button_box.rejected.connect(self.reject)

        # Add all to main layout
        layout.addWidget(field_group)
        layout.addWidget(props_group)
        layout.addWidget(color_group, 1)
        layout.addWidget(button_box)

        self.setLayout(layout)

        # Load first field if available
        if self.field_combo.count() > 0:
            self.load_field_settings(self.field_combo.currentText())

    def load_field_settings(self, field_name):
        """Load settings for the selected field"""
        if not field_name or field_name not in self.subnet_view.fields:
            return

        field_data = self.subnet_view.fields[field_name]

        # Load properties
        self.show_checkbox.setChecked(field_data.get("show", False))
        self.weight_spin.setValue(field_data.get("colorWeight", 1))

        # Load color mappings
        self.color_table.setRowCount(0)
        colormap = field_data.get("colorMap", {})

        for pattern, color in colormap.items():
            self.add_color_row(pattern, color)

    def add_color_row(self, pattern="", color=""):
        """Add a row to the color mapping table"""
        row = self.color_table.rowCount()
        self.color_table.insertRow(row)

        # Pattern input
        pattern_edit = QtWidgets.QLineEdit(pattern)
        self.color_table.setCellWidget(row, 0, pattern_edit)

        # Color button
        color_btn = QtWidgets.QPushButton(color if color else "Choose Color")
        color_btn.setStyleSheet(f"background-color: {color};" if color else "")
        color_btn.clicked.connect(lambda checked, r=row: self.choose_color(r))
        self.color_table.setCellWidget(row, 1, color_btn)

        # Delete button
        delete_btn = QtWidgets.QPushButton("Delete")
        delete_btn.clicked.connect(lambda checked, r=row: self.delete_color_row(r))
        self.color_table.setCellWidget(row, 2, delete_btn)

    def add_color_pattern(self):
        """Add a new color pattern row"""
        self.add_color_row()

    def choose_color(self, row):
        """Open color picker for a row"""
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            color_name = color.name()
            btn = self.color_table.cellWidget(row, 1)
            btn.setText(color_name)
            btn.setStyleSheet(f"background-color: {color_name};")

    def delete_color_row(self, row):
        """Delete a color pattern row"""
        self.color_table.removeRow(row)

    def add_new_field(self):
        """Add a new field to the configuration"""
        field_name, ok = QtWidgets.QInputDialog.getText(
            self, "New Field", "Enter field name:"
        )

        if ok and field_name:
            if field_name in self.subnet_view.fields:
                QtWidgets.QMessageBox.warning(
                    self, "Duplicate Field", f"Field '{field_name}' already exists."
                )
                return

            # Create new field
            self.subnet_view.fields[field_name] = {
                "controlType": "lineEdit",
                "colorMap": {},
                "colorWeight": 1,
                "show": False,
            }

            # Add to combo and select it
            self.field_combo.addItem(field_name)
            self.field_combo.setCurrentText(field_name)

    def save_and_accept(self):
        """Save all settings and close dialog"""
        current_field = self.field_combo.currentText()
        if not current_field:
            self.accept()
            return

        # Save current field settings
        field_data = self.subnet_view.fields[current_field]

        # Save properties
        field_data["show"] = self.show_checkbox.isChecked()
        field_data["colorWeight"] = self.weight_spin.value()

        # Save color mappings
        colormap = {}
        for row in range(self.color_table.rowCount()):
            pattern_widget = self.color_table.cellWidget(row, 0)
            color_widget = self.color_table.cellWidget(row, 1)

            if pattern_widget and color_widget:
                pattern = pattern_widget.text().strip()
                color = color_widget.text()

                if pattern and color and color != "Choose Color":
                    colormap[pattern] = color

        field_data["colorMap"] = colormap

        self.accept()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IP-Visualizer")
        self.setGeometry(50, 50, 1000, 1200)
        self.openfile = ""
        self.autoSave = True

        # Create central widget and tab widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.tabCloseRequested.connect(self.close_tab)

        # Setup toolbar
        toolbar = QtWidgets.QToolBar("Tool Bar Title")
        self.addToolBar(toolbar)

        newIcon = QIcon("icons/new-text.png")
        newAction = QAction(newIcon, "New", self)
        newAction.setStatusTip("Start a new blank file")
        newAction.triggered.connect(self.new_file)

        newTabIcon = QIcon("icons/application-plus-black.png")
        newTabAction = QAction(newTabIcon, "New Tab", self)
        newTabAction.setStatusTip("Add a new subnet tab")
        newTabAction.triggered.connect(self.new_tab)

        loadIcon = QIcon("icons/database--plus.png")
        loadAction = QAction(loadIcon, "Load", self)
        loadAction.setStatusTip("Load Data!")
        loadAction.triggered.connect(self.load_save_data)

        saveicon = QIcon("icons/disk-return.png")
        saveAction = QAction(saveicon, "Save", self)
        saveAction.setStatusTip("save data to file")
        saveAction.triggered.connect(self.save)

        saveAsicon = QIcon("icons/disk--arrow.png")
        saveAsAction = QAction(saveAsicon, "Save As", self)
        saveAsAction.setStatusTip("Save as a New File")
        saveAsAction.triggered.connect(self.saveAs)

        printIcon = QIcon("icons/printer.png")
        printAction = QAction(printIcon, "Print", self)
        printAction.setStatusTip("Print current tab")
        printAction.triggered.connect(self.print)

        aboutIcon = QIcon("icons/question-button.png")
        aboutAction = QAction(aboutIcon, "About", self)
        aboutAction.setStatusTip("Not Implemented")

        settingsIcon = QIcon("icons/wheel.png")
        settingsAction = QAction(settingsIcon, "Settings", self)
        settingsAction.setStatusTip("Settings")
        settingsAction.triggered.connect(self.settings)

        toolbar.addAction(newAction)
        toolbar.addAction(newTabAction)
        toolbar.addAction(loadAction)
        toolbar.addAction(saveAction)
        toolbar.addAction(saveAsAction)
        toolbar.addAction(printAction)
        toolbar.addAction(settingsAction)
        toolbar.addAction(aboutAction)

        self.setStatusBar(QtWidgets.QStatusBar(self))

        # Setup default fields before creating tabs
        self.defaultFields = {
            "Name": {
                "controlType": "lineEdit",
                "colorMap": {r"\w": "green"},
                "colorWeight": 1,
                "show": True,
            }
        }

        # Setup layout with tab widget
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tabWidget)
        central_widget.setLayout(layout)

        # Create initial tab
        self.new_tab()

    def new_file(self):
        """Create a new blank file - clears all tabs and starts fresh"""
        logging.debug("new_file()")
        # Confirm if there are unsaved changes
        if self.tabWidget.count() > 0:
            reply = QtWidgets.QMessageBox.question(
                self,
                "New File",
                "This will close all tabs and start a new file. Continue?",
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.No,
            )
            if reply == QtWidgets.QMessageBox.StandardButton.No:
                return

        # Clear all tabs
        while self.tabWidget.count() > 0:
            self.tabWidget.removeTab(0)

        # Reset file state
        self.openfile = ""
        self.setWindowTitle("IP-Visualizer")

        # Create a fresh tab
        self.new_tab()

    def new_tab(self):
        """Create a new subnet tab"""
        logging.debug("new_tab()")
        tab_count = self.tabWidget.count()
        subnet_view = SubnetView(self, f"Subnet {tab_count + 1}")
        # Use deepcopy to prevent shared field references
        subnet_view.fields = copy.deepcopy(self.defaultFields)
        subnet_view.add_user_fields_to_form()
        subnet_view.compile_field_patterns()  # Compile patterns for new tab
        self.tabWidget.addTab(subnet_view, f"Subnet {tab_count + 1}")
        self.tabWidget.setCurrentWidget(subnet_view)

    def close_tab(self, index):
        """Close a tab at the given index"""
        if self.tabWidget.count() > 1:
            self.tabWidget.removeTab(index)
        else:
            QtWidgets.QMessageBox.warning(
                self, "Cannot Close", "Cannot close the last tab!"
            )

    def get_current_view(self):
        """Get the currently active SubnetView"""
        return self.tabWidget.currentWidget()

    def load_save_data(self):
        """Loads file into saveData dictionary"""
        logging.debug("load_save_data()")
        file = QtWidgets.QFileDialog.getOpenFileName(self, "Choose file")
        if file[0]:
            with open(file[0], "r") as F1:
                saveData = yaml.load(F1, Loader=yaml.FullLoader)

                # Check if it's multi-tab format or legacy single view
                if "tabs" in saveData:
                    # Multi-tab format
                    # Clear existing tabs
                    while self.tabWidget.count() > 0:
                        self.tabWidget.removeTab(0)

                    # Load each tab
                    for tab_data in saveData["tabs"]:
                        subnet_view = SubnetView(self, tab_data.get("name", "Subnet"))
                        subnet_view.load_data(tab_data["fields"], tab_data["networks"])
                        tab_name = tab_data.get("name", "Subnet")
                        self.tabWidget.addTab(subnet_view, tab_name)
                else:
                    # Legacy single view format
                    current_view = self.get_current_view()
                    if current_view:
                        current_view.load_data(saveData["fields"], saveData["data"])

                self.openfile = file[0]
                self.setWindowTitle(f"IP-Visualizer {file[0]}")
        else:
            self.statusBar().showMessage("Failed to Load File")

    def write(self, name):
        """Save all tabs to file"""
        with open(name, "w") as F1:
            self.openfile = name
            tabs_data = []

            for i in range(self.tabWidget.count()):
                subnet_view = self.tabWidget.widget(i)
                tab_name = self.tabWidget.tabText(i)
                view_data = subnet_view.get_data()
                tabs_data.append(
                    {
                        "name": tab_name,
                        "fields": view_data["fields"],
                        "networks": view_data["networks"],
                    }
                )

            save_data = {"tabs": tabs_data}
            yaml.dump(save_data, F1)

    def saveAs(self):
        fileToSave = QtWidgets.QFileDialog.getSaveFileName(self, "WHERE?")
        if fileToSave[0]:
            self.write(fileToSave[0])
            self.openfile = fileToSave[0]
            self.setWindowTitle(f"IP-Visualizer {fileToSave[0]}")

    def save(self):
        if not self.openfile:
            self.saveAs()
        else:
            self.write(self.openfile)

    def settings(self):
        """Open settings dialog for field and color configuration"""
        current_view = self.get_current_view()
        if not current_view:
            QtWidgets.QMessageBox.warning(
                self, "No Active Tab", "Please create or select a tab first."
            )
            return

        dialog = FieldColorSettingsDialog(current_view, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # Recompile patterns after settings change
            current_view.compile_field_patterns()
            self.statusBar().showMessage("Settings updated")

    def print(self):
        current_view = self.get_current_view()
        if not current_view or not current_view.table.model():
            QtWidgets.QMessageBox.warning(
                self,
                "Nothing to Print",
                "Please generate a network visualization first.",
            )
            return

        # Setup printer for Letter size (8.5 x 11 inches)
        prn = QPrinter(QPrinter.PrinterMode.HighResolution)
        prn.setPageSize(QPrinter.PageSize.Letter)
        prn.setPageOrientation(QPrinter.PageOrientation.Landscape)

        printDialog = QPrintDialog(prn, self)
        if printDialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        painter = QPainter(prn)

        # Get page dimensions
        page_rect = prn.pageRect(QPrinter.Unit.DevicePixel)
        page_width = page_rect.width()
        page_height = page_rect.height()

        # Add margins (0.5 inch margins = ~50 pixels at 96 DPI, scaled to printer)
        margin = int(0.5 * prn.resolution())  # 0.5 inch margin
        printable_width = page_width - (2 * margin)
        printable_height = page_height - (2 * margin)

        # Get table widget
        table = current_view.table

        # Calculate table size needed
        table_width = table.horizontalHeader().length()
        table_height = table.verticalHeader().length()

        # Calculate header sizes
        header_height = table.horizontalHeader().height()
        header_width = table.verticalHeader().width()

        # Total size including headers
        total_width = table_width + header_width
        total_height = table_height + header_height

        # Calculate scaling to fit on page while maintaining aspect ratio
        scale_x = printable_width / total_width if total_width > 0 else 1
        scale_y = printable_height / total_height if total_height > 0 else 1
        scale = min(scale_x, scale_y, 1.0)  # Don't scale up, only down

        # Apply scaling and center on page
        painter.translate(margin, margin)
        painter.scale(scale, scale)

        # Render the table view
        table.render(painter)

        painter.end()

        self.statusBar().showMessage(f"Printed with {scale*100:.1f}% scaling")


app = QtWidgets.QApplication([])
window = MainWindow()
window.show()
app.exec()
