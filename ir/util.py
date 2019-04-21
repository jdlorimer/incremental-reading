# Copyright 2017-2019 Joseph Lorimer <joseph@lorimer.me>
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

import os
import stat
import time
from urllib.parse import unquote

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction, QMenu, QSpinBox
from aqt import dialogs, mw
from bs4 import BeautifulSoup


def isIrCard(card):
    return card and (
        card.model()['name'] == mw.readingManager.settings['modelName']
    )


def viewingIrText():
    return (
        isIrCard(mw.reviewer.card)
        and (mw.reviewer.state == 'question')
        and (mw.state == 'review')
    )


def addMenu(fullPath):
    if not hasattr(mw, 'customMenus'):
        mw.customMenus = {}

    if len(fullPath.split('::')) == 2:
        menuPath, submenuPath = fullPath.split('::')
        hasSubmenu = True
    else:
        menuPath = fullPath
        hasSubmenu = False

    if menuPath not in mw.customMenus:
        menu = QMenu('&' + menuPath, mw)
        mw.customMenus[menuPath] = menu
        mw.form.menubar.insertMenu(mw.form.menuTools.menuAction(), menu)

    if hasSubmenu and (fullPath not in mw.customMenus):
        submenu = QMenu('&' + submenuPath, mw)
        mw.customMenus[fullPath] = submenu
        mw.customMenus[menuPath].addMenu(submenu)


def setMenuVisibility(path):
    if path not in mw.customMenus:
        return

    if mw.customMenus[path].isEmpty():
        mw.customMenus[path].menuAction().setVisible(False)
    else:
        mw.customMenus[path].menuAction().setVisible(True)


def addMenuItem(path, text, function, keys=None):
    action = QAction(text, mw)

    if keys:
        action.setShortcut(QKeySequence(keys))

    action.triggered.connect(function)

    if path == 'File':
        mw.form.menuCol.addAction(action)
    elif path == 'Edit':
        mw.form.menuEdit.addAction(action)
    elif path == 'Tools':
        mw.form.menuTools.addAction(action)
    elif path == 'Help':
        mw.form.menuHelp.addAction(action)
    else:
        addMenu(path)
        mw.customMenus[path].addAction(action)


def getField(note, fieldName):
    model = note.model()
    index, _ = mw.col.models.fieldMap(model)[fieldName]
    return note.fields[index]


def setField(note, field, value):
    """Set the value of a note field. Overwrite any existing value."""
    model = note.model()
    index, _ = mw.col.models.fieldMap(model)[field]
    note.fields[index] = value


def getFieldNames(modelName):
    """Return list of field names for given model name."""
    if not modelName:
        return []
    return mw.col.models.fieldNames(mw.col.models.byName(modelName))


def createSpinBox(value, minimum, maximum, step):
    spinBox = QSpinBox()
    spinBox.setRange(minimum, maximum)
    spinBox.setSingleStep(step)
    spinBox.setValue(value)
    return spinBox


def setComboBoxItem(comboBox, text):
    index = comboBox.findText(text, Qt.MatchFixedString)
    comboBox.setCurrentIndex(index)


def removeComboBoxItem(comboBox, text):
    index = comboBox.findText(text, Qt.MatchFixedString)
    comboBox.removeItem(index)


def updateModificationTime(path):
    accessTime = os.stat(path)[stat.ST_ATIME]
    modificationTime = time.time()
    os.utime(path, (accessTime, modificationTime))


def fixImages(html):
    if not html:
        return ''
    soup = BeautifulSoup(html, 'html.parser')
    for img in soup.find_all('img'):
        img['src'] = os.path.basename(unquote(img['src']))
    return str(soup)


def loadFile(fileDir, filename):
    moduleDir, _ = os.path.split(__file__)
    path = os.path.join(moduleDir, fileDir, filename)
    with open(path, encoding='utf-8') as f:
        return f.read()


def getColorList():
    moduleDir, _ = os.path.split(__file__)
    colorsFilePath = os.path.join(moduleDir, 'data', 'colors.u8')
    with open(colorsFilePath, encoding='utf-8') as colorsFile:
        return [line.strip() for line in colorsFile]


def showBrowser(nid):
    browser = dialogs.open('Browser', mw)
    browser.form.searchEdit.lineEdit().setText('nid:' + str(nid))
    browser.onSearchActivated()
