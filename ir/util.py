# Copyright 2017-2018 Joseph Lorimer <luoliyan@posteo.net>
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

from urllib.parse import unquote
import os
import stat
import time

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction, QMenu, QSpinBox

from aqt import mw

from bs4 import BeautifulSoup


def isIrCard(card):
    if (card and (card.model()['name'] ==
                  mw.readingManager.settings['modelName'])):
        return True
    else:
        return False


def viewingIrText():
    if (isIrCard(mw.reviewer.card) and
            (mw.reviewer.state == 'question') and
            (mw.state == 'review')):
        return True
    else:
        return False


def addMenu(fullName):
    if not hasattr(mw, 'customMenus'):
        mw.customMenus = {}

    if len(fullName.split('::')) == 2:
        menuName, submenuName = fullName.split('::')
        hasSubmenu = True
    else:
        menuName = fullName
        hasSubmenu = False

    if menuName not in mw.customMenus:
        menu = QMenu('&' + menuName, mw)
        mw.customMenus[menuName] = menu
        mw.form.menubar.insertMenu(mw.form.menuTools.menuAction(), menu)

    if hasSubmenu and (fullName not in mw.customMenus):
        submenu = QMenu('&' + submenuName, mw)
        mw.customMenus[fullName] = submenu
        mw.customMenus[menuName].addMenu(submenu)


def setMenuVisibility(menuName):
    if menuName not in mw.customMenus:
        return

    if mw.customMenus[menuName].isEmpty():
        mw.customMenus[menuName].menuAction().setVisible(False)
    else:
        mw.customMenus[menuName].menuAction().setVisible(True)


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


def getField(note, fieldName):
    model = note.model()
    index, _ = mw.col.models.fieldMap(model)[fieldName]
    return note.fields[index]


def setField(note, fieldName, content):
    """Sets the content of a note field. Overwrites any existing content."""
    model = note.model()
    index, _ = mw.col.models.fieldMap(model)[fieldName]
    note.fields[index] = content


def getFieldNames(modelName):
    """Returns list of field names for given model name."""
    if not modelName:
        return []

    model = mw.col.models.byName(modelName)
    return [f['name'] for f in model['flds']]


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
