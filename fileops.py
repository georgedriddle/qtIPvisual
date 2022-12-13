import json
from PyQt6.QtWidgets import QFileDialog


def load():
    """Returns first file from a QFiledialog"""
    file = QFileDialog.getOpenFileName()
    if file[0]:
        with open(file[0], "r") as F1:
            data = json.load(F1)
            return data


def main():
    print(load())


if __name__ == "__main__":
    main()
