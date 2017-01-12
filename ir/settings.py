import codecs
import json
import os

from PyQt4.QtCore import SIGNAL, SLOT
from PyQt4.QtGui import (QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout,
                         QLabel, QLineEdit, QVBoxLayout)
from aqt import mw

import ir.util


class SettingsManager():
    def __init__(self):
        self.loadSettings()

    def loadSettings(self):
        self.mediaDir = os.path.join(mw.pm.profileFolder(), 'collection.media')
        self.jsonPath = os.path.join(self.mediaDir, '_ir.json')

        if os.path.isfile(self.jsonPath):
            with codecs.open(self.jsonPath, encoding='utf-8') as jsonFile:
                self.settings = json.load(jsonFile)
        else:
            self.settings = {'doHighlightFont': 'false',
                             'highlightColor': 'yellow',
                             'lastDialogQuickKey': {},
                             'quickKeys': {},
                             'schedLaterInt': 50,
                             'schedLaterRandom': True,
                             'schedLaterType': 'pct',
                             'schedSoonInt': 10,
                             'schedSoonRandom': True,
                             'schedSoonType': 'pct',
                             'scroll': {},
                             'textSizeMultiplier': 1,
                             'zoom': {},
                             'zoomStep': 0.1}

    def saveSettings(self):
        with codecs.open(self.jsonPath, 'w', encoding='utf-8') as jsonFile:
            json.dump(self.settings, jsonFile)

        # Touch the media folder to force sync
        ir.util.updateModificationTime(self.mediaDir)

    def showSettingsDialog(self):
        dialog = QDialog(mw)
        mainLayout = QVBoxLayout()

        zoomStepLabel = QLabel('Zoom Step')
        generalZoomLabel = QLabel('General Zoom')

        zoomStepEditBox = QLineEdit()
        zoomStepEditBox.setText(str(self.settings['zoomStep']))

        generalZoomEditBox = QLineEdit()
        generalZoomEditBox.setText(str(self.settings['textSizeMultiplier']))

        zoomGroupBox = QGroupBox('Zoom')

        zoomGroupLabelsLayout = QVBoxLayout()
        zoomGroupLabelsLayout.addWidget(zoomStepLabel)
        zoomGroupLabelsLayout.addWidget(generalZoomLabel)

        zoomGroupEditBoxesLayout = QVBoxLayout()
        zoomGroupEditBoxesLayout.addWidget(zoomStepEditBox)
        zoomGroupEditBoxesLayout.addWidget(generalZoomEditBox)

        zoomGroupLayout = QHBoxLayout()
        zoomGroupLayout.addLayout(zoomGroupLabelsLayout)
        zoomGroupLayout.addLayout(zoomGroupEditBoxesLayout)

        zoomGroupBox.setLayout(zoomGroupLayout)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        buttonBox.connect(buttonBox,
                          SIGNAL('accepted()'),
                          dialog,
                          SLOT('accept()'))

        mainLayout.addWidget(zoomGroupBox)
        mainLayout.addWidget(buttonBox)

        dialog.setLayout(mainLayout)
        dialog.setWindowTitle('IR Options')
        dialog.exec_()

        self.settings['zoomStep'] = float(zoomStepEditBox.text())
        self.settings['textSizeMultiplier'] = float(generalZoomEditBox.text())
