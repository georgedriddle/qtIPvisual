import json
from ipaddress import ip_network
from PyQt6 import QtCore, QtWidgets
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import (
    QValidator,
    QIntValidator,
    QRegularExpressionValidator,
)
import databuilder
import settings


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            return str(self._data[index.row()][index.column()])

        if role == Qt.ItemDataRole.BackgroundRole:
            value = self._data[index.row()][index.column()]
            vrfcolormap = settings.metadata['Vrf']['colorMap']
            vrf = value.get('Vrf')
            if vrf in vrfcolormap.keys():
                return QtGui.QColor(vrfcolormap[vrf])

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.zero32 = QIntValidator(0, 32)
        matchcidr = QRegularExpression(
            r"^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/(3[0-2]|[1-2][0-9]|[0-9]))$"
        )
        cidrRegex = QRegularExpressionValidator(QRegularExpression(matchcidr))
        self.setWindowTitle("IP-Visualizer")
        self.setGeometry(100, 100, 400, 400)

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

        fields = QtWidgets.QWidget()
        fields.setMaximumWidth(300)
        self.records = []
        self.checkboxes = []
        fieldlayout = QtWidgets.QFormLayout()
        fields.setLayout(fieldlayout)
        filebtn = QtWidgets.QPushButton("Load")
        filebtn.clicked.connect(self.getFile)
        fieldlayout.addRow(filebtn)

        savebtn = QtWidgets.QPushButton("Save")
        savebtn.clicked.connect(self.save)
        fieldlayout.addRow(savebtn)
        dataFields = ['key']
        dataFields.extend(settings.detailFields)
        for field in dataFields:
            z = QtWidgets.QLineEdit()
            self.records.append(z)
        for box in settings.detailChecks:
            z = QtWidgets.QCheckBox()
            self.checkboxes.append(z)

        for number, control in enumerate(self.records):
            fieldlayout.addRow(dataFields[number], control)

        for number, control in enumerate(self.checkboxes):
            fieldlayout.addRow(settings.detailChecks[number], control)

        updateBtn = QtWidgets.QPushButton("Update!")
        updateBtn.clicked.connect(self.updateRecord)
        fieldlayout.addRow(updateBtn)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.labelNetwork, 0, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.displayNetwork, 1, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.labelStart, 0, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.displayStart, 1, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.labelEnd, 0, 2, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.displayEnd, 1, 2, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.btnGenerate, 2, 0)
        layout.addWidget(self.table, 3, 4)
        layout.addWidget(fields, 3, 0)
        widget.setLayout(layout)

    def selectFile(self):
        return QtWidgets.QFileDialog.getOpenFileName(self, "Choose file")

    def getFile(self):
        file = self.selectFile()
        if file[0]:
            with open(file[0], "r") as F1:
                self.saveData = json.load(F1)
        else:
            print("Failed to load File")
            # Todo: Make this message appear in status Bar.

    def updateRecord(self, key):
        for num, name in enumerate(settings.detailFields):
            print(num, name)

    def save(self):
        fileToSave = self.selectFile()
        if fileToSave[0]:
            with open(fileToSave[0], "w") as F1:
                json.dump(self.saveData, F1, indent=4)
        else:
            print("Save Failed, did not get a file from file dialog")
            # Todo: Make this message appear in status Bar.

    def showSelection(self):
        z = self.table.selectedIndexes()[0]
        lookup = self.model.data(z, Qt.ItemDataRole.DisplayRole)
        self.records[0].setText(lookup)
        for i, fld in enumerate(settings.detailFields):
            z = self.saveData.get(lookup)
            value = z.get(fld) if z else ""
            self.records[i + 1].setText(value)

        for i, fld in enumerate(settings.detailChecks):
            y = "False"
            z = self.saveData.get(lookup)
            if z:
                y = z.get(fld)
            value = Qt.CheckState.Checked if y == "True" else Qt.CheckState.Unchecked
            self.checkboxes[i].setCheckState(value)
    
    
    def merge(self, tableIn, records):
        z = None
        for row in tableIn:
            for column in row:
                y = column.get('network')
                if y:
                    z = records.get(column['network'])
                if z:
                    column.update(z)

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
