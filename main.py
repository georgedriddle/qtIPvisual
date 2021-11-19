import json
from ipaddress import ip_network
from PyQt6 import QtCore, QtWidgets
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import (
    QIntValidator,
    QRegularExpressionValidator,
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
                if key not in ['color', 'spansize']:
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
    def __init__(self):
        super().__init__()
        self.user_fields = {}
        self.zero32 = QIntValidator(0, 32)
        matchcidr = QRegularExpression(
            r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/(3[0-2]|[1-2][0-9]|[0-9]))$"
        )
        cidrRegex = QRegularExpressionValidator(QRegularExpression(matchcidr))
        self.setWindowTitle("IP-Visualizer")
        self.setGeometry(50, 50, 1000, 1200)

        menubar = QtWidgets.QMenuBar()
        menubar.setMaximumWidth(50)
        fileMenu = menubar.addMenu("File")
        fileMenu.addAction("New Dataset")
        fileMenu.addAction("Open a Dataset")
        fileMenu.addAction("Save a Dataset")
        fileMenu.addAction("Print")
        fileMenu.addAction("Exit")

        self.setStatusBar(QtWidgets.QStatusBar(self))
        self.saveData = {}
        self.filebtn = QtWidgets.QPushButton("Open File")
        self.filebtn.clicked.connect(self.getFile)
        widget = QtWidgets.QWidget()
        self.table = QtWidgets.QTableView()
        self.table.clicked.connect(self.showSelection)

        self.labelNetwork = QtWidgets.QLabel("Network to Visualze")
        self.displayNetwork = QtWidgets.QLineEdit("192.168.1.0/24")
        self.displayNetwork.setMaxLength(18)
        self.displayNetwork.setMaximumWidth(125)
        self.displayNetwork.setValidator(cidrRegex)

        self.labelStart = QtWidgets.QLabel("Start")
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

        self.setCentralWidget(widget)
        self.setGeometry(600, 100, 400, 200)

        fields_section = QtWidgets.QWidget()
        fields_section.setMaximumWidth(300)
        fieldlayout = QtWidgets.QFormLayout()
        fields_section.setLayout(fieldlayout)
        filebtn = QtWidgets.QPushButton("Load")
        filebtn.clicked.connect(self.getFile)
        fieldlayout.addRow(filebtn)

        savebtn = QtWidgets.QPushButton("Save")
        savebtn.clicked.connect(self.save)
        fieldlayout.addRow(savebtn)
        self.ufields = {'key': QtWidgets.QLineEdit()}
        self.getFile()
        self.update_user_fields()
        for key, value in self.ufields.items():
            fieldlayout.addRow(key, value)

        updateBtn = QtWidgets.QPushButton("Update!")
        updateBtn.clicked.connect(self.updateRecord)
        fieldlayout.addRow(updateBtn)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(menubar, 0, 0)
        layout.addWidget(self.labelNetwork, 1, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.displayNetwork, 2, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.labelStart, 1, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.displayStart, 2, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.labelEnd, 1, 2, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.displayEnd, 2, 2, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.btnGenerate, 3, 0)
        layout.addWidget(self.table, 4, 4)
        layout.addWidget(fields_section, 4, 0)
        widget.setLayout(layout)

    def update_user_fields(self):
        print(f"User_fields is {self.user_fields}")
        for val in self.user_fields.keys():
            if self.user_fields[val]["controlType"] == "lineEdit":
                self.ufields[val] = QtWidgets.QLineEdit()
            if self.user_fields[val]['controlType'] == 'checkbox':
                self.ufields[val] = QtWidgets.QCheckBox()

    def selectFile(self):
        return QtWidgets.QFileDialog.getOpenFileName(self, "Choose file")

    def getFile(self):
        file = self.selectFile()
        if file[0]:
            with open(file[0], "r") as F1:
                self.saveData = json.load(F1)
                self.user_fields = self.saveData['fields']
        else:
            print("Failed to load File")
            self.statusTip = "Failed to Load File!"

    def updateRecord(self):
        self.setStatusTip("Time to update SaveData!")
        key = self.ufields.get('key').text()  # Get key from field list
        if key:
            if self.saveData.get(key):  # Check in it exists in save data
                self.saveData.pop(key)  # Delete it if it does.
            self.saveData[key] = {}
            for ref, val in self.ufields.items():  # terrible var names..
                if ref == 'key':
                    ...
                elif self.user_fields[ref]['controlType'] == 'lineEdit':
                    self.saveData[key][ref] = val.text()
                elif self.user_fields[ref]['controlType'] == 'checkbox':
                    if val.checkState() == Qt.CheckState.Checked:
                        self.saveData[key][ref] = True

    def save(self):
        fileToSave = self.selectFile()
        if fileToSave[0]:
            with open(fileToSave[0], "w") as F1:
                json.dump(self.saveData, F1, indent=4)
        else:
            print("Save Failed, did not get a file from file dialog")
            # Todo: Make this message appear in status Bar.

    def clearUfileds(self):
        for key, control in self.ufields.items():
            if type(self.ufields.get(key)) == QtWidgets.QLineEdit:
                self.ufields[key].setText('')

    def showSelection(self):
        self.clearUfileds()
        z = self.table.selectedIndexes()[0]
        selectedDisplay = self.model.data(z, Qt.ItemDataRole.DisplayRole)
        selected_cidr = selectedDisplay.split()[0]
        self.ufields['key'].setText(selected_cidr)
        data = self.saveData.get(selected_cidr)
        if data:
            for name in data:
                if type(self.ufields.get(name)) == QtWidgets.QLineEdit:
                    text = self.saveData[selected_cidr].get(name)
                    self.ufields[name].setText(text)
                else:
                    self.ufields[name].setText('')
                if type(self.ufields.get(name)) == QtWidgets.QCheckBox:
                    val = self.saveData[selected_cidr].get(name)
                    if val == 'True':
                        self.ufields[name].setCheckState(Qt.CheckState.Checked)
                    else:
                        self.ufields[name].setCheckState(
                            Qt.CheckState.Unchecked)

    def merge(self, tableIn, records):
        z = None
        fillcolor = ''
        for row in tableIn:
            for cell in row:
                y = cell.get('network')
                if y:
                    z = records.get(y)
                    if z:
                        for key, value in z.items():
                            show = self.user_fields[key]['show']
                            if show == 'True':
                                cell.update({key: value})
                                if k:= self.user_fields.get(key):
                                    fillcolor = k['colorMap'].get(value)
                            if fillcolor:
                                cell.update({'color': fillcolor})

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
