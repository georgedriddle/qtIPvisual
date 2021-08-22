from PyQt6.QtCore import Qt
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel,QScrollArea,
                             QSizePolicy, QVBoxLayout)
from PyQt6.QtGui import QPixmap

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Apop")
        photo = QLabel()
        photo.setPixmap(QPixmap("IMAG0147.jpg"))
        photo.setMinimumSize(800, 600)
        sa = QScrollArea()

        
        #sa.setFrameShape(6)
        #sa.setHorizontalScrollBarPolicy(2)
        sa.setWidgetResizable(True)
        sa.setWidget(photo)
        #sa.setBackgroundRole(QPalette.Dark())
        self.setCentralWidget(photo)
        sa_layout = QVBoxLayout()
        sa_layout.addWidget(photo)
        sa_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(sa_layout) 

app = QApplication([])
window = MainWindow()
window.show()
app.exec()