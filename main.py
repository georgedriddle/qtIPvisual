import yaml
import re
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


class MainWindow(QtWidgets.QMainWindow):
    matchcidr = QRegularExpression(
        r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}"
        r"([0-9]|[1-9][0-9]|1[0-9]{2}|"
        r"2[0-4][0-9]|25[0-5])(\/(3[0-2]|[1-2][0-9]|[0-9]))$"
    )
    cidrRegex = QRegularExpressionValidator(QRegularExpression(matchcidr))

    def __init__(self):
        super().__init__()
        widget = QtWidgets.QWidget()
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

        self.updateIcon = QIcon("icons/block--arrow.png")
        self.updateBtn = QtWidgets.QPushButton(self.updateIcon, "Update")
        self.updateBtn.clicked.connect(self.update_networks_data)

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
        netLayout.addWidget(self.updateBtn, 4, 0)

        net_section.setLayout(netLayout)

        layout.addWidget(net_section, 0, 0)
        layout.addWidget(self.label_cidr, 2, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.cidr, 3, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.deleteBtn, 3, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.plusBtn, 3, 2, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(fields_section, 4, 0, 1, 3)
        layout.addWidget(self.table, 4, 3)

        widget.setLayout(layout)

        self.defaultFields = {
            "Name": {
                "controlType": "lineEdit",
                "colorMap": {r"\w": "green"},
                "colorWeight": 1,
                "show": True,
            }
        }
        self.fields = {}
        self.networks = {}
        self.uFieldsCntrls = {}
        self.openfile = ""

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

    def check_field(self, cidr: dict):
        """Verifies that the field in the data section
        has a coresponding entry in the fields section.
        Adds it to fields as a lineEdit if not there."""
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
        """Run through all the subnet entries, call check_field() on each entry"""
        logging.debug("find_fields()")
        for cidr in self.networks.keys():
            self.check_field(cidr)

    def new(self):
        logging.debug("new()")
        self.fields = self.defaultFields
        self.add_user_fields_to_form()

    def load_save_data(self):
        """Loads file into saveData dictionary"""
        logging.debug("load_save_data()")
        self.clear_user_layout()
        file = QtWidgets.QFileDialog.getOpenFileName(self, "Choose file")
        if file[0]:
            with open(file[0], "r") as F1:
                saveData = yaml.load(F1, Loader=yaml.FullLoader)
                self.fields = saveData["fields"]
                self.networks = saveData["data"]
                self.openfile = file[0]
                self.setWindowTitle(f"IP-Visualizer {file[0]}")
            self.find_fields()
            self.add_user_fields_to_form()
        else:
            self.statusTip = "Failed to Load File"

    def update_networks_data(self):
        # TODO Pull key field out of user fields
        logging.debug("update_networks_data()")
        # TODO Next line can be improved I think.
        if self.cidr:
            net = self.cidr.text()
            logging.debug(f"update_networks_data: updating {net}")
            self.networks[net] = {}
            logging.debug("update_networks_data: iterating over form fileds")
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
        """Adds a new user defined field to the form"""
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

    def delete_record(self):
        logging.debug("delete_record()")
        key = self.cidr
        if self.networks.get(key):
            self.networks.pop(key)
        self.clearUfields()

    def write(self, name):
        with open(name, "w") as F1:
            self.openfile = name
            self.nets = {"data": self.networks}
            yaml.dump(self.nets, F1)
            self.flds = {"fields": self.fields}
            yaml.dump(self.flds, F1)

    def autoUpdate(self):
        logging.debug("autoUpdate()")
        if self.auto_update:
            self.update_networks_data()

    def saveAs(self):
        fileToSave = QtWidgets.QFileDialog.getSaveFileName(self, "WHERE?")
        if fileToSave[0]:
            self.write(fileToSave[0])
            self.openfile = fileToSave[0]
            self.windowTitle = "IP VISUAL --{fileToSave[0]}"

    def save(self):
        if not self.openfile:
            self.saveAs()
        else:
            self.write(self.openfile)

    def settings(self):
        print("Cool stuff comming soon")
        # Page 66 on Freda to create a dialog.

    def print(self):
        prn = QPrinter(QPrinter.PrinterMode.HighResolution)
        orig_size = self.size()
        self.resize(self.sizeHint())
        printDialog = QPrintDialog(prn, self)
        if printDialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            painter = QPainter(prn)
            self.render(painter)
            painter.end()
            self.table.resize(orig_size)

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
        # make data an object, then display the object itself.
        # how does this work when adding fields to objects?
        # iterate over object, add filed if missing?
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
        """Updates color and weight values if greater than current"""
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
        for row in self.data:
            for cell in row:
                cellNetwork = cell.get("network")
                networkdetails = self.networks.get(cellNetwork, {})
                for property, value in networkdetails.items():
                    if self.fields[property].get("show", False):
                        cell[property] = value
                    self.setCellColor(property, value, cell)

    def generate(self):
        logging.debug("generate()")
        start = int(self.displayStart.text())
        end = int(self.displayEnd.text())
        net = IPv4Network(self.displayNetwork.text(), strict=False)
        net = databuilder.checkCidr(net, start)
        columnCount = end - start + 1
        rowCount = 2 ** (end - net.prefixlen)
        self.data = databuilder.buildDisplayList(net, start, end)
        self.updateCell()
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
