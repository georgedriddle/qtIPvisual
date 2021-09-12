from ipaddress import ip_network
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QSize, QWaitCondition, Qt
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
        self.labelNetwork = QtWidgets.QLabel("Network to Visualze as CIDR")
        self.displayNetwork = QtWidgets.QLineEdit("192.168.1.0/24")
        self.displayNetwork.setMaxLength(18)
        size0 = QSize(10,10)
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
        self.btnGenerate.clicked.connect(self.generate)
        
        self.setCentralWidget(widget)
        self.setGeometry(600, 100, 400, 200)
    
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.labelNetwork)
        layout.addWidget(self.displayNetwork)
        layout.addWidget(self.labelStart)
        layout.addWidget(self.displayStart)
        layout.addWidget(self.labelEnd)
        layout.addWidget(self.displayEnd)
        layout.addWidget(self.btnGenerate)
        layout.addWidget(self.table)
        widget.setLayout(layout)
    
    def generate(self):
        net = ip_network(self.displayNetwork.text())
        start = int(self.displayStart.text())
        end = int(self.displayEnd.text())
        columnCount =  end - start + 1
        rowCount = 2 ** (end - net.prefixlen)
        self.data = databuilder.buildDisplayList(net, start, end)
        model = TableModel(self.data)
        self.table.setModel(model)
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
