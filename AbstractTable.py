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

        def fix():
            data[2][1] = "192.168.1.128/25"
            data[2][2] = "192.168.1.128/24"
            model.layoutChanged.emit()

        self.setWindowTitle("IP-Visualizer")
        self.setGeometry(100, 100, 400, 400)

        widget = QtWidgets.QWidget()

        visualNet = ip_network("143.0.0.0/14")
        start = 14
        end = 32
        data = databuilder.buildDisplayList(visualNet, start, end)
        table = QtWidgets.QTableView()

        columnCount =  end - start + 1
        rowCount = 2 ** (end - start)
        for currentrow in range(0,rowCount):
            for currentcol in range(0,columnCount):
                if data[currentrow][currentcol].get('network'):
                    span = data[currentrow][currentcol].get('spansize')
                    if span > 1:
                        table.setSpan(currentrow, currentcol, span, 1)
        model = TableModel(data)
        table.setModel(model)
        self.setCentralWidget(widget)
        self.setGeometry(600, 100, 400, 200)

        update = QtWidgets.QPushButton("update")
        update.clicked.connect(fix)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(table)
        layout.addWidget(update)
        widget.setLayout(layout)


app = QtWidgets.QApplication([])
window = MainWindow()
window.show()
app.exec()
