# -*- coding: utf-8 -*-
"""
Created on Thu Sep 26 15:57:20 2019

@author: Louis Vande Perre


Source for the QTree part : https://stackoverflow.com/questions/14385409/pyqt-and-qtreeview-how-get-the-path-from-the-selected-file
"""

from PyQt5 import QtCore, QtWidgets

class BrowseWindow(QtWidgets.QWidget):
    """
    
    """
    
    filePathSig = QtCore.pyqtSignal(str)
    fileNameSig = QtCore.pyqtSignal(str)
    
    def __init__(self, isoiWindow=None, parent=None):
        super(BrowseWindow, self).__init__(parent)

        self.pathRoot = QtCore.QDir.rootPath()

        self.model = QtWidgets.QFileSystemModel(self)
        self.model.setRootPath(self.pathRoot)

        self.indexRoot = self.model.index(self.model.rootPath())

        self.treeView = QtWidgets.QTreeView(self)
        self.treeView.setModel(self.model)
        self.treeView.setRootIndex(self.indexRoot)
        self.treeView.clicked.connect(self.on_treeView_clicked)

        self.labelFileName = QtWidgets.QLabel(self)
        self.labelFileName.setText("File Name:")

        self.lineEditFileName = QtWidgets.QLineEdit(self)

        self.labelFilePath = QtWidgets.QLabel(self)
        self.labelFilePath.setText("File Path:")

        self.lineEditFilePath = QtWidgets.QLineEdit(self)

        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.addWidget(self.labelFileName, 0, 0)
        self.gridLayout.addWidget(self.lineEditFileName, 0, 1)
        self.gridLayout.addWidget(self.labelFilePath, 1, 0)
        self.gridLayout.addWidget(self.lineEditFilePath, 1, 1)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addLayout(self.gridLayout)
        self.layout.addWidget(self.treeView)
        
        if isoiWindow != None :
            print 'signal connection'
            self.isoiWindow = isoiWindow
            self.isoiWindow.settingsLoaded.connect(self.close)

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def on_treeView_clicked(self, index):
        indexItem = self.model.index(index.row(), 0, index.parent())

        fileName = self.model.fileName(indexItem)
        filePath = self.model.filePath(indexItem)
        
        #Sending information to the main GUI window
        self.fileNameSig.emit(fileName)
        self.filePathSig.emit(filePath)

        self.lineEditFileName.setText(fileName)
        self.lineEditFilePath.setText(filePath)

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName('MyWindow')

    main = BrowseWindow()
    main.resize(666, 333)
    main.move(app.desktop().screen().rect().center() - main.rect().center())
    main.show()

    sys.exit(app.exec_())