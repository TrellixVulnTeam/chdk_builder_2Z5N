__author__ = 'Anthony'

import sys
from PyQt4 import QtCore, QtGui
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class Tree(QtGui.QWidget):
    """Widget abstracting the available ports available.
    root should point to a directory containing a CHDK root.
    selected is a dict, or a boolean indicating which versions should be built.
    Ex: selected = {'a2200': set(['100b', '100d'])},
    selected = True
    selected = False
    By default, selected follows camera_list.csv
    """

    def __init__(self, root=None, selected=None, parent=None):
        super(Tree, self).__init__(parent)
        self._setupUI()
        self.uncheckButton.clicked.connect(lambda: self.setSelected(False))
        self.defaultButton.clicked.connect(lambda: self.setSelected(None))
        self.checkButton.clicked.connect(lambda: self.setSelected(True))
        self.treeWidget.itemChanged.connect(self._updateChecks)
        if root is not None:
            self.setRoot(root)
            self.setSelected(selected)

    def _setupUI(self):
        self.uncheckButton = QtGui.QPushButton("Uncheck all")
        self.checkButton = QtGui.QPushButton("Check all")
        self.defaultButton = QtGui.QPushButton("Default")
        self.treeWidget = QtGui.QTreeWidget()
        self.treeWidget.setHeaderHidden(True)

        btnLayout = QtGui.QHBoxLayout()
        btnLayout.addWidget(self.uncheckButton)
        btnLayout.addWidget(self.checkButton)
        btnLayout.addWidget(self.defaultButton)

        layout = QtGui.QVBoxLayout()
        layout.addLayout(btnLayout)
        layout.addWidget(self.treeWidget)

        self.setLayout(layout)

    def _updateChecks(self, item, column):
        if column != 0:
            return

        state = item.checkState(0)
        n_children = item.childCount()
        if n_children != 0 and state != QtCore.Qt.PartiallyChecked:
            for i in range(n_children):
                item.child(i).setCheckState(0, state)

        parent = item.parent()
        if parent is None:
            return

        partial = False
        for i in range(parent.childCount()):
            if parent.child(i).checkState(0) != state:
                partial = True
                break

        if partial:
            parent.setCheckState(0, QtCore.Qt.PartiallyChecked)
        else:
            parent.setCheckState(0, state)

    def setRoot(self, path):
        logger.debug("Clearing tree widget")
        self.treeWidget.clear()
        logger.debug("Setting root to %s", path)
        self.root = QtCore.QDir(path)

        path = QtCore.QDir(path)
        path.setFilter(QtCore.QDir.Dirs | QtCore.QDir.NoDotAndDotDot)
        if not path.exists():
            logger.error("%s does not exists", path)
            raise Exception("Incorrect path provided")
        if not path.exists("camera_list.csv"):
            logger.error("No camera_list.csv in %s", path)
            raise Exception("Path does not seem to be a CHDK root")

        root = QtCore.QDir(path)
        if not path.cd("platform"):
            logger.error("Could not switch to 'platform'")
            raise Exception()

        for platform in path.entryList():
            if platform == "generic":
                continue
            # Check if corresponding folder in loader exists
            if not root.exists("loader/%s" % platform):
                logger.warning("Platform folder %s without corresponding loader folder", platform)
                continue

            logger.debug("Adding platform %s", platform)
            platform_item = self._addChild(platform)
            platform_dir = QtCore.QDir(path.absoluteFilePath(platform))
            platform_dir.setFilter(QtCore.QDir.Dirs | QtCore.QDir.NoDotAndDotDot)
            if not platform_dir.cd("sub"):
                logger.warning("No subplatform found for %s", platform)
                continue

            for subplatform in platform_dir.entryList():
                logger.debug("Adding subplatform %s for platform %s", subplatform, platform)
                self._addChild(subplatform, platform_item)

        # Add duplicate entries
        self._parseList()

    def _parseList(self):
        logger.debug("Parsing camera_list.csv for duplicate entries")
        if not hasattr(self, "root"):
            logger.error("_parseList called without setting tree root")
            return
        self.cameraSelected = defaultdict(set)
        with open(self.root.absoluteFilePath("camera_list.csv"), "r") as csvfile:
            # Skip header
            csvfile.next()
            for line in csvfile:
                if not line:
                    continue
                data = line.rstrip().split(',')
                if len(data) != 5:
                    logger.debug("Skipping malformatted line %s", line)
                    continue
                platform = data[0]
                subplatform = data[1]
                if not data[4]:
                    self.cameraSelected[platform].add(subplatform)
                if not data[3]:
                    continue
                dup_subplatforms = data[3].split(":")
                #if not data[4]:
                #    for dup_subplat in dup_subplatforms:
                #        self.cameraSelected[platform].add(dup_subplat)
                try:
                    item = self.treeWidget.findItems(platform, QtCore.Qt.MatchExactly)[0]
                except IndexError:
                    logger.warning("Could not find platform %s", platform)
                    continue
                for i in range(item.childCount()):
                    child = item.child(i)
                    if child.text(0) == subplatform:
                        for dup_subplatform in dup_subplatforms:
                            self._addChild(dup_subplatform, child, checkable=False)
                        break

    def _addChild(self, name, parent=None, checkable=True):
        logger.debug("Add child %s to parent %s in tree", name, parent)
        if parent is None:
            parent = self.treeWidget.invisibleRootItem()
        item = QtGui.QTreeWidgetItem(parent, [name])
        item.setExpanded(True)
        item.setCheckState(0, QtCore.Qt.Unchecked)
        if not checkable:
            item.setFlags(QtCore.Qt.ItemIsUserCheckable)
        return item

    def _setSelected(self, selected=None, all_or_none=None):
        if selected is None and all_or_none is None:
            logger.error("Invalid parameters for _setSelected")
            raise Exception("Invalid parameters for _setSelected")
        logger.debug("Set selected items for tree to %s", selected if selected is not None else all_or_none)
        if selected is not None:
            for platform, subplatforms in selected.iteritems():
                logger.debug("Select platform %s and subplatforms %s", platform, subplatforms)
                try:
                    item = self.treeWidget.findItems(platform, QtCore.Qt.MatchExactly)[0]
                except IndexError:
                    logger.warning("Could not find platform %s", platform)
                    continue
                # Shortcut if everything is checked
                n_children = item.childCount()
                if n_children == len(subplatforms):
                    item.setCheckState(0, QtCore.Qt.Checked)
                    continue
                for subplatform in subplatforms:
                    for i in range(n_children):
                        child = item.child(i)
                        if child.text(0) == subplatform:
                            child.setCheckState(0, QtCore.Qt.Checked)
        else:
            if all_or_none:
                state = QtCore.Qt.Checked
            else:
                state = QtCore.Qt.Unchecked
            item = self.treeWidget.invisibleRootItem()
            n_children = item.childCount()
            for i in range(n_children):
                item.child(i).setCheckState(0, state)

    def setSelected(self, selected=None):
        if selected is None:
            if not hasattr(self, "cameraSelected"):
                return
            logger.debug("No preset for tree, defaulting to camera_list.csv")
            self._setSelected(self.cameraSelected)
        elif isinstance(selected, bool):
            self._setSelected(all_or_none=selected)
        else:
            self._setSelected(selected)


if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    window = Tree("C:/Users/Anthony/Downloads/chdk/trunk/chdk_trunk")
    window.show()
    sys.exit(app.exec_())