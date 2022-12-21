__author__ = 'Anthony'
from PyQt4 import QtCore, QtGui, QtNetwork
import logging
import io
import tarfile
import json
import sys
try:
    import lzma
except ImportError:
    from backports import lzma

logger = logging.getLogger(__name__)


def download(manager, url, identifier):
    QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
    request = QtNetwork.QNetworkRequest()
    request.setUrl(QtCore.QUrl(url))
    request.setAttribute(QtNetwork.QNetworkRequest.User, identifier)
    reply = manager.get(request)
    reply.finished.connect(lambda: QtGui.QApplication.restoreOverrideCursor())


class Build(QtGui.QWidget):
    """Widget handling toolchain and building
    Handles prompting user to download toolchain if it does not exists"""

    toolchain_url = 'https://raw.githubusercontent.com/adongy/chdk_builder/master/toolchain.json'

    def __init__(self, parent=None, path=None):
        super(Build, self).__init__(parent)

        self._setupUI()
        if path is None:
            path = QtCore.QCoreApplication.applicationDirPath()
        self.rootPath = QtCore.QDir(path)
        self.manager = QtNetwork.QNetworkAccessManager(self)
        self.manager.finished.connect(self.handleReply)
        self._checkToolchain()

    def _setupUI(self):
        self.toolchainCombo = QtGui.QComboBox()
        self.compileButton = QtGui.QPushButton("Build selected")

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.toolchainCombo)
        layout.addWidget(self.compileButton)
        self.setLayout(layout)

    def _checkToolchain(self):
        if not self.rootPath.exists('toolchain'):
            self.promptToolchainDownload()
        else:
            path = QtCore.QDir(self.rootPath)
            if not path.cd('toolchain/bin'):
                logger.error('Could not change to toolchain directory')
                raise Exception('Error when loading toolchains')
            toolchains = {}
            for file in path.entryList(['arm-*-gcc-[0-9]*']):
                ver = file.split('-')[-1]
                if ver.endsWith('.exe'):
                    ver = ver[:-4]
                if 'elf' in file:
                    logger.info('Found elf gcc toolchain %s version %s', file, ver)
                    toolchains['ELF'] = 'ELF ({})'.format(ver)
                elif 'eabi' in file:
                    logger.info('Found eabi gcc toolchain %s version %s', file, ver)
                    toolchains['EABI'] = 'EABI ({})'.format(ver)
                else:
                    logger.warning('Unknown gcc toolchain %s', file)
            for toolchain, name in toolchains.iteritems():
                self.toolchainCombo.addItem(name)

    def promptToolchainDownload(self):
        # Download manifest
        download(self.manager, self.toolchain_url, 'manifest')

    def handleReply(self, reply):
        response = reply.readAll()
        attr = reply.request().attribute(QtNetwork.QNetworkRequest.User)
        if attr == 'manifest':
            download_links = json.loads(str(response))
            if sys.platform not in download_links:
                logger.error('Platform %s not found in available toolchains %s', sys.platform, download_links)
                raise Exception('Count not find a toolchain for your OS')
            reply = QtGui.QMessageBox.question(self, "Download toolchain ?",
                                               'No toolchain found! Download it ?',
                                               QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.Yes:
                download(self.manager, download_links[sys.platform], 'toolchain')
        elif attr == 'toolchain':
            # uncompress
            with lzma.open(io.BytesIO(bytes(response))) as fileobj, tarfile.open(fileobj=fileobj) as tar:
                
                import os
                
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(tar, "{}/toolchain/".format(self.rootPath))
            QtGui.QMessageBox.information(self, "Download complete", "Finished downloading toolchain!")

        reply.deleteLater()
