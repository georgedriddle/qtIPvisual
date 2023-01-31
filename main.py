import yaml
import re
import logging
from ipaddress import ip_network
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import (
    QAction,
    QIcon,
    QColor,
    QIntValidator,
    QRegularExpressionValidator,
    QPainter,
)
from gui.settings import Ui_frmSettings
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


class MainWindow(QtWidgets.QMainWindow):
    matchcidr = QRegularExpression(
        r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/(3[0-2]|[1-2][0-9]|[0-9]))$"
    )
    cidrRegex = QRegularExpressionValidator(QRegularExpression(matchcidr))

    def __init__(self):
        super().__init__()
        self.zero32 = QIntValidator(0, 32)
        self.setWindowTitle("IP-Visualizer")
        self.setGeometry(50, 50, 1000, 1200)

        toolbar = QtWidgets.QToolBar("Tool Bar Title")
        self.addToolBar(toolbar)

        self.autoSave = True
        self.auto_update = True

        newIcon = QIcon("icons/new-text.png")
        newAction = QAction(newIcon, "New", self)
        newAction.triggered.connect(self.new)

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
        printAction.setStatusTip("Not Implemented")
        printAction.triggered.connect(self.print)

        aboutIcon = QIcon("icons/question-button.png")
        aboutAction = QAction(aboutIcon, "About", self)
        aboutAction.setStatusTip("Not Implemented")

        settingsIcon = QIcon("icons/wheel.png")
        settingsAction = QAction(settingsIcon, "Settings", self)
        settingsAction.setStatusTip("Settings")
        settingsAction.triggered.connect(self.settings)

        toolbar.addAction(newAction)
        toolbar.addAction(loadAction)
        toolbar.addAction(saveAction)
        toolbar.addAction(saveAsAction)
        toolbar.addAction(printAction)
        toolbar.addAction(settingsAction)
        toolbar.addAction(aboutAction)

        printAction = QAction("Print It!", self)
        printAction.triggered.connect(print)

        menubar = QtWidgets.QMenuBar()
        menubar.setMaximumWidth(50)

        self.setStatusBar(QtWidgets.QStatusBar(self))

        self.filebtn = QtWidgets.QPushButton("Open File")
        self.filebtn.clicked.connect(self.load_save_data)
        widget = QtWidgets.QWidget()
        self.table = QtWidgets.QTableView()
        self.table.clicked.connect(self.show_selection)

        self.labelNetwork = QtWidgets.QLabel("Network to Visualze")
        self.labelNetwork.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.displayNetwork = QtWidgets.QLineEdit("192.168.1.0/24")
        self.displayNetwork.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.displayNetwork.setMaxLength(18)
        self.displayNetwork.setMaximumWidth(125)
        self.displayNetwork.setValidator(self.cidrRegex)

        self.labelStart = QtWidgets.QLabel("Start")
        self.labelStart.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.displayStart = QtWidgets.QLineEdit("24")
        self.displayStart.setMaxLength(2)
        self.displayStart.setMaximumWidth(25)
        self.displayStart.setValidator(self.zero32)

        self.labelEnd = QtWidgets.QLabel("end")
        self.displayEnd = QtWidgets.QLineEdit("26")
        self.displayEnd.setMaximumWidth(25)
        self.displayEnd.setMaxLength(2)
        self.displayEnd.setValidator(self.zero32)

        self.btnGenerate = QtWidgets.QPushButton("Generate")
        self.btnGenerate.setMaximumWidth(100)
        self.btnGenerate.clicked.connect(self.generate)

        self.openfile = QtWidgets.QLabel("NONE")
        self.setCentralWidget(widget)
        self.setGeometry(600, 100, 400, 200)

        self.deleteIcon = QIcon("icons/cross.png")
        self.deleteBtn = QtWidgets.QPushButton(self.deleteIcon, "Delete")
        self.deleteBtn.setMaximumWidth(65)
        self.deleteBtn.clicked.connect(self.delete_record)

        self.plusIcon = QIcon("icons/application-plus-black.png")
        self.plusBtn = QtWidgets.QPushButton(self.plusIcon, "Add Field")
        self.plusBtn.setMaximumWidth(75)
        self.plusBtn.clicked.connect(self.add_user_field)

        self.label_cidr = QtWidgets.QLabel("CIDR")
        self.cidr = QtWidgets.QLineEdit()

        fields_section = QtWidgets.QWidget(None)
        fields_section.setMaximumWidth(300)
        self.fieldlayout = QtWidgets.QFormLayout()
        fields_section.setLayout(self.fieldlayout)
        layout = QtWidgets.QGridLayout()
        net_section = QtWidgets.QWidget(None)
        netLayout = QtWidgets.QGridLayout()
        netLayout.addWidget(self.labelNetwork, 1, 0, Qt.AlignmentFlag.AlignLeft)
        netLayout.addWidget(self.displayNetwork, 2, 0, Qt.AlignmentFlag.AlignLeft)
        netLayout.addWidget(self.labelStart, 1, 1, Qt.AlignmentFlag.AlignLeft)
        netLayout.addWidget(self.displayStart, 2, 1, Qt.AlignmentFlag.AlignLeft)
        netLayout.addWidget(self.labelEnd, 1, 2, Qt.AlignmentFlag.AlignLeft)
        netLayout.addWidget(self.displayEnd, 2, 2, Qt.AlignmentFlag.AlignLeft)
        netLayout.addWidget(self.btnGenerate, 3, 0, 1, 1, Qt.AlignmentFlag.AlignLeft)
        net_section.setLayout(netLayout)

        layout.addWidget(net_section, 0, 0)
        layout.addWidget(self.label_cidr, 2, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.cidr, 3, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.deleteBtn, 3, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.plusBtn, 3, 2, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.openfile, 1, 4)
        layout.addWidget(fields_section, 4, 0, 1, 3)
        layout.addWidget(self.table, 4, 4)

        widget.setLayout(layout)

        self.defaultFields = {
            "Name": {
                "controlType": "lineEdit",
                "colorMap": {r"\w": "green"},
                "colorWeight": 1,
                "show": True,
            }
        }
        # Need to set up a Model for fields
        self.fields = {}
        self.networks = {}
        self.ufields = {}

    def add_user_fields_to_form(self):
        logging.info("add_user_fields_to_form()")
        self.update_user_fields()
        for key, value in self.ufields.items():
            self.fieldlayout.addRow(key, value)

        UpdateIcon = QIcon("icons/block--arrow.png")
        updateBtn = QtWidgets.QPushButton(UpdateIcon, "Update")
        updateBtn.clicked.connect(self.update_networks_data)
        self.fieldlayout.addRow(updateBtn)

    def update_user_fields(self):
        logging.info("update_user_fields()")
        for fieldname in self.fields.keys():
            if self.fields[fieldname]["controlType"] == "lineEdit":
                self.ufields[fieldname] = QtWidgets.QLineEdit()
                self.ufields[fieldname].editingFinished.connect(self.autoUpdate)
            if self.fields[fieldname]["controlType"] == "checkbox":
                self.ufields[fieldname] = QtWidgets.QCheckBox()

    def clear_user_layout(self):
        logging.info("clear_user_layout")
        rowCount = self.fieldlayout.rowCount()
        for x in range(rowCount - 1, -1, -1):
            self.fieldlayout.removeRow(x)

    def check_field(self, cidr: dict):
        """Verifies that the field in the data section
        has a coresponding entry in the fields section.
        Adds it to fields as a lineEdit if not there."""
        logging.info("check_field()")
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
        """Run through all the subnet entries and find any fields that are not in the fields section"""
        # TO DO: Cache found fields and skip check if already checked.
        logging.info("find_fields()")
        for cidr in self.networks.keys():
            self.check_field(cidr)

    def new(self):
        logging.info("new()")
        self.fields = self.defaultFields
        self.add_user_fields_to_form()

    def load_save_data(self):
        """1. Loads file into saveData dictionary"""
        logging.info("load_save_data()")
        self.clear_user_layout()
        file = QtWidgets.QFileDialog.getOpenFileName(self, "Choose file")
        if file[0]:
            with open(file[0], "r") as F1:
                saveData = yaml.load(F1, Loader=yaml.FullLoader)
                try:
                    self.fields = saveData["fields"]
                except:
                    logging.warning(
                        f"Did not find Field data in {file[0]} setting to default"
                    )
                    self.fields = self.defaultFields
                try:
                    self.networks = saveData["data"]
                except:
                    logging.warning(f"Did not find networks in {file[0]}")
                    self.networks = {}
            self.openfile.setText(file[0])
            self.find_fields()
            self.add_user_fields_to_form()
        else:
            self.statusTip = "Failed to Load File"

    def update_networks_data(self):
        # TODO Pull key field out of user fields
        logging.info("update_networks_data()")
        # TODO Next line can be improved I think.
        if self.cidr:
            net = self.cidr.text()
            logging.debug(f"update_networks_data: updating {net}")
            self.networks[net] = {}
            logging.debug(f"update_networks_data: iterating over form fileds")
            for fldname, val in self.ufields.items():
                newvalue = val.text()
                logging.debug(f"newvalue is {newvalue}")
                logging.info(f"update_networks_data: {fldname} is {newvalue}")
                if self.fields[fldname]["controlType"] == "lineEdit":
                    self.networks[net][fldname] = newvalue
                    logging.debug(f" networks is now: {self.networks}")
                elif self.fields[fldname]["controlType"] == "checkbox":
                    if val.checkState() == Qt.CheckState.Checked:
                        self.fields[net][fldname] = True

    def add_user_field(self):
        """Adds a new user defined field to the form"""
        logging.info("add_user_fields()")
        newName, ok = QtWidgets.QInputDialog.getText(self, "New field name", "Name")
        if newName and ok:
            fieldData = {
                "controlType": "lineEdit",
                "colorMap": {},
                "colorWeight": 1,
                "show": False,
            }
            self.fields[newName] = fieldData
            logging.info(f'self.fields is now {self.fields}')
            self.ufields[newName] = QtWidgets.QLineEdit()
            self.clear_user_layout()
            self.find_fields()
            self.add_user_fields_to_form()
            self.update_user_fields()
            self.generate()
            self.merge()
            logging.debug(f"fields[{newName}] is {self.fields[newName]}")

    def delete_record(self):
        logging.info("delete_record()")
        key = self.cidr
        if self.networks.get(key):
            self.networks.pop(key)
        self.clearUfields()

    def write(self, name):
        with open(name, "w") as F1:
            self.openfile.setText(name)
            self.nets = {"data": self.networks}
            yaml.dump(self.nets, F1)
            self.flds = {"fields": self.fields}
            yaml.dump(self.flds, F1)

    def autoUpdate(self):
        logging.info("autoUpdate()")
        if self.auto_update:
            self.update_networks_data()

    def saveAs(self):
        fileToSave = QtWidgets.QFileDialog.getSaveFileName(self, "WHERE?")
        if fileToSave[0]:
            self.write(fileToSave[0])
            self.openfile.setText(fileToSave[0])

    def save(self):
        if self.openfile.text() == "NONE":
            self.saveAs()
        else:
            self.write(self.openfile.text())

    def settings(self):
        print("Cool stuff comming soon")
        # Page 66 on Freda to create a dialog.

    def print(self):
        self.prn = QPrinter()
        self.prn.colorMode = QPrinter.ColorMode.Color
        self.prn.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        self.prn.setOutputFileName("test.pdf")

        painter = QPainter(self.prn)
        self.render(painter)

    def clearUfields(self):
        logging.info("clearufields()")
        for key in self.ufields.keys():
            if type(self.ufields.get(key)) == QtWidgets.QLineEdit:
                self.ufields[key].setText("")

            elif type(self.fields.get(key)) == QtWidgets.QCheckBox:
                self.ufields[key] == Qt.CheckState.Unchecked

    def show_selection(self):
        logging.info("show_selection()")
        self.clearUfields()
        z = self.table.selectedIndexes()[0]
        selectedDisplay = self.model.data(z, Qt.ItemDataRole.DisplayRole)
        selected_cidr = selectedDisplay.split()[0]
        self.cidr.setText(selected_cidr)
        logging.debug(f"selected_cidr is {selected_cidr}")
        data = self.networks.get(selected_cidr)
        logging.debug(f"show_selection: Populating user fields with {data}")
        logging.debug(f"Into these user fields {self.ufields.keys()}")
        if data:
            for name in data:
                if type(self.ufields.get(name)) == QtWidgets.QLineEdit:
                    text = data.get(name)
                    self.ufields[name].setText(text)
                else:
                    self.ufields[name].setText("")
                if type(self.ufields.get(name)) == QtWidgets.QCheckBox:
                    val = data.get(name)
                    if val == True:
                        self.ufields[name].setCheckState(Qt.CheckState.Checked)
                    else:
                        self.ufields[name].setCheckState(Qt.CheckState.Unchecked)

    def setFillcolor(
        self, fieldName: str, value_in: str, currentColor: str, currentWeight: int
    ) -> tuple:
        """Updates color and weight values if greater than current"""
        logging.info("setFillcolor()")
        logging.info(f"inbound color and weight is {currentColor} {currentWeight}")
        logging.info(f"Getting color for {fieldName}")
        color = ""
        weight = 0
        colormap = self.fields[fieldName]["colorMap"]
        for pattern in colormap.keys():
            if re.match(fr"{pattern}", value_in):
                logging.info(f"match on {pattern}")
                color = self.fields[fieldName]["colorMap"].get(pattern)
                logging.info(f"color is {color}")
                weight = self.fields[fieldName].get("colorWeight")
                logging.info(f"weight is {weight}")
            if color and (weight > currentWeight):
                logging.info(f"color and weight are now {color} {weight}")
                return (color, weight)
        else:
            logging.info(f"color and weight remain {currentColor} {weight}")
            return (currentColor, currentWeight)

    def merge(self):
        logging.info("merge()")
        cidrDetails = None
        logging.debug(f"merge in {self.networks}")
        for row in self.data:
            for cell in row:
                fillweight = 0
                if cidr := cell.get("network"):
                    logging.debug(f"MERGE:CIDR value to check is {cidr}")
                    if cidrDetails := self.networks.get(cidr):
                        logging.debug(f"MERGE: {cidr} is in networks")
                        logging.debug(f"MERGE: cidr details are {cidrDetails}")

                        for property, value in cidrDetails.items():
                            showValue = self.fields[property]["show"]
                            logging.debug(f"show value of {property} is {showValue} ")
                            logging.debug(f" showValue is type {type(showValue)}")
                            if showValue == True:
                                cell[property] = value
                                logging.debug(
                                    f"getting fillcolor for {property} {value}"
                                )
                                cell["color"], weight = self.setFillcolor(
                                    property, value, cell.get("color"), fillweight
                                )
                            else:
                                logging.debug("Not showing")
                    else:
                        logging.debug(f"MERGE: {cidr} is not in networks")

    def generate(self):
        logging.info("generate()")
        start = int(self.displayStart.text())
        end = int(self.displayEnd.text())
        net = ip_network(self.displayNetwork.text(), strict=False)
        net = databuilder.checkCidr(net, start)
        columnCount = end - start + 1
        rowCount = 2 ** (end - net.prefixlen)
        self.data = databuilder.buildDisplayList(net, start, end)
        self.merge()
        # Looking into here for potential issue with updates not working.
        self.model = TableModel(self.data)
        self.table.setModel(self.model)
        self.table.clearSpans()
        for currentrow in range(0, rowCount):
            for currentcol in range(0, columnCount):
                if self.data[currentrow][currentcol].get("network"):
                    span = self.data[currentrow][currentcol].get("spansize")
                    if span > 1:
                        self.table.setSpan(currentrow, currentcol, span, 1)
                    self.table


app = QtWidgets.QApplication([])
window = MainWindow()
window.show()
app.exec()
