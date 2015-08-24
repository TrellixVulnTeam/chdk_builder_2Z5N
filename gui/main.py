__author__ = 'Anthony'
import sys
from PyQt4 import QtCore, QtGui
from tree import Tree
from svn import SVN
from build import Build
import logging

logging.basicConfig()


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self._setupUI()
        self.svn.pathBox.currentIndexChanged[str].connect(self.tree.setRoot)

    def _setupUI(self):
        svnGroup = QtGui.QGroupBox("SVN Status")
        self.svn = SVN()
        svnLayout = QtGui.QHBoxLayout(svnGroup)
        svnLayout.addWidget(self.svn)

        buildGroup = QtGui.QGroupBox("Building")
        self.build = Build()
        buildLayout = QtGui.QHBoxLayout(buildGroup)
        buildLayout.addWidget(self.build)

        treeGroup = QtGui.QGroupBox("Available versions")
        self.tree = Tree()
        treeLayout = QtGui.QHBoxLayout(treeGroup)
        treeLayout.addWidget(self.tree)

        mainLayout = QtGui.QHBoxLayout()
        mainLayout.addWidget(treeGroup)
        mainLayout.addWidget(buildGroup)
        mainLayout.addWidget(svnGroup)

        centralWidget = QtGui.QWidget()
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)


def main():
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()