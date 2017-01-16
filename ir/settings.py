# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import codecs
import json
import os

try:
    from PyQt4.QtCore import Qt
    from PyQt4.QtGui import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                             QGroupBox, QHBoxLayout, QLabel, QRadioButton,
                             QSpinBox, QVBoxLayout)
except ImportError:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialog,
                                 QDialogButtonBox, QGroupBox, QHBoxLayout,
                                 QLabel, QRadioButton, QSpinBox, QVBoxLayout)

from aqt import mw

import ir.util


class SettingsManager():
    def __init__(self):
        self.loadSettings()

    def addMissingSettings(self):
        for key, value in self.defaults.items():
            if key not in self.settings:
                self.settings[key] = value

    def loadSettings(self):
        self.defaults = {'editExtractedNote': False,
                         'editSourceNote': False,
                         'extractPlainText': False,
                         'generalZoom': 1,
                         'highlightColor': 'yellow',
                         'textColor': 'black',
                         'lastDialogQuickKey': {},
                         'quickKeys': {},
                         'schedLaterInt': 50,
                         'schedLaterRandom': True,
                         'schedLaterType': 'pct',
                         'schedSoonInt': 10,
                         'schedSoonRandom': True,
                         'schedSoonType': 'pct',
                         'scroll': {},
                         'zoom': {},
                         'zoomStep': 0.1}

        self.mediaDir = os.path.join(mw.pm.profileFolder(), 'collection.media')
        self.jsonPath = os.path.join(self.mediaDir, '_ir.json')

        if os.path.isfile(self.jsonPath):
            with codecs.open(self.jsonPath, encoding='utf-8') as jsonFile:
                self.settings = json.load(jsonFile)
            self.addMissingSettings()
        else:
            self.settings = self.defaults

    def saveSettings(self):
        with codecs.open(self.jsonPath, 'w', encoding='utf-8') as jsonFile:
            json.dump(self.settings, jsonFile)

        # Touch the media folder to force sync
        ir.util.updateModificationTime(self.mediaDir)

    def getColorList(self):
        moduleDir, _ = os.path.split(__file__)
        colorsFilePath = os.path.join(moduleDir, 'data', 'colors.u8')
        with codecs.open(colorsFilePath, encoding='utf-8') as colorsFile:
            return [line.strip() for line in colorsFile]

    def showSettingsDialog(self):
        dialog = QDialog(mw)
        mainLayout = QVBoxLayout()

        extractionGroupBox = self.createExtractionGroupBox()
        highlightingGroupBox = self.createHighlightingGroupBox()
        zoomGroupBox = self.createZoomGroupBox()

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        buttonBox.accepted.connect(dialog.accept)

        mainLayout.addWidget(extractionGroupBox)
        mainLayout.addWidget(highlightingGroupBox)
        mainLayout.addWidget(zoomGroupBox)
        mainLayout.addWidget(buttonBox)

        dialog.setLayout(mainLayout)
        dialog.setWindowTitle('IR Options')
        dialog.exec_()

        self.settings['zoomStep'] = self.zoomStepSpinBox.value() / 100.0
        self.settings['generalZoom'] = self.generalZoomSpinBox.value() / 100.0
        self.settings['highlightColor'] = self.highlightColorComboBox.currentText()
        self.settings['textColor'] = self.textColorComboBox.currentText()

        if self.editNoteButton.isChecked():
            self.settings['editExtractedNote'] = True
        else:
            self.settings['editExtractedNote'] = False

        if self.editSourceNoteCheckBox.isChecked():
            self.settings['editSourceNote'] = True
        else:
            self.settings['editSourceNote'] = False

        if self.extractPlainTextCheckBox.isChecked():
            self.settings['extractPlainText'] = True
        else:
            self.settings['extractPlainText'] = False

    def createExtractionGroupBox(self):
        extractedTextLabel = QLabel('Extracted Text')

        self.editNoteButton = QRadioButton('Edit Note')
        editTitleButton = QRadioButton('Edit Title')

        if self.settings['editExtractedNote']:
            self.editNoteButton.setChecked(True)
        else:
            editTitleButton.setChecked(True)

        radioButtonLayout = QHBoxLayout()
        radioButtonLayout.addWidget(extractedTextLabel)
        radioButtonLayout.addWidget(self.editNoteButton)
        radioButtonLayout.addWidget(editTitleButton)

        self.editSourceNoteCheckBox = QCheckBox('Edit Source Note')
        self.extractPlainTextCheckBox = QCheckBox('Extract as Plain Text')

        if self.settings['editSourceNote']:
            self.editSourceNoteCheckBox.setChecked(True)

        if self.settings['extractPlainText']:
            self.extractPlainTextCheckBox.setChecked(True)

        groupBox = QGroupBox('Extraction')
        layout = QVBoxLayout()
        layout.addLayout(radioButtonLayout)
        layout.addWidget(self.editSourceNoteCheckBox)
        layout.addWidget(self.extractPlainTextCheckBox)
        groupBox.setLayout(layout)

        return groupBox

    def createHighlightingGroupBox(self):
        highlightColorLabel = QLabel('Background Color')
        textColorLabel = QLabel('Text Color')

        colors = self.getColorList()

        self.textColorComboBox = QComboBox()
        self.textColorComboBox.addItems(colors)
        index = self.textColorComboBox.findText(
                self.settings['textColor'], Qt.MatchFixedString)
        self.textColorComboBox.setCurrentIndex(index)

        self.highlightColorComboBox = QComboBox()
        self.highlightColorComboBox.addItems(colors)
        index = self.highlightColorComboBox.findText(
                self.settings['highlightColor'], Qt.MatchFixedString)
        self.highlightColorComboBox.setCurrentIndex(index)

        labelsLayout = QVBoxLayout()
        labelsLayout.addWidget(highlightColorLabel)
        labelsLayout.addWidget(textColorLabel)

        choicesLayout = QVBoxLayout()
        choicesLayout.addWidget(self.highlightColorComboBox)
        choicesLayout.addWidget(self.textColorComboBox)

        layout = QHBoxLayout()
        layout.addLayout(labelsLayout)
        layout.addLayout(choicesLayout)

        groupBox = QGroupBox('Highlighting')
        groupBox.setLayout(layout)

        return groupBox

    def createZoomGroupBox(self):
        zoomStepLabel = QLabel('Zoom Step')
        zoomStepPercentLabel = QLabel('%')
        generalZoomLabel = QLabel('General Zoom')
        generalZoomPercentLabel = QLabel('%')

        self.zoomStepSpinBox = QSpinBox()
        self.zoomStepSpinBox.setMinimum(5)
        self.zoomStepSpinBox.setMaximum(100)
        self.zoomStepSpinBox.setSingleStep(5)
        zoomStepPercent = round(self.settings['zoomStep'] * 100)
        self.zoomStepSpinBox.setValue(zoomStepPercent)

        self.generalZoomSpinBox = QSpinBox()
        self.generalZoomSpinBox.setMinimum(10)
        self.generalZoomSpinBox.setMaximum(200)
        self.generalZoomSpinBox.setSingleStep(10)
        generalZoomPercent = round(self.settings['generalZoom'] * 100)
        self.generalZoomSpinBox.setValue(generalZoomPercent)

        labelsLayout = QVBoxLayout()
        labelsLayout.addWidget(zoomStepLabel)
        labelsLayout.addWidget(generalZoomLabel)

        spinBoxesLayout = QVBoxLayout()
        spinBoxesLayout.addWidget(self.zoomStepSpinBox)
        spinBoxesLayout.addWidget(self.generalZoomSpinBox)

        percentsLayout = QVBoxLayout()
        percentsLayout.addWidget(zoomStepPercentLabel)
        percentsLayout.addWidget(generalZoomPercentLabel)

        layout = QHBoxLayout()
        layout.addLayout(labelsLayout)
        layout.addLayout(spinBoxesLayout)
        layout.addLayout(percentsLayout)

        groupBox = QGroupBox('Zoom')
        groupBox.setLayout(layout)

        return groupBox
