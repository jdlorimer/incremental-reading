# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from functools import partial
from sys import getfilesystemencoding
import codecs
import json
import os

from PyQt4.QtCore import Qt
from PyQt4.QtGui import (QButtonGroup,
                         QCheckBox,
                         QComboBox,
                         QDialog,
                         QDialogButtonBox,
                         QGroupBox,
                         QHBoxLayout,
                         QLabel,
                         QLineEdit,
                         QPushButton,
                         QRadioButton,
                         QSpinBox,
                         QTabWidget,
                         QVBoxLayout,
                         QWidget)

from anki.hooks import addHook
from aqt import mw
from aqt.utils import showInfo

from ir.util import (addMenuItem,
                     removeComboBoxItem,
                     setComboBoxItem,
                     updateModificationTime)


class SettingsManager():
    def __init__(self):
        self.settingsChanged = False
        self.loadSettings()

        if self.settingsChanged:
            showInfo('Your Incremental Reading settings file has been modified'
                     ' for compatibility reasons. Please take a moment to'
                     ' reconfigure the add-on to your liking.')

        addHook('unloadProfile', self.saveSettings)

    def addMenuItem(self):
        addMenuItem('Read', 'Options...', self.showDialog, 'Alt+1')

    def saveSettings(self):
        with codecs.open(self.jsonPath, 'w', encoding='utf-8') as jsonFile:
            json.dump(self.settings, jsonFile)

        updateModificationTime(self.mediaDir)

    def loadSettings(self):
        self.defaults = {'editExtract': False,
                         'editSource': False,
                         'extractBgColor': 'Green',
                         'extractDeck': None,
                         'extractKey': 'X',
                         'extractTextColor': 'White',
                         'generalZoom': 1,
                         'highlightBgColor': 'Yellow',
                         'highlightKey': 'H',
                         'highlightTextColor': 'Black',
                         'lineScrollFactor': 0.05,
                         'modelName': 'IR3',
                         'pageScrollFactor': 0.5,
                         'plainText': False,
                         'quickKeys': {},
                         'removeKey': 'Z',
                         'schedLaterInt': 50,
                         'schedLaterRandom': True,
                         'schedLaterType': 'pct',
                         'schedSoonInt': 10,
                         'schedSoonRandom': True,
                         'schedSoonType': 'pct',
                         'scroll': {},
                         'undoKey': 'U',
                         'zoom': {},
                         'zoomStep': 0.1}

        self.mediaDir = os.path.join(mw.pm.profileFolder(), 'collection.media')
        self.jsonPath = os.path.join(self.mediaDir, '_ir.json')

        if os.path.isfile(self.jsonPath):
            with codecs.open(self.jsonPath, encoding='utf-8') as jsonFile:
                self.settings = json.load(jsonFile)
            self.addMissingSettings()
            self.removeOutdatedQuickKeys()
        else:
            self.settings = self.defaults

        self.loadMenuItems()

    def addMissingSettings(self):
        for k, v in self.defaults.items():
            if k not in self.settings:
                self.settings[k] = v
                self.settingsChanged = True

    def removeOutdatedQuickKeys(self):
        required = ['alt',
                    'bgColor',
                    'ctrl',
                    'deckName',
                    'editExtract',
                    'editSource',
                    'fieldName',
                    'modelName',
                    'regularKey',
                    'shift',
                    'textColor']

        for keyCombo, quickKey in self.settings['quickKeys'].copy().items():
            for k in required:
                if k not in quickKey:
                    self.settings['quickKeys'].pop(keyCombo)
                    self.settingsChanged = True
                    break

    def loadMenuItems(self):
        self.clearMenuItems()

        for keyCombo, quickKey in self.settings['quickKeys'].items():
            menuText = 'Add Card [%s -> %s]' % (quickKey['modelName'],
                                                quickKey['deckName'])
            function = partial(mw.readingManager.quickAdd, quickKey)
            mw.readingManager.quickKeyActions.append(
                addMenuItem('Read', menuText, function, keyCombo))

    def clearMenuItems(self):
        if mw.readingManager.quickKeyActions:
            for action in mw.readingManager.quickKeyActions:
                mw.customMenus['Read'].removeAction(action)
            mw.readingManager.quickKeyActions = []

    def showDialog(self):
        dialog = QDialog(mw)

        zoomScrollLayout = QHBoxLayout()
        zoomScrollLayout.addWidget(self.createZoomGroupBox())
        zoomScrollLayout.addWidget(self.createScrollGroupBox())

        zoomScrollTab = QWidget()
        zoomScrollTab.setLayout(zoomScrollLayout)

        tabWidget = QTabWidget()
        tabWidget.setUsesScrollButtons(False)
        tabWidget.addTab(self.createGeneralTab(), 'General')
        tabWidget.addTab(self.createExtractionTab(), 'Extraction')
        tabWidget.addTab(self.createHighlightingTab(), 'Highlighting')
        tabWidget.addTab(self.createSchedulingTab(), 'Scheduling')
        tabWidget.addTab(self.createQuickKeysTab(), 'Quick Keys')
        tabWidget.addTab(zoomScrollTab, 'Zoom / Scroll')

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        buttonBox.accepted.connect(dialog.accept)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(tabWidget)
        mainLayout.addWidget(buttonBox)

        dialog.setLayout(mainLayout)
        dialog.setWindowTitle('Incremental Reading Options')
        dialog.exec_()

        self.settings['zoomStep'] = self.zoomStepSpinBox.value() / 100.0
        self.settings['generalZoom'] = self.generalZoomSpinBox.value() / 100.0
        self.settings['lineScrollFactor'] = self.lineStepSpinBox.value() / 100.0
        self.settings['pageScrollFactor'] = self.pageStepSpinBox.value() / 100.0
        self.settings['editExtract'] = self.editExtractButton.isChecked()
        self.settings['editSource'] = self.editSourceCheckBox.isChecked()
        self.settings['plainText'] = self.plainTextCheckBox.isChecked()
        self.settings['schedSoonRandom'] = self.soonRandomCheckBox.isChecked()
        self.settings['schedLaterRandom'] = self.laterRandomCheckBox.isChecked()

        if self.extractDeckComboBox.currentText() == '[Current Deck]':
            self.settings['extractDeck'] = None
        else:
            self.settings['extractDeck'] = self.extractDeckComboBox.currentText()

        try:
            self.settings['schedSoonInt'] = int(
                self.soonIntegerEditBox.text())
            self.settings['schedLaterInt'] = int(
                self.laterIntegerEditBox.text())
        except:
            pass

        if self.soonPercentButton.isChecked():
            self.settings['schedSoonType'] = 'pct'
        else:
            self.settings['schedSoonType'] = 'cnt'

        if self.laterPercentButton.isChecked():
            self.settings['schedLaterType'] = 'pct'
        else:
            self.settings['schedLaterType'] = 'cnt'

        mw.viewManager.resetZoom(mw.state)

    def createGeneralTab(self):
        extractKeyLabel = QLabel('Extract Key')
        highlightKeyLabel = QLabel('Highlight Key')
        removeKeyLabel = QLabel('Remove Key')

        self.extractKeyComboBox = QComboBox()
        self.highlightKeyComboBox = QComboBox()
        self.removeKeyComboBox = QComboBox()

        keys = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789')
        for comboBox in [self.extractKeyComboBox,
                         self.highlightKeyComboBox,
                         self.removeKeyComboBox]:
            comboBox.addItems(keys)

        self.setDefaultKeys()

        extractKeyLayout = QHBoxLayout()
        extractKeyLayout.addWidget(extractKeyLabel)
        extractKeyLayout.addWidget(self.extractKeyComboBox)

        highlightKeyLayout = QHBoxLayout()
        highlightKeyLayout.addWidget(highlightKeyLabel)
        highlightKeyLayout.addWidget(self.highlightKeyComboBox)

        removeKeyLayout = QHBoxLayout()
        removeKeyLayout.addWidget(removeKeyLabel)
        removeKeyLayout.addWidget(self.removeKeyComboBox)

        saveButton = QPushButton('Save')
        saveButton.clicked.connect(self.saveKeys)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(saveButton)

        basicControlsLayout = QVBoxLayout()
        basicControlsLayout.addLayout(extractKeyLayout)
        basicControlsLayout.addLayout(highlightKeyLayout)
        basicControlsLayout.addLayout(removeKeyLayout)
        basicControlsLayout.addLayout(buttonLayout)
        basicControlsLayout.addStretch()

        groupBox = QGroupBox('Basic Controls')
        groupBox.setLayout(basicControlsLayout)

        layout = QHBoxLayout()
        layout.addWidget(groupBox)

        tab = QWidget()
        tab.setLayout(layout)

        return tab

    def setDefaultKeys(self):
        setComboBoxItem(self.extractKeyComboBox, self.settings['extractKey'])
        setComboBoxItem(self.highlightKeyComboBox,
                        self.settings['highlightKey'])
        setComboBoxItem(self.removeKeyComboBox, self.settings['removeKey'])

    def saveKeys(self):
        keys = [self.extractKeyComboBox.currentText(),
                self.highlightKeyComboBox.currentText(),
                self.removeKeyComboBox.currentText()]

        if len(set(keys)) < 3:
            showInfo('There is a conflict with the keys you have chosen.'
                     ' Please try again.')
            self.setDefaultKeys()
        else:
            self.settings['extractKey'] = self.extractKeyComboBox.currentText()
            self.settings['highlightKey'] = self.highlightKeyComboBox.currentText()
            self.settings['removeKey'] = self.removeKeyComboBox.currentText()

    def createExtractionTab(self):
        extractDeckLabel = QLabel('Extracts Deck')
        self.extractDeckComboBox = QComboBox()
        deckNames = sorted([d['name'] for d in mw.col.decks.all()])
        self.extractDeckComboBox.addItem('[Current Deck]')
        self.extractDeckComboBox.addItems(deckNames)

        if self.settings['extractDeck']:
            setComboBoxItem(self.extractDeckComboBox,
                            self.settings['extractDeck'])
        else:
            setComboBoxItem(self.extractDeckComboBox, '[Current Deck]')

        extractDeckLayout = QHBoxLayout()
        extractDeckLayout.addWidget(extractDeckLabel)
        extractDeckLayout.addWidget(self.extractDeckComboBox)

        self.editExtractButton = QRadioButton('Edit Extracted Note')
        enterTitleButton = QRadioButton('Enter Title Only')

        if self.settings['editExtract']:
            self.editExtractButton.setChecked(True)
        else:
            enterTitleButton.setChecked(True)

        radioButtonsLayout = QHBoxLayout()
        radioButtonsLayout.addWidget(self.editExtractButton)
        radioButtonsLayout.addWidget(enterTitleButton)
        radioButtonsLayout.addStretch()

        self.editSourceCheckBox = QCheckBox('Edit Source Note')
        self.plainTextCheckBox = QCheckBox('Extract as Plain Text')

        if self.settings['editSource']:
            self.editSourceCheckBox.setChecked(True)

        if self.settings['plainText']:
            self.plainTextCheckBox.setChecked(True)

        layout = QVBoxLayout()
        layout.addLayout(extractDeckLayout)
        layout.addLayout(radioButtonsLayout)
        layout.addWidget(self.editSourceCheckBox)
        layout.addWidget(self.plainTextCheckBox)
        layout.addStretch()

        tab = QWidget()
        tab.setLayout(layout)

        return tab

    def createHighlightingTab(self):
        colorsGroupBox = self.createColorsGroupBox()
        colorPreviewGroupBox = self.createColorPreviewGroupBox()

        horizontalLayout = QHBoxLayout()
        horizontalLayout.addWidget(colorsGroupBox)
        horizontalLayout.addWidget(colorPreviewGroupBox)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Save)
        buttonBox.accepted.connect(self.saveHighlightSettings)

        layout = QVBoxLayout()
        layout.addWidget(self.targetComboBox)
        layout.addLayout(horizontalLayout)
        layout.addWidget(buttonBox)
        layout.addStretch()

        tab = QWidget()
        tab.setLayout(layout)

        return tab

    def saveHighlightSettings(self):
        target = self.targetComboBox.currentText()
        bgColor = self.bgColorComboBox.currentText()
        textColor = self.textColorComboBox.currentText()

        if target == self.settings['highlightKey']:
            self.settings['highlightBgColor'] = bgColor
            self.settings['highlightTextColor'] = textColor
        elif target == self.settings['extractKey']:
            self.settings['extractBgColor'] = bgColor
            self.settings['extractTextColor'] = textColor
        else:
            self.settings['quickKeys'][target]['bgColor'] = bgColor
            self.settings['quickKeys'][target]['textColor'] = textColor

    def createColorsGroupBox(self):
        self.targetComboBox = QComboBox()
        self.targetComboBox.addItem(self.settings['highlightKey'])
        self.targetComboBox.addItem(self.settings['extractKey'])
        self.targetComboBox.addItems(self.settings['quickKeys'].keys())
        self.targetComboBox.currentIndexChanged.connect(
            self.updateHighlightingTab)

        targetLayout = QHBoxLayout()
        targetLayout.addWidget(self.targetComboBox)
        targetLayout.addStretch()

        colors = self.getColorList()

        self.bgColorComboBox = QComboBox()
        self.bgColorComboBox.addItems(colors)
        setComboBoxItem(self.bgColorComboBox,
                        self.settings['highlightBgColor'])
        self.bgColorComboBox.currentIndexChanged.connect(
            self.updateColorPreview)

        self.textColorComboBox = QComboBox()
        self.textColorComboBox.addItems(colors)
        setComboBoxItem(self.textColorComboBox,
                        self.settings['highlightTextColor'])
        self.textColorComboBox.currentIndexChanged.connect(
            self.updateColorPreview)

        bgColorLabel = QLabel('Background')
        bgColorLayout = QHBoxLayout()
        bgColorLayout.addWidget(bgColorLabel)
        bgColorLayout.addSpacing(10)
        bgColorLayout.addWidget(self.bgColorComboBox)

        textColorLabel = QLabel('Text')
        textColorLayout = QHBoxLayout()
        textColorLayout.addWidget(textColorLabel)
        textColorLayout.addSpacing(10)
        textColorLayout.addWidget(self.textColorComboBox)

        layout = QVBoxLayout()
        layout.addLayout(bgColorLayout)
        layout.addLayout(textColorLayout)
        layout.addStretch()

        groupBox = QGroupBox('Colors')
        groupBox.setLayout(layout)

        return groupBox

    def updateHighlightingTab(self):
        target = self.targetComboBox.currentText()
        if target == self.settings['highlightKey']:
            setComboBoxItem(self.bgColorComboBox,
                            self.settings['highlightBgColor'])
            setComboBoxItem(self.textColorComboBox,
                            self.settings['highlightTextColor'])
        elif target == self.settings['extractKey']:
            setComboBoxItem(self.bgColorComboBox,
                            self.settings['extractBgColor'])
            setComboBoxItem(self.textColorComboBox,
                            self.settings['extractTextColor'])
        else:
            setComboBoxItem(self.bgColorComboBox,
                            self.settings['quickKeys'][target]['bgColor'])
            setComboBoxItem(self.textColorComboBox,
                            self.settings['quickKeys'][target]['textColor'])

    def getColorList(self):
        moduleDir, _ = os.path.split(__file__)
        moduleDir = moduleDir.decode(getfilesystemencoding())
        colorsFilePath = os.path.join(moduleDir, 'data', 'colors.u8')
        with codecs.open(colorsFilePath, encoding='utf-8') as colorsFile:
            return [line.strip() for line in colorsFile]

    def updateColorPreview(self):
        bgColor = self.bgColorComboBox.currentText()
        textColor = self.textColorComboBox.currentText()
        styleSheet = ('QLabel {'
                      'background-color: %s;'
                      'color: %s;'
                      'padding: 10px;'
                      'font-size: 16px;'
                      'font-family: tahoma, geneva, sans-serif;'
                      '}') % (bgColor, textColor)
        self.colorPreviewLabel.setStyleSheet(styleSheet)
        self.colorPreviewLabel.setAlignment(Qt.AlignCenter)

    def createColorPreviewGroupBox(self):
        self.colorPreviewLabel = QLabel('Example Text')
        self.updateColorPreview()
        colorPreviewLayout = QVBoxLayout()
        colorPreviewLayout.addWidget(self.colorPreviewLabel)

        groupBox = QGroupBox('Preview')
        groupBox.setLayout(colorPreviewLayout)

        return groupBox

    def createSchedulingTab(self):
        soonLabel = QLabel('Soon Button')
        laterLabel = QLabel('Later Button')

        self.soonPercentButton = QRadioButton('Percent')
        soonPositionButton = QRadioButton('Position')
        self.laterPercentButton = QRadioButton('Percent')
        laterPositionButton = QRadioButton('Position')
        self.soonRandomCheckBox = QCheckBox('Randomize')
        self.laterRandomCheckBox = QCheckBox('Randomize')

        self.soonIntegerEditBox = QLineEdit()
        self.soonIntegerEditBox.setFixedWidth(100)
        self.laterIntegerEditBox = QLineEdit()
        self.laterIntegerEditBox.setFixedWidth(100)

        if self.settings['schedSoonType'] == 'pct':
            self.soonPercentButton.setChecked(True)
        else:
            soonPositionButton.setChecked(True)

        if self.settings['schedLaterType'] == 'pct':
            self.laterPercentButton.setChecked(True)
        else:
            laterPositionButton.setChecked(True)

        if self.settings['schedSoonRandom']:
            self.soonRandomCheckBox.setChecked(True)

        if self.settings['schedLaterRandom']:
            self.laterRandomCheckBox.setChecked(True)

        self.soonIntegerEditBox.setText(str(self.settings['schedSoonInt']))
        self.laterIntegerEditBox.setText(str(self.settings['schedLaterInt']))

        soonLayout = QHBoxLayout()
        soonLayout.addWidget(soonLabel)
        soonLayout.addStretch()
        soonLayout.addWidget(self.soonIntegerEditBox)
        soonLayout.addWidget(self.soonPercentButton)
        soonLayout.addWidget(soonPositionButton)
        soonLayout.addWidget(self.soonRandomCheckBox)

        laterLayout = QHBoxLayout()
        laterLayout.addWidget(laterLabel)
        laterLayout.addStretch()
        laterLayout.addWidget(self.laterIntegerEditBox)
        laterLayout.addWidget(self.laterPercentButton)
        laterLayout.addWidget(laterPositionButton)
        laterLayout.addWidget(self.laterRandomCheckBox)

        soonButtonGroup = QButtonGroup(soonLayout)
        soonButtonGroup.addButton(self.soonPercentButton)
        soonButtonGroup.addButton(soonPositionButton)

        laterButtonGroup = QButtonGroup(laterLayout)
        laterButtonGroup.addButton(self.laterPercentButton)
        laterButtonGroup.addButton(laterPositionButton)

        layout = QVBoxLayout()
        layout.addLayout(soonLayout)
        layout.addLayout(laterLayout)
        layout.addStretch()

        tab = QWidget()
        tab.setLayout(layout)

        return tab

    def createQuickKeysTab(self):
        destDeckLabel = QLabel('Destination Deck')
        noteTypeLabel = QLabel('Note Type')
        textFieldLabel = QLabel('Paste Text to Field')
        keyComboLabel = QLabel('Key Combination')

        self.quickKeysComboBox = QComboBox()
        self.quickKeysComboBox.addItem('')
        self.quickKeysComboBox.addItems(self.settings['quickKeys'].keys())
        self.quickKeysComboBox.currentIndexChanged.connect(
            self.updateQuickKeysTab)

        self.destDeckComboBox = QComboBox()
        self.noteTypeComboBox = QComboBox()
        self.textFieldComboBox = QComboBox()
        self.quickKeyEditExtractCheckBox = QCheckBox('Edit Extracted Note')
        self.quickKeyEditSourceCheckBox = QCheckBox('Edit Source Note')
        self.quickKeyPlainTextCheckBox = QCheckBox('Extract as Plain Text')

        self.ctrlKeyCheckBox = QCheckBox('Ctrl')
        self.shiftKeyCheckBox = QCheckBox('Shift')
        self.altKeyCheckBox = QCheckBox('Alt')
        self.regularKeyComboBox = QComboBox()
        self.regularKeyComboBox.addItem('')
        self.regularKeyComboBox.addItems(
            list('ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789'))

        destDeckLayout = QHBoxLayout()
        destDeckLayout.addWidget(destDeckLabel)
        destDeckLayout.addWidget(self.destDeckComboBox)

        noteTypeLayout = QHBoxLayout()
        noteTypeLayout.addWidget(noteTypeLabel)
        noteTypeLayout.addWidget(self.noteTypeComboBox)

        textFieldLayout = QHBoxLayout()
        textFieldLayout.addWidget(textFieldLabel)
        textFieldLayout.addWidget(self.textFieldComboBox)

        keyComboLayout = QHBoxLayout()
        keyComboLayout.addWidget(keyComboLabel)
        keyComboLayout.addStretch()
        keyComboLayout.addWidget(self.ctrlKeyCheckBox)
        keyComboLayout.addWidget(self.shiftKeyCheckBox)
        keyComboLayout.addWidget(self.altKeyCheckBox)
        keyComboLayout.addWidget(self.regularKeyComboBox)

        deckNames = sorted([d['name'] for d in mw.col.decks.all()])
        self.destDeckComboBox.addItem('')
        self.destDeckComboBox.addItems(deckNames)

        modelNames = sorted([m['name'] for m in mw.col.models.all()])
        self.noteTypeComboBox.addItem('')
        self.noteTypeComboBox.addItems(modelNames)
        self.noteTypeComboBox.currentIndexChanged.connect(self.updateFieldList)

        newButton = QPushButton('New')
        newButton.clicked.connect(self.clearQuickKeysTab)
        deleteButton = QPushButton('Delete')
        deleteButton.clicked.connect(self.deleteQuickKey)
        saveButton = QPushButton('Save')
        saveButton.clicked.connect(self.setQuickKey)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(newButton)
        buttonLayout.addWidget(deleteButton)
        buttonLayout.addWidget(saveButton)

        layout = QVBoxLayout()
        layout.addWidget(self.quickKeysComboBox)
        layout.addLayout(destDeckLayout)
        layout.addLayout(noteTypeLayout)
        layout.addLayout(textFieldLayout)
        layout.addLayout(keyComboLayout)
        layout.addWidget(self.quickKeyEditExtractCheckBox)
        layout.addWidget(self.quickKeyEditSourceCheckBox)
        layout.addWidget(self.quickKeyPlainTextCheckBox)
        layout.addLayout(buttonLayout)

        tab = QWidget()
        tab.setLayout(layout)

        return tab

    def updateQuickKeysTab(self):
        quickKey = self.quickKeysComboBox.currentText()
        if quickKey:
            model = self.settings['quickKeys'][quickKey]
            setComboBoxItem(self.destDeckComboBox, model['deckName'])
            setComboBoxItem(self.noteTypeComboBox, model['modelName'])
            setComboBoxItem(self.textFieldComboBox, model['fieldName'])
            self.ctrlKeyCheckBox.setChecked(model['ctrl'])
            self.shiftKeyCheckBox.setChecked(model['shift'])
            self.altKeyCheckBox.setChecked(model['alt'])
            setComboBoxItem(self.regularKeyComboBox, model['regularKey'])
            self.quickKeyEditExtractCheckBox.setChecked(model['editExtract'])
            self.quickKeyEditSourceCheckBox.setChecked(model['editSource'])
            self.quickKeyPlainTextCheckBox.setChecked(model['plainText'])
        else:
            self.clearQuickKeysTab()

    def updateFieldList(self):
        modelName = self.noteTypeComboBox.currentText()
        self.textFieldComboBox.clear()
        if modelName:
            model = mw.col.models.byName(modelName)
            fieldNames = [f['name'] for f in model['flds']]
            self.textFieldComboBox.addItems(fieldNames)

    def clearQuickKeysTab(self):
        self.quickKeysComboBox.setCurrentIndex(0)
        self.destDeckComboBox.setCurrentIndex(0)
        self.noteTypeComboBox.setCurrentIndex(0)
        self.textFieldComboBox.setCurrentIndex(0)
        self.ctrlKeyCheckBox.setChecked(False)
        self.shiftKeyCheckBox.setChecked(False)
        self.altKeyCheckBox.setChecked(False)
        self.regularKeyComboBox.setCurrentIndex(0)
        self.quickKeyEditExtractCheckBox.setChecked(False)
        self.quickKeyEditSourceCheckBox.setChecked(False)
        self.quickKeyPlainTextCheckBox.setChecked(False)

    def deleteQuickKey(self):
        quickKey = self.quickKeysComboBox.currentText()
        if quickKey:
            self.settings['quickKeys'].pop(quickKey)
            removeComboBoxItem(self.quickKeysComboBox, quickKey)
            self.clearQuickKeysTab()
            self.loadMenuItems()

    def setQuickKey(self):
        quickKey = {'deckName': self.destDeckComboBox.currentText(),
                    'modelName': self.noteTypeComboBox.currentText(),
                    'fieldName': self.textFieldComboBox.currentText(),
                    'ctrl': self.ctrlKeyCheckBox.isChecked(),
                    'shift': self.shiftKeyCheckBox.isChecked(),
                    'alt': self.altKeyCheckBox.isChecked(),
                    'regularKey': self.regularKeyComboBox.currentText(),
                    'bgColor': self.bgColorComboBox.currentText(),
                    'textColor': self.textColorComboBox.currentText(),
                    'editExtract': self.quickKeyEditExtractCheckBox.isChecked(),
                    'editSource': self.quickKeyEditSourceCheckBox.isChecked(),
                    'plainText': self.quickKeyPlainTextCheckBox.isChecked()}

        for k in ['deckName', 'modelName', 'regularKey']:
            if not quickKey[k]:
                showInfo('Please complete all settings. Destination deck,'
                         ' note type, and a letter or number for the key'
                         ' combination are required.')
                return

        keyCombo = ''
        if quickKey['ctrl']:
            keyCombo += 'Ctrl+'
        if quickKey['shift']:
            keyCombo += 'Shift+'
        if quickKey['alt']:
            keyCombo += 'Alt+'
        keyCombo += quickKey['regularKey']

        self.settings['quickKeys'][keyCombo] = quickKey
        self.loadMenuItems()

        showInfo('New shortcut added: %s' % keyCombo)

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

        zoomStepLayout = QHBoxLayout()
        zoomStepLayout.addWidget(zoomStepLabel)
        zoomStepLayout.addStretch()
        zoomStepLayout.addWidget(self.zoomStepSpinBox)
        zoomStepLayout.addWidget(zoomStepPercentLabel)

        generalZoomLayout = QHBoxLayout()
        generalZoomLayout.addWidget(generalZoomLabel)
        generalZoomLayout.addStretch()
        generalZoomLayout.addWidget(self.generalZoomSpinBox)
        generalZoomLayout.addWidget(generalZoomPercentLabel)

        layout = QVBoxLayout()
        layout.addLayout(zoomStepLayout)
        layout.addLayout(generalZoomLayout)
        layout.addStretch()

        groupBox = QGroupBox('Zoom')
        groupBox.setLayout(layout)

        return groupBox

    def createScrollGroupBox(self):
        lineStepLabel = QLabel('Line Step')
        lineStepPercentLabel = QLabel('%')
        pageStepLabel = QLabel('Page Step')
        pageStepPercentLabel = QLabel('%')

        self.lineStepSpinBox = QSpinBox()
        self.lineStepSpinBox.setMinimum(5)
        self.lineStepSpinBox.setMaximum(100)
        self.lineStepSpinBox.setSingleStep(5)
        self.lineStepSpinBox.setValue(
            round(self.settings['lineScrollFactor'] * 100))

        self.pageStepSpinBox = QSpinBox()
        self.pageStepSpinBox.setMinimum(5)
        self.pageStepSpinBox.setMaximum(100)
        self.pageStepSpinBox.setSingleStep(5)
        self.pageStepSpinBox.setValue(
            round(self.settings['pageScrollFactor'] * 100))

        lineStepLayout = QHBoxLayout()
        lineStepLayout.addWidget(lineStepLabel)
        lineStepLayout.addStretch()
        lineStepLayout.addWidget(self.lineStepSpinBox)
        lineStepLayout.addWidget(lineStepPercentLabel)

        pageStepLayout = QHBoxLayout()
        pageStepLayout.addWidget(pageStepLabel)
        pageStepLayout.addStretch()
        pageStepLayout.addWidget(self.pageStepSpinBox)
        pageStepLayout.addWidget(pageStepPercentLabel)

        layout = QVBoxLayout()
        layout.addLayout(lineStepLayout)
        layout.addLayout(pageStepLayout)
        layout.addStretch()

        groupBox = QGroupBox('Scroll')
        groupBox.setLayout(layout)

        return groupBox
