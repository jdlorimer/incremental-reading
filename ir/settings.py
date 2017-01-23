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
                         'backgroundColor': 'yellow',
                         'editSourceNote': False,
                         'extractPlainText': False,
                         'generalZoom': 1,
                         'lastDialogQuickKey': {},
                         'lineScrollFactor': 0.05,
                         'pageScrollFactor': 0.5,
                         'quickKeys': {},
                         'schedLaterInt': 50,
                         'schedLaterRandom': True,
                         'schedLaterType': 'pct',
                         'schedSoonInt': 10,
                         'schedSoonRandom': True,
                         'schedSoonType': 'pct',
                         'scroll': {},
                         'textColor': 'black',
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
        horizontalLayout1 = QHBoxLayout()
        horizontalLayout2 = QHBoxLayout()

        extractionGroupBox = self.createExtractionGroupBox()
        highlightingGroupBox = self.createHighlightingGroupBox()
        zoomGroupBox = self.createZoomGroupBox()
        scrollGroupBox = self.createScrollGroupBox()

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        buttonBox.accepted.connect(dialog.accept)

        horizontalLayout1.addWidget(extractionGroupBox)
        horizontalLayout1.addWidget(highlightingGroupBox)
        horizontalLayout2.addWidget(zoomGroupBox)
        horizontalLayout2.addWidget(scrollGroupBox)

        mainLayout.addLayout(horizontalLayout1)
        mainLayout.addLayout(horizontalLayout2)
        mainLayout.addWidget(buttonBox)

        dialog.setLayout(mainLayout)
        dialog.setWindowTitle('IR Options')
        dialog.exec_()

        self.settings['zoomStep'] = self.zoomStepSpinBox.value() / 100.0
        self.settings['generalZoom'] = self.generalZoomSpinBox.value() / 100.0
        self.settings['lineScrollFactor'] = self.lineScrollPercentSpinBox.value() / 100.0
        self.settings['pageScrollFactor'] = self.pageScrollPercentSpinBox.value() / 100.0
        self.settings['backgroundColor'] = self.backgroundColorComboBox.currentText()
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

        mw.viewManager.resetZoom(mw.state)

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

    def updateColorPreviewLabel(self):
        backgroundColor = self.backgroundColorComboBox.currentText()
        textColor = self.textColorComboBox.currentText()
        styleSheet = ('QLabel {'
                      'background-color: %s;'
                      'color: %s;'
                      'padding: 10px;}') % (backgroundColor, textColor)
        self.colorPreviewLabel.setStyleSheet(styleSheet)

    def createHighlightingGroupBox(self):
        backgroundColorLabel = QLabel('Background Color')
        textColorLabel = QLabel('Text Color')

        colors = self.getColorList()

        self.textColorComboBox = QComboBox()
        self.textColorComboBox.addItems(colors)
        index = self.textColorComboBox.findText(
                self.settings['textColor'], Qt.MatchFixedString)
        self.textColorComboBox.setCurrentIndex(index)
        self.textColorComboBox.currentIndexChanged.connect(
            self.updateColorPreviewLabel)

        self.backgroundColorComboBox = QComboBox()
        self.backgroundColorComboBox.addItems(colors)
        index = self.backgroundColorComboBox.findText(
                self.settings['backgroundColor'], Qt.MatchFixedString)
        self.backgroundColorComboBox.setCurrentIndex(index)
        self.backgroundColorComboBox.currentIndexChanged.connect(
            self.updateColorPreviewLabel)

        labelsLayout = QVBoxLayout()
        labelsLayout.addWidget(backgroundColorLabel)
        labelsLayout.addWidget(textColorLabel)

        choicesLayout = QVBoxLayout()
        choicesLayout.addWidget(self.backgroundColorComboBox)
        choicesLayout.addWidget(self.textColorComboBox)

        self.colorPreviewLabel = QLabel('Example Text')
        self.updateColorPreviewLabel()
        colorPreviewLayout = QVBoxLayout()
        colorPreviewLayout.addWidget(self.colorPreviewLabel)

        layout = QHBoxLayout()
        layout.addLayout(labelsLayout)
        layout.addLayout(choicesLayout)
        layout.addLayout(colorPreviewLayout)

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

    def createScrollGroupBox(self):
        lineScrollStepLabel = QLabel('Line Up/Down Step')
        lineScrollPercentLabel = QLabel('% of Window')
        pageScrollStepLabel = QLabel('Page Up/Down Step')
        pageScrollPercentLabel = QLabel('% of Window')

        self.lineScrollPercentSpinBox = QSpinBox()
        self.lineScrollPercentSpinBox.setMinimum(5)
        self.lineScrollPercentSpinBox.setMaximum(100)
        self.lineScrollPercentSpinBox.setSingleStep(5)
        lineScrollPercent = round(self.settings['lineScrollFactor'] * 100)
        self.lineScrollPercentSpinBox.setValue(lineScrollPercent)

        self.pageScrollPercentSpinBox = QSpinBox()
        self.pageScrollPercentSpinBox.setMinimum(5)
        self.pageScrollPercentSpinBox.setMaximum(100)
        self.pageScrollPercentSpinBox.setSingleStep(5)
        pageScrollPercent = round(self.settings['pageScrollFactor'] * 100)
        self.pageScrollPercentSpinBox.setValue(pageScrollPercent)

        labelsLayout = QVBoxLayout()
        labelsLayout.addWidget(lineScrollStepLabel)
        labelsLayout.addWidget(pageScrollStepLabel)

        spinBoxesLayout = QVBoxLayout()
        spinBoxesLayout.addWidget(self.lineScrollPercentSpinBox)
        spinBoxesLayout.addWidget(self.pageScrollPercentSpinBox)

        percentsLayout = QVBoxLayout()
        percentsLayout.addWidget(lineScrollPercentLabel)
        percentsLayout.addWidget(pageScrollPercentLabel)

        layout = QHBoxLayout()
        layout.addLayout(labelsLayout)
        layout.addLayout(spinBoxesLayout)
        layout.addLayout(percentsLayout)

        groupBox = QGroupBox('Scroll')
        groupBox.setLayout(layout)

        return groupBox
