import json
from ipaddress import ip_network
from PyQt6 import QtCore, QtWidgets
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QTableView,
)
import databuilder


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def data(self, index, role):
        item = self._data[index.row()][index.column()]

        if role == Qt.ItemDataRole.DisplayRole:
            out = ''
            for key, value in item.items():
                if key not in ['spansize']:
                    if key == 'network':
                        out += f'{value}\n'
                    else:
                        out += f'{key}: {value}\n'
            return out

        if role == Qt.ItemDataRole.BackgroundRole:
            value = self._data[index.row()][index.column()]
            if item.get('color'):
                return QtGui.QColor(item.get('color'))

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])


class MainWindow(QtWidgets.QMainWindow):
    matchcidr = QRegularExpression(
            r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/(3[0-2]|[1-2][0-9]|[0-9]))$"
        )
    cidrvalid = QtGui.QRegularExpressionValidator(matchcidr)
    zero32 = QtGui.QIntValidator(0, 32)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IP-Visualizer")
        self.setGeometry(50, 50, 1000, 1200)

        self.loadIcon = QtGui.QIcon("icons/database--plus.png")
        self.loadAction = QtGui.QAction(self.loadIcon, "Load", self)
        self.loadAction.setStatusTip("Load Data!")
        self.loadAction.triggered.connect(self.loadSaveData)

        self.saveicon = QtGui.QIcon("icons/disk-return.png")
        self.saveAction = QtGui.QAction(self.saveicon, "Save", self)
        self.saveAction.setStatusTip("save data to file")
        self.saveAction.triggered.connect(self.save)

        self.printIcon = QtGui.QIcon("icons/printer.png")
        self.printAction = QtGui.QAction(self.printIcon, "Print", self)
        self.printAction.setStatusTip("Not Implemented")

        self.aboutIcon = QtGui.QIcon("icons/question-button.png")
        self.aboutAction = QtGui.QAction(self.aboutIcon, "About", self)
        self.aboutAction.setStatusTip("Not Implemented")

        self.toolbar = QtWidgets.QToolBar("Tool Bar")
        self.addToolBar(self.toolbar)
        self.toolbar.addAction(self.loadAction)
        self.toolbar.addAction(self.saveAction)
        self.toolbar.addAction(self.printAction)
        self.toolbar.addAction(self.aboutAction)

        self.setStatusBar(QtWidgets.QStatusBar(self))
#  Header Widget
        self.headerWidget = QWidget()
        self.labelNetwork = QLabel("Network to Visualize", self.headerWidget)
        self.displayNetwork = QLineEdit("192.168.1.0/24", self.headerWidget)
        self.displayNetwork.setMaximumWidth(110)
        self.displayNetwork.setMaxLength(18)
        self.displayNetwork.setValidator(self.cidrvalid)

        self.labelStart = QLabel("Start", self.headerWidget)

        self.displayStart = QLineEdit("24", self.headerWidget)
        self.displayStart.setMaxLength(2)
        self.displayStart.setMaximumWidth(25)
        self.displayStart.setValidator(self.zero32)
        self.labelEnd = QLabel("end", self.headerWidget)
        self.displayEnd = QLineEdit("26", self.headerWidget)
        self.displayEnd.setMaximumWidth(25)
        self.displayEnd.setMaxLength(2)
        self.displayEnd.setValidator(self.zero32)

        self.btnGenerate = QPushButton("Generate", self.headerWidget)
        self.btnGenerate.setMaximumWidth(100)
        self.btnGenerate.clicked.connect(self.generate)

        self.labelNetwork.move(0,5)
        self.labelStart.move(120, 5)
        self.labelEnd.move(150, 5)
        self.displayNetwork.move(0,20)
        self.displayStart.move(120, 20)
        self.displayEnd.move(150, 20)
        self.btnGenerate.move(10, 50)
        
        self.windowWidget = QWidget()
        self.windowWidgetLayout = QVBoxLayout()
        self.windowWidget.setLayout(self.windowWidgetLayout)
        
        self.setCentralWidget(self.windowWidget)

        self.table = QTableView()
        self.table.clicked.connect(self.showSelection)

        

        self.openfile = QLabel("NONE")
        self.setCentralWidget(self.windowWidget)
        self.setGeometry(600, 100, 400, 200)

        fields_section = QWidget()
        fields_section.setMaximumWidth(300)
        fieldlayout = QtWidgets.QFormLayout()
        fields_section.setLayout(fieldlayout)

        self.ufields = {'key': QLineEdit()}
        self.loadSaveData()
        deleteIcon = QtGui.QIcon("icons/cross.png")
        deleteBtn = QPushButton(deleteIcon,"Delete")
        deleteBtn.setMaximumWidth(65)
        deleteBtn.clicked.connect(self.delRecord)
        fieldlayout.addRow(deleteBtn)
        self.update_user_fields()
        for key, value in self.ufields.items():
            fieldlayout.addRow(key, value)
        UpdateIcon = QtGui.QIcon("icons/block--arrow.png")
        updateBtn = QPushButton(UpdateIcon, "Update")
        updateBtn.clicked.connect(self.updateFormFields)
        fieldlayout.addRow(updateBtn)

        self.coreWidget = QWidget()
        self.corelayout = QHBoxLayout()
        self.coreWidget.setLayout(self.corelayout)
        self.corelayout.addWidget(fields_section)

        self.windowWidgetLayout.addWidget(self.headerWidget)
        self.windowWidgetLayout.addWidget(self.coreWidget)
        #self.windowWidgetLayout.addWidget(self.table)

        self.saveData = {}

    def update_user_fields(self):
        for val in self.saveData['fields'].keys():
            if self.saveData['fields'][val]["controlType"] == "lineEdit":
                self.ufields[val] = QLineEdit()
            if self.saveData['fields'][val]['controlType'] == 'checkbox':
                self.ufields[val] = QCheckBox()

    def loadSaveData(self):
        ''' 1. Loads file into saveData dictionary'''
        file = QtWidgets.QFileDialog.getOpenFileName(self, "Choose file")
        if file[0]:
            with open(file[0], "r") as F1:
                self.saveData = json.load(F1)
            self.openfile.setText(file[0])
        else:
            self.statusTip = "Failed to Load File"

    def updateFormFields(self):
        key = self.ufields.get('key').text()  # Get key from field list
        if key:
            if self.saveData.get(key):  # Check in it exists in save data
                self.saveData.pop(key)  # Delete it if it does.
            self.saveData[key] = {}
            for ref, val in self.ufields.items():  # terrible var names..
                if ref == 'key':
                    ...
                elif self.saveData['fields'][ref]['controlType'] == 'lineEdit':
                    self.saveData[key][ref] = val.text()
                elif self.saveData['fields'][ref]['controlType'] == 'checkbox':
                    if val.checkState() == Qt.CheckState.Checked:
                        self.saveData[key][ref] = True

    def delRecord(self):
        key = self.ufields.get('key').text()
        if self.saveData.get(key):
                self.saveData.pop(key)
        self.clearUfileds()


    def save(self):
        fileToSave = QtWidgets.QFileDialog.getSaveFileName(self, "WHERE?")
        if fileToSave[0]:
            with open(fileToSave[0], "w") as F1:
                json.dump(self.saveData, F1, indent=4)

    def clearUfileds(self):
        for key in self.ufields.keys():
            if type(self.ufields.get(key)) == QLineEdit:
                self.ufields[key].setText('')

            elif type(self.saveData['fields'].get(key)) == QCheckBox:
                    self.ufields[key] == Qt.CheckState.Unchecked


    def showSelection(self):
        self.clearUfileds()
        z = self.table.selectedIndexes()[0]
        selectedDisplay = self.model.data(z, Qt.ItemDataRole.DisplayRole)
        selected_cidr = selectedDisplay.split()[0]
        self.ufields['key'].setText(selected_cidr)
        data = self.saveData.get(selected_cidr)
        if data:
            for name in data:
                if type(self.ufields.get(name)) == QLineEdit:
                    text = data.get(name)
                    self.ufields[name].setText(text)
                else:
                    self.ufields[name].setText('')
                if type(self.ufields.get(name)) == QCheckBox:
                    val = data.get(name)
                    if val == 'True':
                        self.ufields[name].setCheckState(Qt.CheckState.Checked)
                    else:
                        self.ufields[name].setCheckState(
                            Qt.CheckState.Unchecked)

    def merge(self, tableIn, records):
        cidrDetails = None
        for row in tableIn:
            for cell in row:
                fillcolor = ''
                fillweight = 0
                colorWeight = 0
                cidr = cell.get('network')
                if cidr:
                    cidrDetails = records.get(cidr)  # SaveData records.
                    if cidrDetails:
                        for property, value in cidrDetails.items():
                            if self.saveData['fields'][property]['show'] == 'True':
                                cell[property] = value
                                if self.saveData[cidr].get(property):
                                    fillcolor = self.saveData['fields'][property]['colorMap'].get(value)
                                    colorWeight = self.saveData['fields'][property].get("colorWeight")
                                    if colorWeight == None:
                                        colorWeight = 0
                                    if colorWeight > fillweight:
                                        fillweight = colorWeight
                                        cell['color'] = fillcolor

    def generate(self):
        start = int(self.displayStart.text())
        end = int(self.displayEnd.text())
        net = ip_network(self.displayNetwork.text(), strict=False)
        net = databuilder.checkCidr(net, start)
        columnCount = end - start + 1
        rowCount = 2 ** (end - net.prefixlen)
        self.data = databuilder.buildDisplayList(net, start, end)
        self.merge(self.data, self.saveData)
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
