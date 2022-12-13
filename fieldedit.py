from PyQt6 import QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Field Editor")
        self.setGeometry(50, 50, 1000, 1200)

        layout = QtWidgets.QFormLayout()
        layout.addRow("Key", QtWidgets.QLineEdit())


def main():
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
