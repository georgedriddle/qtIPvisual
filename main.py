from ipaddress import ip_network
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt
import databuilder

class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            return self._data[index.row()][index.column()].get('network')

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        return len(self._data[0])

    
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("IP-Visualizer")
        self.setGeometry(100, 100, 400, 400)

        widget = QtWidgets.QWidget()
        self.table = QtWidgets.QTableView()
        self.table.clicked.connect(self.showSelection)
        self.labelNetwork = QtWidgets.QLabel("Network to Visualze")
        self.displayNetwork = QtWidgets.QLineEdit("192.168.1.0/24")
        self.displayNetwork.setMaxLength(18)
        self.displayNetwork.setMaximumWidth(125)
        self.labelStart = QtWidgets.QLabel("Start")
        self.displayStart = QtWidgets.QLineEdit("24")
        self.displayStart.setMaxLength(2)
        self.displayStart.setMaximumWidth(25)
        self.labelEnd = QtWidgets.QLabel("end")
        self.displayEnd = QtWidgets.QLineEdit("26")
        self.displayEnd.setMaximumWidth(25)
        self.displayEnd.setMaxLength(2)

        self.btnGenerate = QtWidgets.QPushButton('Generate')
        self.btnGenerate.setMaximumWidth(100)
        self.btnGenerate.clicked.connect(self.generate)
        
        self.setCentralWidget(widget)
        self.setGeometry(600, 100, 400, 200)
        
        fields = QtWidgets.QWidget()
        fields.setMaximumWidth(400)
        self.detailSite = QtWidgets.QLineEdit()
        self.detailSite.setMaximumWidth(125)
        self.detailName = QtWidgets.QLineEdit()
        self.detailName.setMaximumWidth(400)
        self.detailVrf = QtWidgets.QLineEdit()
        self.detailVrf.setMaximumWidth(125)
        self.detailEnterpriseSummary = QtWidgets.QCheckBox()
        self.detailSiteSummary = QtWidgets.QCheckBox()

        fieldlayout = QtWidgets.QFormLayout()
        fieldlayout.addRow("Site", self.detailSite)
        fieldlayout.addRow("Name", self.detailName) 
        fieldlayout.addRow("VRF", self.detailVrf)
        fieldlayout.addRow("Ent. Summ", self.detailEnterpriseSummary)
        fieldlayout.addRow("Site Summ", self.detailSiteSummary) 
        fields.setLayout(fieldlayout)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.labelNetwork, 0, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.displayNetwork, 1, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.labelStart,0,1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.displayStart, 1, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.labelEnd, 0, 2, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.displayEnd, 1, 2, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.btnGenerate, 2, 0)
        layout.addWidget(self.table, 3, 4)
        layout.addWidget(fields,3,0)
        widget.setLayout(layout)


    def showSelection(self):
        
        z = self.table.selectedIndexes()[0]
        print(f'z is {type(z)}')
        print(f'row is {z.row()} and column is {z.column()}')
        print(self.model.data(z, Qt.ItemDataRole.DisplayRole))


    def generate(self):
        start = int(self.displayStart.text())
        end = int(self.displayEnd.text())
        net = ip_network(self.displayNetwork.text(),strict=False)
        net = databuilder.checkCidr(net, start)
        columnCount =  end - start + 1
        rowCount = 2 ** (end - net.prefixlen)
        self.data = databuilder.buildDisplayList(net, start, end)
        self.model = TableModel(self.data)
        self.table.setModel(self.model)
        for currentrow in range(0,rowCount):
            for currentcol in range(0,columnCount):
                if self.data[currentrow][currentcol].get('network'):
                    span = self.data[currentrow][currentcol].get('spansize')
                    if span > 1:
                        self.table.setSpan(currentrow, currentcol, span, 1)

app = QtWidgets.QApplication([])
window = MainWindow()
window.show()
app.exec()
