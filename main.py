from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import (QIntValidator, QRegularExpressionValidator, QColor,
                         QPalette)
from PyQt6.QtWidgets import (QApplication, QLineEdit, QMainWindow, QGridLayout,
                             QPushButton, QScrollBar, QVBoxLayout,  QWidget, QLabel,
                             QScrollArea, QHBoxLayout)

from ipaddress import ip_address as ipa

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
 
        
        toplayout = QVBoxLayout()
        headerlayout = QGridLayout()
        datalayout = QGridLayout()
        
        dataContainer = QWidget()

        zero32 = QIntValidator(0, 32)
        matchcidr = QRegularExpression(r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/(3[0-2]|[1-2][0-9]|[0-9]))$')
        V = QRegularExpressionValidator(QRegularExpression(matchcidr))
        
        sourceNetwork_lbl = QLabel()
        sourceNetwork_lbl.setText("Network")
        headerlayout.addWidget(sourceNetwork_lbl, 0, 0)
        
        start_lbl = QLabel("start")
        headerlayout.addWidget(start_lbl, 0, 1)
        
        sourceNetwork = QLineEdit()
        sourceNetwork.setMinimumSize(115,20)
        sourceNetwork.setValidator(V)
        
        sourceNetwork.editingFinished.connect(self.cidrOK)
        headerlayout.addWidget(sourceNetwork, 1, 0)

        start = QLineEdit()
        start.setMaxLength(2)
        start.setValidator(zero32)
        start.setMaximumSize(30, 20)
        start.editingFinished.connect(self.startOK)
        headerlayout.addWidget(start, 1, 1)
        
        end_lbl = QLabel("end")
        headerlayout.addWidget(end_lbl, 0, 2)

        end = QLineEdit()
        end.setMaxLength(2)
        end.setValidator(zero32)
        end.setMaximumSize(30,20)
        headerlayout.addWidget(end, 1, 2)
        toplayout.addLayout(headerlayout)

        generate = QPushButton("Generate")
        headerlayout.addWidget(generate, 1, 3)

        baseIP = ipa("192.168.0.0")
        
        for x in range(0,32):
            z = QLabel(f"{baseIP + x}/128")
            datalayout.addWidget(z)
        toplayout.addLayout(datalayout)
                       
        widget = QWidget()
        widget.setGeometry(0, 0, 800, 600)
        widget.setMaximumSize(800, 600)
        
        
        widget.setLayout(toplayout)
        scroller = QScrollArea()
        scroller.setWidget(widget)
        self.setCentralWidget(widget)

    def cidrOK(self):
        print("network input is good")
    
    def startOK(self):
        print("start is good!")
    
app = QApplication([])
window = MainWindow()
window.show()
app.exec()


