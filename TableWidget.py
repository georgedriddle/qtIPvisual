import sys
from PyQt6 import QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        def change():
            table.clear()
            table.setItem(0, 0, QtWidgets.QTableWidgetItem("192.168.1.0/24"))
            d = QtWidgets.QTableWidgetItem("192.168.1.128/26")
            table.setItem(2, 2, d)
            print(data)

        self.setWindowTitle("IP-Visualizer")
        self.setGeometry(100, 100, 400, 400)
        widget = QtWidgets.QWidget()
        table = QtWidgets.QTableWidget(4, 3)
        table.setCornerButtonEnabled(True)
        table.setHorizontalHeaderLabels(["/24", "/25", "/26"])
        table.setShowGrid(True)
        table.setSpan(0, 0, 4, 1)
        table.setSpan(0, 1, 2, 1)
        table.setSpan(2, 1, 2, 1)

        self.v = {'vrf': "GLOBAL"}
        data = [
            ["192.168.1.0/24", "192.168.1.0/25",
             "192.168.1.0/26"],
            ['', "", "192.168.1.64/26"],
            ["", "", ""],
            ["", "", "192.168.1.192/26"]
        ]

        update = QtWidgets.QPushButton("update")
        update.clicked.connect(change)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(table)
        layout.addWidget(update)

        widget.setLayout(layout)
        self.setCentralWidget(widget)


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
