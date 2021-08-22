import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt
import ipaddress as ip


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            # See below for the nested-list data structure.
            # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data[0])


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        def change():
            data[2][2] = "192.168.1.128/26"
            print(data)

        self.setWindowTitle("IP-Visualizer")
        self.setGeometry(100,100,400,400)
        widget = QtWidgets.QWidget()
        
        table = QtWidgets.QTableView()
        table.setSpan(0, 0, 4, 1)
        table.setSpan(0, 1, 2, 1)
        table.setSpan(2, 1, 2, 1)
        
        self.v ={'vrf':"GLOBAL"}
        data = [
            ["192.168.1.0/24\n" + self.v['vrf'], "192.168.1.0/25","192.168.1.0/26"],
            ['', "","192.168.1.64/26"],
            ["","", ""],
            ["", "", "192.168.1.192/26"]
        ]
        
        update = QtWidgets.QPushButton("update")
        update.clicked.connect(change)
        
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(table)
        layout.addWidget(update)
        
        model = TableModel(data)
        table.setModel(model)
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        
        
        
        
        
app         = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
