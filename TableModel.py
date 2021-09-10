import sys
from PyQt6 import QtWidgets
from PyQt6.QtGui import QStandardItemModel, QStandardItem


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        def change():
            model.setItem(0, 0, QStandardItem("192.168.1.0/24"))
            d = QStandardItem("192.168.1.128/26")
            model.setItem(2, 2, d)

        self.setWindowTitle("IP-Visualizer")
        self.setGeometry(100, 100, 400, 400)
        widget = QtWidgets.QWidget()
        data = [
                [QStandardItem("192.168.1.0/24"),
                 QStandardItem("192.168.1.0/25"),
                 QStandardItem("192.168.1.0/26")
                ],
                [QStandardItem(''),
                 QStandardItem(""),
                 QStandardItem("192.168.1.64/26")
                ],
                [QStandardItem(""),
                 QStandardItem(""),
                 QStandardItem("")
                ],
                [QStandardItem(""),
                 QStandardItem(""),
                 QStandardItem("192.168.1.192/26")
                ]
               ]
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["/24", "/25", "/26"])

        view = QtWidgets.QTableView()
        view.setModel(model)
        view.setSpan(0, 0, 4, 1)
        view.setSpan(0, 1, 2, 1)
        view.setSpan(2, 1, 2, 1)

        self.v = {'vrf': "GLOBAL"}

        update = QtWidgets.QPushButton("update")
        update.clicked.connect(change)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(view)
        layout.addWidget(update)

        widget.setLayout(layout)
        self.setCentralWidget(widget)


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
