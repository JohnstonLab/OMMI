#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import random
from PyQt4 import QtCore, QtGui

class MyWidget(QtGui.QWidget):
    def __init__(self):
        super(MyWidget, self).__init__()

        self.hello = ["Hallo Welt", "Hei maailma", "Hola Mundo", "Привет мир"]

        self.button = QtGui.QPushButton("Click me!")
        self.text = QtGui.QLabel("Hello World")
        self.text.setAlignment(QtCore.Qt.AlignCenter)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

        self.button.clicked.connect(self.magic)


    def magic(self):
        self.text.setText(random.choice(self.hello))

if __name__ == "__main__":
    app = QtGui.QApplication([])
    widget = MyWidget()
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec_())
