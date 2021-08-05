from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import (QIntValidator, QRegularExpressionValidator, QColor,
                         QPalette)
from PyQt6.QtWidgets import (QApplication, QLineEdit, QMainWindow, QGridLayout,
                             QPushButton,  QWidget, QLabel)


class Color(QWidget):
    def __init__(self, color):
        super().__init__()
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IP VISUAL")
        layout = QGridLayout()
        layout.setVerticalSpacing(1)
        layout.setRowMinimumHeight(0, 1)

        zero32 = QIntValidator(0, 32)
        matchcidr = QRegularExpression(r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/(3[0-2]|[1-2][0-9]|[0-9]))$')
        V = QRegularExpressionValidator(QRegularExpression(matchcidr))
        
        sourceNetwork_lbl = QLabel()
        sourceNetwork_lbl.setText("Network")
        layout.addWidget(sourceNetwork_lbl, 0, 0)
        
        start_lbl = QLabel("start")
        layout.addWidget(start_lbl, 0, 1)
        
        sourceNetwork = QLineEdit()
        sourceNetwork.setMinimumSize(115,20)
        sourceNetwork.setValidator(V)
        
        sourceNetwork.editingFinished.connect(self.cidrOK)
        layout.addWidget(sourceNetwork, 1, 0)

        start = QLineEdit()
        start.setMaxLength(2)
        start.setValidator(zero32)
        start.setMaximumSize(30, 20)
        start.editingFinished.connect(self.startOK)
        layout.addWidget(start, 1, 1)
        
        end_lbl = QLabel("end")
        layout.addWidget(end_lbl, 0, 2)

        end = QLineEdit()
        end.setMaxLength(2)
        end.setValidator(zero32)
        end.setMaximumSize(30,20)
        layout.addWidget(end, 1, 2)

        generate = QPushButton("Generate")
        layout.addWidget(generate, 1, 3)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def cidrOK(self):
        print("network input is good")
    
    def startOK(self):
        print("start is good!")
    
app = QApplication([])
window = MainWindow()
window.show()
app.exec()


