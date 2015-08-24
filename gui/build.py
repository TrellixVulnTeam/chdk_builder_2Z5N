__author__ = 'Anthony'
from PyQt4 import QtCore, QtGui, QtNetwork
import logging
import io
import tarfile
import json

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

    toolchain_url = '.json'

    def __init__(self, parent=None, path=''):
        super(Build, self).__init__(parent)

        self._setupUI()
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
        if not self.rootPath.exists('bin'):
            self.promptToolchainDownload()
        else:
            path = QtCore.QDir(self.rootPath)
            path.cd('bin')
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
        response = unicode(reply.readAll())
        attr = reply.request().attribute(QtNetwork.QNetworkRequest.User)
        if attr == 'manifest':
            download_links = json.loads(response)
            avail_toolchains = [tc for tc in download_links.keys() if tc != 'default']
            default = avail_toolchains.index(download_links['default']) if 'default' in download_links else 0
            select_toolchain, ok = QtGui.QInputDialog.getItem(self, 'Select toolchain to download',
                                                              'Toolchain', avail_toolchains, default, False)
            if ok and select_toolchain:
                download(self.manager, download_links[select_toolchain], 'toolchain')
        elif attr == 'toolchain':
            # uncompress
            with io.BytesIO(response) as fileobj, tarfile.open(fileobj=fileobj, mode='r:gz') as tar:
                tar.extractall('{}/toolchain/'.format(QtCore.QCoreApplication.applicationDirPath()))
            QtGui.QMessageBox.information(self, "Download complete", "Finished downloading toolchain!")

        reply.deleteLater()
