__author__ = 'Anthony'
import sys
from PyQt4 import QtCore, QtGui
import pysvn
import logging

logger = logging.getLogger(__name__)


class SVN(QtGui.QWidget):
    """Widget holding the filesystem data. It downloads
    the CHDK source code, allowing the user to choose the
    revision, branch, or provide his own source tree"""

    chdk_base_url = "http://subversion.assembla.com/svn/chdk/"

    def __init__(self, parent=None):
        super(SVN, self).__init__(parent)

        self._setupUI()
        self.errorMessageDialog = QtGui.QErrorMessage(self)
        self.browseButton.clicked.connect(self.browse)
        self.pathBox.currentIndexChanged[str].connect(self._pathChanged)
        self.client = pysvn.Client()
        self._updateData()

    def _setupUI(self):
        self.revisionLabel = QtGui.QLabel("Current local revision :")

        self.pathLabel = QtGui.QLabel("Current path")
        self.pathBox = QtGui.QComboBox()
        self.pathBox.setEditable(True)
        self.pathLabel.setBuddy(self.pathBox)
        self.browseButton = QtGui.QPushButton("Browse")

        self.branchCombo = QtGui.QComboBox()

        self.updateButton = QtGui.QPushButton("Update")
        self.updateButton.setToolTip("Update to latest revision in current branch.<br/>"
                                     "Will reset <b>all</b> changes!")

        svnLayout = QtGui.QVBoxLayout()
        svnLayout.addWidget(self.revisionLabel)
        svnLayout.addWidget(self.pathLabel)
        svnLayout.addWidget(self.pathBox)
        svnLayout.addWidget(self.browseButton)
        svnLayout.addWidget(self.branchCombo)
        svnLayout.addWidget(self.updateButton)

        self.setLayout(svnLayout)

    def _pathChanged(self, index):
        print index

    def _checkDir(self, directory):
        path = QtCore.QDir(directory)
        if not path.exists():
            return False

        if not path.exists("camera_list.csv"):
            return False
        return True

    def browse(self):
        directory = QtGui.QFileDialog.getExistingDirectory(self, "Select CHDK root",
                                                           QtCore.QDir.currentPath())

        if directory:
            if self._checkDir(directory):
                if self.pathBox.findText(directory) == -1:
                    self.pathBox.addItem(directory)

                self.pathBox.setCurrentIndex(self.pathBox.findText(directory))
            else:
                self.errorMessageDialog.showMessage("You have selected a directory that does not seem"
                    " to be a CHDK root folder.")


    def _updateData(self):
        logger.debug("Updating branches data")
        # Get branches
        branches = self.client.list(self.chdk_base_url + "branches",
                                    recurse=False,
                                    dirent_fields=pysvn.SVN_DIRENT_CREATED_REV)
        trunk, _ = self.client.list(self.chdk_base_url + "trunk",
                                    recurse=False,
                                    dirent_fields=pysvn.SVN_DIRENT_CREATED_REV)[0]
        logger.debug("Trunk is at revision %s", trunk.created_rev.number)
        self.branchCombo.addItem('trunk (r{})'.format(trunk.created_rev.number), trunk)

        # Remove root
        for branch, _ in branches[1:]:
            branch_name = branch.repos_path.split("/")[-1]
            revision = branch.created_rev.number
            logger.debug("Branch %s is at revision %s", branch_name, revision)
            self.branchCombo.addItem('{} (r{})'.format(branch_name, revision), branch)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = SVN()
    window.show()
    sys.exit(app.exec_())