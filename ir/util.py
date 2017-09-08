import os
import stat
import time

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (QAction, QDialog, QDialogButtonBox, QHBoxLayout,
                             QLabel, QLineEdit, QMenu, QShortcut)

from aqt import mw
from aqt.utils import showInfo


def isIrCard(card):
    if (card and card.model()['name'] ==
            mw.settingsManager.settings['modelName']):
        return True
    else:
        return False


def viewingIrText():
    if (isIrCard() and
            mw.reviewer.state == 'question' and
            mw.state == 'review'):
        return True
    else:
        return False


def addMenu(name):
    if not hasattr(mw, 'customMenus'):
        mw.customMenus = {}

    if name not in mw.customMenus:
        menu = QMenu('&' + name, mw)
        mw.customMenus[name] = menu
        mw.form.menubar.insertMenu(mw.form.menuTools.menuAction(),
                                   mw.customMenus[name])


def addMenuItem(menuName, text, function, keys=None):
    action = QAction(text, mw)

    if keys:
        action.setShortcut(QKeySequence(keys))

    action.triggered.connect(function)

    if menuName == 'File':
        mw.form.menuCol.addAction(action)
    elif menuName == 'Edit':
        mw.form.menuEdit.addAction(action)
    elif menuName == 'Tools':
        mw.form.menuTools.addAction(action)
    elif menuName == 'Help':
        mw.form.menuHelp.addAction(action)
    else:
        addMenu(menuName)
        mw.customMenus[menuName].addAction(action)

    return action


def addShortcut(function, keys):
    shortcut = QShortcut(QKeySequence(keys), mw)
    shortcut.activated.connect(function)


def getField(note, fieldName):
    model = note.model()
    index, _ = mw.col.models.fieldMap(model)[fieldName]
    return note.fields[index]


def setField(note, fieldName, content):
    model = note.model()
    index, _ = mw.col.models.fieldMap(model)[fieldName]
    note.fields[index] = content


def setComboBoxItem(comboBox, text):
    index = comboBox.findText(text, Qt.MatchFixedString)
    comboBox.setCurrentIndex(index)


def removeComboBoxItem(comboBox, text):
    index = comboBox.findText(text, Qt.MatchFixedString)
    comboBox.removeItem(index)


def disableOutdated():
    outdated = ['Incremental_Reading_Extension.py', 'View_Size_Adjust.py']
    disabled = False
    for filename in outdated:
        path = os.path.join(mw.pm.addonFolder(), filename)
        if os.path.isfile(path):
            os.rename(path, path + '.old')
            disabled = True
    if disabled:
        showInfo('One or more outdated add-on files have been deactivated.'
                 ' Please restart Anki.')


def updateModificationTime(path):
    accessTime = os.stat(path)[stat.ST_ATIME]
    modificationTime = time.time()
    os.utime(path, (accessTime, modificationTime))


def getInput(windowTitle, labelText):
    dialog = QDialog(mw)
    dialog.setWindowTitle(windowTitle)
    label = QLabel(labelText)
    editBox = QLineEdit()
    editBox.setFixedWidth(300)
    buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
    buttonBox.accepted.connect(dialog.accept)
    layout = QHBoxLayout()
    layout.addWidget(label)
    layout.addWidget(editBox)
    layout.addWidget(buttonBox)
    dialog.setLayout(layout)
    dialog.exec_()
    return editBox.text()
