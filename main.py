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
            if item.get("color"):
                clr = item.get("color")
                logging.debug(f"color = {clr}")
                return QColor(clr)

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])


class settingsWindow(QtWidgets.QWidget, Ui_frmSettings):
    super(Ui_frmSettings).__init__


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
        loadAction.triggered.connect(self.loadSaveData)

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
        self.filebtn.clicked.connect(self.loadSaveData)
        widget = QtWidgets.QWidget()
        self.table = QtWidgets.QTableView()
        self.table.clicked.connect(self.showSelection)

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

        fields_section = QtWidgets.QWidget(None)
        fields_section.setMaximumWidth(300)
        self.fieldlayout = QtWidgets.QFormLayout()
        fields_section.setLayout(self.fieldlayout)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.labelNetwork, 1, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.displayNetwork, 2, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.labelStart, 1, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.displayStart, 2, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.labelEnd, 1, 2, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.displayEnd, 2, 2, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.btnGenerate, 3, 0, 1, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.openfile, 3, 4)
        layout.addWidget(self.table, 4, 4)
        layout.addWidget(fields_section, 4, 0, 1, 3)
        widget.setLayout(layout)

        self.defaultFields = {
            "Name": {
                "controlType": "lineEdit",
                "colorMap": {".*": "green"},
                "colorWeight": 1,
                "show": "True",
            }
        }
        self.fields = {}
        self.networks = {}

    def add_user_fields_to_form(self):
        self.deleteIcon = QIcon("icons/cross.png")
        self.deleteBtn = QtWidgets.QPushButton(self.deleteIcon, "Delete")
        self.deleteBtn.setMaximumWidth(65)
        self.deleteBtn.clicked.connect(self.delRecord)
        self.plusIcon = QIcon("icons/application-plus-black.png")
        self.plusBtn = QtWidgets.QPushButton(self.plusIcon, "Add Field")
        self.plusBtn.setMaximumWidth(75)
        self.plusBtn.clicked.connect(self.addRecord)
        self.newField = QtWidgets.QLineEdit()

        self.fieldlayout.addRow(self.deleteBtn)
        self.fieldlayout.addRow(self.plusBtn)
        self.fieldlayout.addRow(self.newField)
        self.ufields = {"key": QtWidgets.QLineEdit()}

        self.update_user_fields()
        for key, value in self.ufields.items():
            self.fieldlayout.addRow(key, value)

        UpdateIcon = QIcon("icons/block--arrow.png")
        updateBtn = QtWidgets.QPushButton(UpdateIcon, "Update")
        updateBtn.clicked.connect(self.updateNetworksData)
        self.fieldlayout.addRow(updateBtn)

    def update_user_fields(self):
        for fieldname in self.fields.keys():
            if self.fields[fieldname]["controlType"] == "lineEdit":
                self.ufields[fieldname] = QtWidgets.QLineEdit()
                self.ufields[fieldname].editingFinished.connect(self.autoUpdate)
            if self.fields[fieldname]["controlType"] == "checkbox":
                self.ufields[fieldname] = QtWidgets.QCheckBox()

    def clear_user_layout(self):
        rowCount = self.fieldlayout.rowCount()
        for x in range(rowCount - 1, -1, -1):
            self.fieldlayout.removeRow(x)

    def checkField(self, cidr: dict):
        for fieldname in self.networks.get(cidr).keys():
            if fieldname not in self.fields.keys():
                entry = {
                    fieldname: {
                        "controlType": "lineEdit",
                        "colorMap": {},
                        "show": "False",
                    }
                }
                self.fields.update(entry)

    def findFields(self):
        """Run through all the subnet entries and find any fields that are not in the fields section"""
        for cidr in self.networks.keys():
            self.checkField(cidr)

    def new(self):
        self.fields = self.defaultFields
        self.add_user_fields_to_form()

    def loadSaveData(self):
        """1. Loads file into saveData dictionary"""
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
            self.findFields()
            self.add_user_fields_to_form()
        else:
            self.statusTip = "Failed to Load File"

    def load(self):
        """Loads fields and data sections from yaml file"""
        file = QtWidgets.QFileDialog.getOpenFileName(self, "Choose a File")
        if file[0]:
            with open(file[0], "r") as F1:
                data = yaml.load(F1)
                self.fields = data["fields"]
                self.networks = data["data"]

    def updateNetworksData(self):
        # TODO Pull key field out of user fields
        if cidr := self.ufields.get("key").text():
            logging.info(f"updateNetworksData: updating {cidr}")
            self.networks[cidr] = {}
            logging.info(f"updateNetworksData: iterating over form fileds")
            for fldname, val in self.ufields.items():
                if fldname == "key":
                    continue
                newvalue = val.text()
                logging.info(f"updateNetworksData: {fldname} is {newvalue}")
                if self.fields[fldname]["controlType"] == "lineEdit":
                    self.networks[cidr][fldname] = newvalue
                    logging.info(f" networks is now: {self.networks}")
                elif self.fields[fldname]["controlType"] == "checkbox":
                    if val.checkState() == Qt.CheckState.Checked:
                        self.fields[cidr][fldname] = True

    def addRecord(self):
        """Adds a new user defined field to the form"""
        if self.newField.text():
            fieldData = {
                "controlType": "lineEdit",
                "colorMap": {},
                "colorWeight": 1,
                "show": "False",
            }
            self.fields[self.newField.text()] = fieldData
            self.ufields[self.newField.text()] = QtWidgets.QLineEdit()
            self.clear_user_layout()
            self.findFields()
            self.add_user_fields_to_form()
            self.update_user_fields()
            self.updateNetworksData()
            logging.debug(f"{self.newField.text()} is {fieldData}")
            self.update_user_fields()

    def delRecord(self):
        key = self.ufields.get("key").text()
        if self.networks.get(key):
            self.networks.pop(key)
        self.clearUfileds()

    def write(self, name):
        with open(name, "w") as F1:
            self.openfile.setText(name)
            self.nets = {"data": self.networks}
            yaml.dump(self.nets, F1)
            self.flds = {"fields": self.fields}
            yaml.dump(self.flds, F1)

    def autoUpdate(self):
        if self.auto_update:
            self.updateNetworksData()

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

    def clearUfileds(self):
        for key in self.ufields.keys():
            if type(self.ufields.get(key)) == QtWidgets.QLineEdit:
                self.ufields[key].setText("")

            elif type(self.fields.get(key)) == QtWidgets.QCheckBox:
                self.ufields[key] == Qt.CheckState.Unchecked

    def showSelection(self):
        self.clearUfileds()
        z = self.table.selectedIndexes()[0]
        selectedDisplay = self.model.data(z, Qt.ItemDataRole.DisplayRole)
        selected_cidr = selectedDisplay.split()[0]
        self.ufields["key"].setText(selected_cidr)
        data = self.networks.get(selected_cidr)
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
        self, property_in: str, value_in: str, currentColor: str, currentWeight: int
    ) -> tuple:
        """Updates color and weight values if greater than current"""
        logging.debug(f"inbound color and weight is {currentColor} {currentWeight}")
        logging.debug(f"Getting color for {property_in}")

        color = ""
        weight = 0
        colormap = self.fields[property_in]["colorMap"]
        for item in colormap.keys():
            if re.match(fr"{item}", value_in):
                color = self.fields[property_in]["colorMap"].get(item)
                weight = self.fields[property_in].get("colorWeight")
            if color and (weight > currentWeight):
                logging.debug(f"color and weight are now {color} {weight}")
                return (color, weight)
        else:
            logging.debug(f"color and weight remain {currentColor} {weight}")
            return (currentColor, currentWeight)

    def merge(self):
        cidrDetails = None
        for row in self.data:
            for cell in row:
                fillweight = 0
                if cidr := cell.get("network"):
                    if cidrDetails := self.networks.get(cidr):
                        logging.info(f"MERGE: {cidr} is in networks")
                        for property, value in cidrDetails.items():
                            if self.fields[property]["show"] == True:
                                cell[property] = value
                                logging.debug(
                                    f"getting fillcolor for {property} {value}"
                                )
                                cell["color"], fillweight = self.setFillcolor(
                                    property, value, cell.get("color"), fillweight
                                )
                    else:
                        logging.info(f"MERGE: {cidr} is not in networks")

    def generate(self):
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
