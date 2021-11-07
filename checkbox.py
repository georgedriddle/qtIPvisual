from PyQt6 import QtWidgets

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Learn a Checkbox")

        self.ck1 = QtWidgets.QCheckBox()
        self.ck1.setChecked(False)
        print(self.ck1.checkState())
        print(f'Bool is {bool(self.ck1.checkState())}')

app = QtWidgets.QApplication([])
window = MainWindow()
window.show()
app.exec()
