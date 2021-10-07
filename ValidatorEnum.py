from PyQt6.QtGui import QIntValidator, QValidator

test = "2"
passed = QValidator.State.Acceptable
failed = QValidator.State.Invalid

v1 = QIntValidator(0, 32)
r = v1.validate(test, 0)
print(type(passed))