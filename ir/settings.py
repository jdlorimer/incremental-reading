# Copyright 2013 Tiago Barroso
# Copyright 2013 Frank Kmiec
# Copyright 2013-2016 Aleksej
# Copyright 2017 Luo Li-Yan <joseph.lorimer13@gmail.com>
#
# Permission to use, copy, modify, and distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright
# notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

from functools import partial
from unicodedata import normalize
import json
import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QButtonGroup,
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
                             QTabWidget,
                             QVBoxLayout,
                             QWidget)

from anki.hooks import addHook
from aqt import mw
from aqt.tagedit import TagEdit
from aqt.utils import showInfo, showWarning, tooltip

from ._version import __version__
from .about import IR_GITHUB_URL
from .util import (addMenuItem,
                   createSpinBox,
                   removeComboBoxItem,
                   setComboBoxItem,
                   setMenuVisibility,
                   updateModificationTime)


class SettingsManager:
    def __init__(self):
        mw.addonManager.setConfigAction(__name__, self.showDialog)
        addHook('unloadProfile', self.saveSettings)

        self.defaults = {'badTags': ['iframe', 'script'],
                         'copyTitle': False,
                         'editExtract': False,
                         'editSource': False,
                         'extractBgColor': 'Green',
                         'extractDeck': None,
                         'extractKey': 'x',
                         'extractMethod': 'percent',
                         'extractRandom': True,
                         'extractTextColor': 'White',
                         'extractValue': 30,
                         'feedLog': {},
                         'generalZoom': 1,
                         'highlightBgColor': 'Yellow',
                         'highlightKey': 'h',
                         'highlightTextColor': 'Black',
                         'importDeck': 'Default',
                         'laterMethod': 'percent',
                         'laterRandom': True,
                         'laterValue': 50,
                         'limitWidth': True,
                         'limitWidthAll': False,
                         'lineScrollFactor': 0.05,
                         'maxWidth': 600,
                         'modelName': 'IR3',
                         'pageScrollFactor': 0.5,
                         'plainText': False,
                         'quickKeys': {},
                         'removeKey': 'z',
                         'scheduleExtract': True,
                         'scroll': {},
                         'soonMethod': 'percent',
                         'soonRandom': True,
                         'soonValue': 10,
                         'sourceField': 'Source',
                         'sourceFormat': '{url} ({date})',
                         'textField': 'Text',
                         'titleField': 'Title',
                         'undoKey': 'u',
                         'userAgent': 'IR/{} (+{})'.format(
                             __version__, IR_GITHUB_URL),
                         'zoom': {},
                         'zoomStep': 0.1}

    def loadSettings(self):
        self.settingsChanged = False
        self.mediaDir = os.path.join(mw.pm.profileFolder(), 'collection.media')
        self.jsonPath = os.path.join(self.mediaDir, '_ir.json')

        if os.path.isfile(self.jsonPath):
            with open(self.jsonPath, encoding='utf-8') as jsonFile:
                self.settings = json.load(jsonFile)
            self._addMissingSettings()
            self._removeOutdatedQuickKeys()
        else:
            self.settings = self.defaults

        if self.settingsChanged:
            showInfo('Your Incremental Reading settings file has been modified'
                     ' for compatibility reasons. Please take a moment to'
                     ' reconfigure the add-on to your liking.')

        return self.settings

    def _addMissingSettings(self):
        for k, v in self.defaults.items():
            if k not in self.settings:
                self.settings[k] = v
                self.settingsChanged = True

    def _removeOutdatedQuickKeys(self):
        required = [
            'alt',
            'ctrl',
            'editExtract',
            'editSource',
            'extractBgColor',
            'extractDeck',
            'extractTextColor',
            'modelName',
            'regularKey',
            'shift',
            'tags',
            'textField',
        ]

        for keyCombo, settings in self.settings['quickKeys'].copy().items():
            for k in required:
                if k not in settings:
                    self.settings['quickKeys'].pop(keyCombo)
                    self.settingsChanged = True
                    break

    def saveSettings(self):
        with open(self.jsonPath, 'w', encoding='utf-8') as jsonFile:
            json.dump(self.settings, jsonFile)

        updateModificationTime(self.mediaDir)

    def loadMenuItems(self):
        menuName = 'Read::Quick Keys'

        if menuName in mw.customMenus:
            mw.customMenus[menuName].clear()

        for keyCombo, settings in self.settings['quickKeys'].items():
            menuText = 'Add Card [%s -> %s]' % (settings['modelName'],
                                                settings['extractDeck'])
            function = partial(mw.readingManager.textManager.extract, settings)
            addMenuItem(menuName, menuText, function, keyCombo)

        setMenuVisibility(menuName)

    def showDialog(self):
        dialog = QDialog(mw)

        zoomScrollLayout = QHBoxLayout()
        zoomScrollLayout.addWidget(self._getZoomGroupBox())
        zoomScrollLayout.addWidget(self._getScrollGroupBox())

        zoomScrollTab = QWidget()
        zoomScrollTab.setLayout(zoomScrollLayout)

        tabWidget = QTabWidget()
        tabWidget.setUsesScrollButtons(False)
        tabWidget.addTab(self._getGeneralTab(), 'General')
        tabWidget.addTab(self._getExtractionTab(), 'Extraction')
        tabWidget.addTab(self._getHighlightTab(), 'Highlighting')
        tabWidget.addTab(self._getSchedulingTab(), 'Scheduling')
        tabWidget.addTab(self._getImportingTab(), 'Importing')
        tabWidget.addTab(self._getQuickKeysTab(), 'Quick Keys')
        tabWidget.addTab(zoomScrollTab, 'Zoom / Scroll')

        buttonBox = QDialogButtonBox(QDialogButtonBox.Close |
                                     QDialogButtonBox.Save)
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)
        buttonBox.setOrientation(Qt.Horizontal)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(tabWidget)
        mainLayout.addWidget(buttonBox)

        dialog.setLayout(mainLayout)
        dialog.setWindowTitle('Incremental Reading Options')

        done = False
        while not done:
            if dialog.exec_():
                done = self._saveChanges()
            else:
                done = True

    def _saveChanges(self):
        self._saveHighlightSettings()
        done = self._saveKeys()

        self.settings['zoomStep'] = self.zoomStepSpinBox.value() / 100.0
        self.settings['generalZoom'] = self.generalZoomSpinBox.value() / 100.0
        self.settings['lineScrollFactor'] = self.lineStepSpinBox.value() / 100.0
        self.settings['pageScrollFactor'] = self.pageStepSpinBox.value() / 100.0
        self.settings['editExtract'] = self.editExtractButton.isChecked()
        self.settings['editSource'] = self.editSourceCheckBox.isChecked()
        self.settings['plainText'] = self.plainTextCheckBox.isChecked()
        self.settings['copyTitle'] = self.copyTitleCheckBox.isChecked()
        self.settings['scheduleExtract'] = (self
                                            .scheduleExtractCheckBox
                                            .isChecked())
        self.settings['soonRandom'] = self.soonRandomCheckBox.isChecked()
        self.settings['laterRandom'] = self.laterRandomCheckBox.isChecked()
        self.settings['extractRandom'] = self.extractRandomCheckBox.isChecked()

        if self.extractDeckComboBox.currentText() == '[Current Deck]':
            self.settings['extractDeck'] = None
        else:
            self.settings['extractDeck'] = (self
                                            .extractDeckComboBox
                                            .currentText())

        try:
            self.settings['soonValue'] = int(self.soonValueEditBox.text())
            self.settings['laterValue'] = int(self.laterValueEditBox.text())
            self.settings['extractValue'] = int(self.extractValueEditBox.text())
            self.settings['maxWidth'] = int(self.widthEditBox.text())
        except ValueError:
            showWarning('Integer value expected. Please try again.')
            done = False

        self.settings['sourceFormat'] = self.sourceFormatEditBox.text()

        if self.soonPercentButton.isChecked():
            self.settings['soonMethod'] = 'percent'
        else:
            self.settings['soonMethod'] = 'count'

        if self.laterPercentButton.isChecked():
            self.settings['laterMethod'] = 'percent'
        else:
            self.settings['laterMethod'] = 'count'

        if self.extractPercentButton.isChecked():
            self.settings['extractMethod'] = 'percent'
        else:
            self.settings['extractMethod'] = 'count'

        if self.limitAllCardsButton.isChecked():
            self.settings['limitWidth'] = True
            self.settings['limitWidthAll'] = True
        elif self.limitIrCardsButton.isChecked():
            self.settings['limitWidth'] = True
            self.settings['limitWidthAll'] = False
        else:
            self.settings['limitWidth'] = False
            self.settings['limitWidthAll'] = False

        mw.readingManager.viewManager.resetZoom(mw.state)
        return done

    def _getGeneralTab(self):
        highlightKeyLabel = QLabel('Highlight Key')
        extractKeyLabel = QLabel('Extract Key')
        removeKeyLabel = QLabel('Remove Key')
        undoKeyLabel = QLabel('Undo Key')

        self.extractKeyComboBox = QComboBox()
        self.highlightKeyComboBox = QComboBox()
        self.removeKeyComboBox = QComboBox()
        self.undoKeyComboBox = QComboBox()

        keys = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789')
        for comboBox in [self.highlightKeyComboBox,
                         self.extractKeyComboBox,
                         self.removeKeyComboBox,
                         self.undoKeyComboBox]:
            comboBox.addItems(keys)

        self._setCurrentKeys()

        highlightKeyLayout = QHBoxLayout()
        highlightKeyLayout.addWidget(highlightKeyLabel)
        highlightKeyLayout.addStretch()
        highlightKeyLayout.addWidget(self.highlightKeyComboBox)

        extractKeyLayout = QHBoxLayout()
        extractKeyLayout.addWidget(extractKeyLabel)
        extractKeyLayout.addStretch()
        extractKeyLayout.addWidget(self.extractKeyComboBox)

        removeKeyLayout = QHBoxLayout()
        removeKeyLayout.addWidget(removeKeyLabel)
        removeKeyLayout.addStretch()
        removeKeyLayout.addWidget(self.removeKeyComboBox)

        undoKeyLayout = QHBoxLayout()
        undoKeyLayout.addWidget(undoKeyLabel)
        undoKeyLayout.addStretch()
        undoKeyLayout.addWidget(self.undoKeyComboBox)

        controlsLayout = QVBoxLayout()
        controlsLayout.addLayout(highlightKeyLayout)
        controlsLayout.addLayout(extractKeyLayout)
        controlsLayout.addLayout(removeKeyLayout)
        controlsLayout.addLayout(undoKeyLayout)
        controlsLayout.addStretch()

        controlsGroupBox = QGroupBox('Basic Controls')
        controlsGroupBox.setLayout(controlsLayout)

        widthLabel = QLabel('Card Width Limit:')
        self.widthEditBox = QLineEdit()
        self.widthEditBox.setFixedWidth(50)
        self.widthEditBox.setText(str(self.settings['maxWidth']))
        pixelsLabel = QLabel('pixels')

        widthEditLayout = QHBoxLayout()
        widthEditLayout.addWidget(widthLabel)
        widthEditLayout.addWidget(self.widthEditBox)
        widthEditLayout.addWidget(pixelsLabel)

        applyLabel = QLabel('Apply to')
        self.limitAllCardsButton = QRadioButton('All Cards')
        self.limitIrCardsButton = QRadioButton('IR Cards')
        limitNoneButton = QRadioButton('None')

        if self.settings['limitWidth'] and self.settings['limitWidthAll']:
            self.limitAllCardsButton.setChecked(True)
        elif self.settings['limitWidth']:
            self.limitIrCardsButton.setChecked(True)
        else:
            limitNoneButton.setChecked(True)

        applyLayout = QHBoxLayout()
        applyLayout.addWidget(applyLabel)
        applyLayout.addWidget(self.limitAllCardsButton)
        applyLayout.addWidget(self.limitIrCardsButton)
        applyLayout.addWidget(limitNoneButton)

        displayLayout = QVBoxLayout()
        displayLayout.addLayout(widthEditLayout)
        displayLayout.addLayout(applyLayout)
        displayLayout.addStretch()

        displayGroupBox = QGroupBox('Display')
        displayGroupBox.setLayout(displayLayout)

        layout = QHBoxLayout()
        layout.addWidget(controlsGroupBox)
        layout.addWidget(displayGroupBox)

        tab = QWidget()
        tab.setLayout(layout)

        return tab

    def _setCurrentKeys(self):
        setComboBoxItem(self.highlightKeyComboBox,
                        self.settings['highlightKey'])
        setComboBoxItem(self.extractKeyComboBox, self.settings['extractKey'])
        setComboBoxItem(self.removeKeyComboBox, self.settings['removeKey'])
        setComboBoxItem(self.undoKeyComboBox, self.settings['undoKey'])

    def _saveKeys(self):
        keys = [self.highlightKeyComboBox.currentText(),
                self.extractKeyComboBox.currentText(),
                self.removeKeyComboBox.currentText(),
                self.undoKeyComboBox.currentText()]

        if len(set(keys)) < len(keys):
            showInfo('There is a conflict with the keys you have chosen.'
                     ' Please try again.')
            self._setCurrentKeys()
            return False
        else:
            self.settings['highlightKey'] = (self
                                             .highlightKeyComboBox
                                             .currentText()
                                             .lower())
            self.settings['extractKey'] = (self
                                           .extractKeyComboBox
                                           .currentText()
                                           .lower())
            self.settings['removeKey'] = (self
                                          .removeKeyComboBox
                                          .currentText()
                                          .lower())
            self.settings['undoKey'] = (self
                                        .undoKeyComboBox
                                        .currentText()
                                        .lower())
            return True

    def _getExtractionTab(self):
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
        self.copyTitleCheckBox = QCheckBox('Copy Title')
        self.scheduleExtractCheckBox = QCheckBox('Schedule Extracts')

        if self.settings['editSource']:
            self.editSourceCheckBox.setChecked(True)

        if self.settings['plainText']:
            self.plainTextCheckBox.setChecked(True)

        if self.settings['copyTitle']:
            self.copyTitleCheckBox.setChecked(True)

        if self.settings['scheduleExtract']:
            self.scheduleExtractCheckBox.setChecked(True)

        layout = QVBoxLayout()
        layout.addLayout(extractDeckLayout)
        layout.addLayout(radioButtonsLayout)
        layout.addWidget(self.editSourceCheckBox)
        layout.addWidget(self.plainTextCheckBox)
        layout.addWidget(self.copyTitleCheckBox)
        layout.addWidget(self.scheduleExtractCheckBox)
        layout.addStretch()

        tab = QWidget()
        tab.setLayout(layout)

        return tab

    def _getHighlightTab(self):
        colorsGroupBox = self._getColorsGroupBox()
        colorPreviewGroupBox = self._getColorPreviewGroupBox()

        horizontalLayout = QHBoxLayout()
        horizontalLayout.addWidget(colorsGroupBox)
        horizontalLayout.addWidget(colorPreviewGroupBox)

        layout = QVBoxLayout()
        layout.addWidget(self.targetComboBox)
        layout.addLayout(horizontalLayout)
        layout.addStretch()

        tab = QWidget()
        tab.setLayout(layout)

        return tab

    def _saveHighlightSettings(self):
        target = self.targetComboBox.currentText()
        bgColor = self.bgColorComboBox.currentText()
        textColor = self.textColorComboBox.currentText()

        if target == '[Highlight Key]':
            self.settings['highlightBgColor'] = bgColor
            self.settings['highlightTextColor'] = textColor
        elif target == '[Extract Key]':
            self.settings['extractBgColor'] = bgColor
            self.settings['extractTextColor'] = textColor
        else:
            self.settings['quickKeys'][target]['bgColor'] = bgColor
            self.settings['quickKeys'][target]['textColor'] = textColor

    def _getColorsGroupBox(self):
        self.targetComboBox = QComboBox()
        self._populateTargetComboBox()
        self.targetComboBox.currentIndexChanged.connect(
            self._updateHighlightTab)

        targetLayout = QHBoxLayout()
        targetLayout.addWidget(self.targetComboBox)
        targetLayout.addStretch()

        colors = self.getColorList()

        self.bgColorComboBox = QComboBox()
        self.bgColorComboBox.addItems(colors)
        setComboBoxItem(self.bgColorComboBox,
                        self.settings['highlightBgColor'])
        self.bgColorComboBox.currentIndexChanged.connect(
            self._updateColorPreview)

        self.textColorComboBox = QComboBox()
        self.textColorComboBox.addItems(colors)
        setComboBoxItem(self.textColorComboBox,
                        self.settings['highlightTextColor'])
        self.textColorComboBox.currentIndexChanged.connect(
            self._updateColorPreview)

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

    def _populateTargetComboBox(self):
        self.targetComboBox.clear()
        self.targetComboBox.addItem('[Highlight Key]')
        self.targetComboBox.addItem('[Extract Key]')
        self.targetComboBox.addItems(self.settings['quickKeys'].keys())

    def _updateHighlightTab(self):
        target = self.targetComboBox.currentText()

        if not target:
            return

        if target == '[Highlight Key]':
            setComboBoxItem(self.bgColorComboBox,
                            self.settings['highlightBgColor'])
            setComboBoxItem(self.textColorComboBox,
                            self.settings['highlightTextColor'])
        elif target == '[Extract Key]':
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
        colorsFilePath = os.path.join(moduleDir, 'data', 'colors.u8')
        with open(colorsFilePath, encoding='utf-8') as colorsFile:
            return [line.strip() for line in colorsFile]

    def _updateColorPreview(self):
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

    def _getColorPreviewGroupBox(self):
        self.colorPreviewLabel = QLabel('Example Text')
        self._updateColorPreview()
        colorPreviewLayout = QVBoxLayout()
        colorPreviewLayout.addWidget(self.colorPreviewLabel)

        groupBox = QGroupBox('Preview')
        groupBox.setLayout(colorPreviewLayout)

        return groupBox

    def _getSchedulingTab(self):
        soonLabel = QLabel('Soon Button')
        laterLabel = QLabel('Later Button')
        extractLabel = QLabel('Extracts')

        self.soonPercentButton = QRadioButton('Percent')
        soonPositionButton = QRadioButton('Position')
        self.laterPercentButton = QRadioButton('Percent')
        laterPositionButton = QRadioButton('Position')
        self.extractPercentButton = QRadioButton('Percent')
        extractPositionButton = QRadioButton('Position')

        self.soonRandomCheckBox = QCheckBox('Randomize')
        self.laterRandomCheckBox = QCheckBox('Randomize')
        self.extractRandomCheckBox = QCheckBox('Randomize')

        self.soonValueEditBox = QLineEdit()
        self.soonValueEditBox.setFixedWidth(100)
        self.laterValueEditBox = QLineEdit()
        self.laterValueEditBox.setFixedWidth(100)
        self.extractValueEditBox = QLineEdit()
        self.extractValueEditBox.setFixedWidth(100)

        if self.settings['soonMethod'] == 'percent':
            self.soonPercentButton.setChecked(True)
        else:
            soonPositionButton.setChecked(True)

        if self.settings['laterMethod'] == 'percent':
            self.laterPercentButton.setChecked(True)
        else:
            laterPositionButton.setChecked(True)

        if self.settings['extractMethod'] == 'percent':
            self.extractPercentButton.setChecked(True)
        else:
            extractPositionButton.setChecked(True)

        if self.settings['soonRandom']:
            self.soonRandomCheckBox.setChecked(True)

        if self.settings['laterRandom']:
            self.laterRandomCheckBox.setChecked(True)

        if self.settings['extractRandom']:
            self.extractRandomCheckBox.setChecked(True)

        self.soonValueEditBox.setText(str(self.settings['soonValue']))
        self.laterValueEditBox.setText(str(self.settings['laterValue']))
        self.extractValueEditBox.setText(str(self.settings['extractValue']))

        soonLayout = QHBoxLayout()
        soonLayout.addWidget(soonLabel)
        soonLayout.addStretch()
        soonLayout.addWidget(self.soonValueEditBox)
        soonLayout.addWidget(self.soonPercentButton)
        soonLayout.addWidget(soonPositionButton)
        soonLayout.addWidget(self.soonRandomCheckBox)

        laterLayout = QHBoxLayout()
        laterLayout.addWidget(laterLabel)
        laterLayout.addStretch()
        laterLayout.addWidget(self.laterValueEditBox)
        laterLayout.addWidget(self.laterPercentButton)
        laterLayout.addWidget(laterPositionButton)
        laterLayout.addWidget(self.laterRandomCheckBox)

        extractLayout = QHBoxLayout()
        extractLayout.addWidget(extractLabel)
        extractLayout.addStretch()
        extractLayout.addWidget(self.extractValueEditBox)
        extractLayout.addWidget(self.extractPercentButton)
        extractLayout.addWidget(extractPositionButton)
        extractLayout.addWidget(self.extractRandomCheckBox)

        soonButtonGroup = QButtonGroup(soonLayout)
        soonButtonGroup.addButton(self.soonPercentButton)
        soonButtonGroup.addButton(soonPositionButton)

        laterButtonGroup = QButtonGroup(laterLayout)
        laterButtonGroup.addButton(self.laterPercentButton)
        laterButtonGroup.addButton(laterPositionButton)

        extractButtonGroup = QButtonGroup(extractLayout)
        extractButtonGroup.addButton(self.extractPercentButton)
        extractButtonGroup.addButton(extractPositionButton)

        layout = QVBoxLayout()
        layout.addLayout(soonLayout)
        layout.addLayout(laterLayout)
        layout.addLayout(extractLayout)
        layout.addStretch()

        tab = QWidget()
        tab.setLayout(layout)

        return tab

    def _getQuickKeysTab(self):
        destDeckLabel = QLabel('Destination Deck')
        noteTypeLabel = QLabel('Note Type')
        textFieldLabel = QLabel('Paste Text to Field')
        keyComboLabel = QLabel('Key Combination')

        self.quickKeysComboBox = QComboBox()
        self.quickKeysComboBox.addItem('')
        self.quickKeysComboBox.addItems(self.settings['quickKeys'].keys())
        self.quickKeysComboBox.currentIndexChanged.connect(
            self._updateQuickKeysTab)

        self.destDeckComboBox = QComboBox()
        self.noteTypeComboBox = QComboBox()
        self.textFieldComboBox = QComboBox()
        self.quickKeyEditExtractCheckBox = QCheckBox('Edit Extracted Note')
        self.quickKeyEditSourceCheckBox = QCheckBox('Edit Source Note')
        self.quickKeyPlainTextCheckBox = QCheckBox('Extract as Plain Text')

        self.ctrlKeyCheckBox = QCheckBox('Ctrl')
        self.altKeyCheckBox = QCheckBox('Alt')
        self.shiftKeyCheckBox = QCheckBox('Shift')
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
        keyComboLayout.addWidget(self.altKeyCheckBox)
        keyComboLayout.addWidget(self.shiftKeyCheckBox)
        keyComboLayout.addWidget(self.regularKeyComboBox)

        deckNames = sorted([d['name'] for d in mw.col.decks.all()])
        self.destDeckComboBox.addItem('')
        self.destDeckComboBox.addItems(deckNames)

        modelNames = sorted([m['name'] for m in mw.col.models.all()])
        self.noteTypeComboBox.addItem('')
        self.noteTypeComboBox.addItems(modelNames)
        self.noteTypeComboBox.currentIndexChanged.connect(self._updateFieldList)

        newButton = QPushButton('New')
        newButton.clicked.connect(self._clearQuickKeysTab)
        setButton = QPushButton('Set')
        setButton.clicked.connect(self._setQuickKey)
        unsetButton = QPushButton('Unset')
        unsetButton.clicked.connect(self._unsetQuickKey)

        tagsLabel = QLabel('Tags')
        self.tagsEditBox = TagEdit(mw)
        self.tagsEditBox.setCol(mw.col)
        tagsLayout = QHBoxLayout()
        tagsLayout.addWidget(tagsLabel)
        tagsLayout.addWidget(self.tagsEditBox)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(newButton)
        buttonLayout.addWidget(setButton)
        buttonLayout.addWidget(unsetButton)

        layout = QVBoxLayout()
        layout.addWidget(self.quickKeysComboBox)
        layout.addLayout(destDeckLayout)
        layout.addLayout(noteTypeLayout)
        layout.addLayout(textFieldLayout)
        layout.addLayout(keyComboLayout)
        layout.addWidget(self.quickKeyEditExtractCheckBox)
        layout.addWidget(self.quickKeyEditSourceCheckBox)
        layout.addWidget(self.quickKeyPlainTextCheckBox)
        layout.addLayout(tagsLayout)
        layout.addLayout(buttonLayout)

        tab = QWidget()
        tab.setLayout(layout)

        return tab

    def _updateQuickKeysTab(self):
        keyCombo = self.quickKeysComboBox.currentText()
        if keyCombo:
            settings = self.settings['quickKeys'][keyCombo]
            setComboBoxItem(self.destDeckComboBox, settings['extractDeck'])
            setComboBoxItem(self.noteTypeComboBox, settings['modelName'])
            setComboBoxItem(self.textFieldComboBox, settings['textField'])
            self.ctrlKeyCheckBox.setChecked(settings['ctrl'])
            self.altKeyCheckBox.setChecked(settings['alt'])
            self.shiftKeyCheckBox.setChecked(settings['shift'])
            setComboBoxItem(self.regularKeyComboBox, settings['regularKey'])
            self.quickKeyEditExtractCheckBox.setChecked(settings['editExtract'])
            self.quickKeyEditSourceCheckBox.setChecked(settings['editSource'])
            self.quickKeyPlainTextCheckBox.setChecked(settings['plainText'])
            self.tagsEditBox.setText(mw.col.tags.join(settings['tags']))
        else:
            self._clearQuickKeysTab()

    def _updateFieldList(self):
        modelName = self.noteTypeComboBox.currentText()
        self.textFieldComboBox.clear()
        if modelName:
            model = mw.col.models.byName(modelName)
            fieldNames = [f['name'] for f in model['flds']]
            self.textFieldComboBox.addItems(fieldNames)

    def _clearQuickKeysTab(self):
        self.quickKeysComboBox.setCurrentIndex(0)
        self.destDeckComboBox.setCurrentIndex(0)
        self.noteTypeComboBox.setCurrentIndex(0)
        self.textFieldComboBox.setCurrentIndex(0)
        self.ctrlKeyCheckBox.setChecked(False)
        self.altKeyCheckBox.setChecked(False)
        self.shiftKeyCheckBox.setChecked(False)
        self.regularKeyComboBox.setCurrentIndex(0)
        self.quickKeyEditExtractCheckBox.setChecked(False)
        self.quickKeyEditSourceCheckBox.setChecked(False)
        self.quickKeyPlainTextCheckBox.setChecked(False)
        self.tagsEditBox.clear()

    def _unsetQuickKey(self):
        keyCombo = self.quickKeysComboBox.currentText()
        if keyCombo:
            self.settings['quickKeys'].pop(keyCombo)
            removeComboBoxItem(self.quickKeysComboBox, keyCombo)
            self._clearQuickKeysTab()
            self._populateTargetComboBox()
            self.loadMenuItems()

    def _setQuickKey(self):
        tags = mw.col.tags.canonify(
            mw.col.tags.split(normalize('NFC', self.tagsEditBox.text())))

        settings = {
            'alt': self.altKeyCheckBox.isChecked(),
            'ctrl': self.ctrlKeyCheckBox.isChecked(),
            'editExtract': self.quickKeyEditExtractCheckBox.isChecked(),
            'editSource': self.quickKeyEditSourceCheckBox.isChecked(),
            'extractBgColor': self.bgColorComboBox.currentText(),
            'extractDeck': self.destDeckComboBox.currentText(),
            'extractTextColor': self.textColorComboBox.currentText(),
            'modelName': self.noteTypeComboBox.currentText(),
            'plainText': self.quickKeyPlainTextCheckBox.isChecked(),
            'regularKey': self.regularKeyComboBox.currentText(),
            'shift': self.shiftKeyCheckBox.isChecked(),
            'tags': tags,
            'textField': self.textFieldComboBox.currentText(),
        }

        for k in ['extractDeck', 'modelName', 'regularKey']:
            if not settings[k]:
                showInfo('Please complete all settings. Destination deck,'
                         ' note type, and a letter or number for the key'
                         ' combination are required.')
                return

        keyCombo = ''
        if settings['ctrl']:
            keyCombo += 'Ctrl+'
        if settings['alt']:
            keyCombo += 'Alt+'
        if settings['shift']:
            keyCombo += 'Shift+'
        keyCombo += settings['regularKey']

        if keyCombo in self.settings['quickKeys']:
            tooltip('Shortcut updated')
        else:
            tooltip('New shortcut added: %s' % keyCombo)

        self.settings['quickKeys'][keyCombo] = settings
        self.quickKeysComboBox.addItem(keyCombo)
        setComboBoxItem(self.quickKeysComboBox, keyCombo)
        self._populateTargetComboBox()
        self.loadMenuItems()

    def _getZoomGroupBox(self):
        zoomStepLabel = QLabel('Zoom Step')
        zoomStepPercentLabel = QLabel('%')
        generalZoomLabel = QLabel('General Zoom')
        generalZoomPercentLabel = QLabel('%')

        zoomStepPercent = round(self.settings['zoomStep'] * 100)
        generalZoomPercent = round(self.settings['generalZoom'] * 100)
        self.zoomStepSpinBox = createSpinBox(zoomStepPercent, 5, 100, 5)
        self.generalZoomSpinBox = createSpinBox(generalZoomPercent, 10, 200, 10)

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

    def _getScrollGroupBox(self):
        lineStepLabel = QLabel('Line Step')
        lineStepPercentLabel = QLabel('%')
        pageStepLabel = QLabel('Page Step')
        pageStepPercentLabel = QLabel('%')

        lineStepPercent = round(self.settings['lineScrollFactor'] * 100)
        pageStepPercent = round(self.settings['pageScrollFactor'] * 100)
        self.lineStepSpinBox = createSpinBox(lineStepPercent, 5, 100, 5)
        self.pageStepSpinBox = createSpinBox(pageStepPercent, 5, 100, 5)

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

    def _getImportingTab(self):
        sourceFormatLabel = QLabel('Source Format')

        self.sourceFormatEditBox = QLineEdit()
        self.sourceFormatEditBox.setFixedWidth(200)
        self.sourceFormatEditBox.setText(str(self.settings['sourceFormat']))
        font = QFont('Lucida Sans Typewriter')
        font.setStyleHint(QFont.Monospace)
        self.sourceFormatEditBox.setFont(font)

        sourceFormatLayout = QHBoxLayout()
        sourceFormatLayout.addWidget(sourceFormatLabel)
        sourceFormatLayout.addWidget(self.sourceFormatEditBox)
        sourceFormatLayout.addStretch()

        layout = QVBoxLayout()
        layout.addLayout(sourceFormatLayout)
        layout.addStretch()

        tab = QWidget()
        tab.setLayout(layout)

        return tab
