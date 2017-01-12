import codecs
import json
import os

from PyQt4.QtCore import SIGNAL, SLOT
from PyQt4.QtGui import (QDialog, QDialogButtonBox, QGroupBox, QHBoxLayout,
                         QLabel, QLineEdit, QRadioButton, QVBoxLayout)
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

        zoomGroupBox = QGroupBox('Zoom')

        zoomStepLabel = QLabel('Zoom Step')
        generalZoomLabel = QLabel('General Zoom')

        zoomStepEditBox = QLineEdit()
        zoomStepEditBox.setText(str(self.settings['zoomStep']))

        generalZoomEditBox = QLineEdit()
        generalZoomEditBox.setText(str(self.settings['textSizeMultiplier']))

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

        highlightGroupBox = QGroupBox('Highlighting')

        highlightColorLabel = QLabel('Color')
        highlightLabel = QLabel('Highlight')

        highlightColorEditBox = QLineEdit()
        highlightColorEditBox.setText(self.settings['highlightColor'])

        highlightBackgroundButton = QRadioButton('Background')
        highlightTextButton = QRadioButton('Text')

        if self.settings['doHighlightFont'] == 'true':
            highlightTextButton.setChecked(True)
        else:
            highlightBackgroundButton.setChecked(True)

        radioButtonLayout = QHBoxLayout()
        radioButtonLayout.addWidget(highlightBackgroundButton)
        radioButtonLayout.addWidget(highlightTextButton)

        highlightGroupLabelsLayout = QVBoxLayout()
        highlightGroupLabelsLayout.addWidget(highlightColorLabel)
        highlightGroupLabelsLayout.addWidget(highlightLabel)

        highlightGroupEditBoxesLayout = QVBoxLayout()
        highlightGroupEditBoxesLayout.addWidget(highlightColorEditBox)
        highlightGroupEditBoxesLayout.addLayout(radioButtonLayout)

        highlightGroupLayout = QHBoxLayout()
        highlightGroupLayout.addLayout(highlightGroupLabelsLayout)
        highlightGroupLayout.addLayout(highlightGroupEditBoxesLayout)

        highlightGroupBox.setLayout(highlightGroupLayout)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        buttonBox.connect(buttonBox,
                          SIGNAL('accepted()'),
                          dialog,
                          SLOT('accept()'))

        mainLayout.addWidget(zoomGroupBox)
        mainLayout.addWidget(highlightGroupBox)
        mainLayout.addWidget(buttonBox)

        dialog.setLayout(mainLayout)
        dialog.setWindowTitle('IR Options')
        dialog.exec_()

        self.settings['zoomStep'] = float(zoomStepEditBox.text())
        self.settings['textSizeMultiplier'] = float(generalZoomEditBox.text())
        self.settings['highlightColor'] = highlightColorEditBox.text()

        if highlightTextButton.isChecked():
            self.settings['doHighlightFont'] = 'true'
        else:
            self.settings['doHighlightFont'] = 'false'
