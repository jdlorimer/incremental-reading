from PyQt4.QtGui import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from aqt import mw

from ir._version import __version__


def showAbout():
    dialog = QDialog(mw)

    label = QLabel()
    text = '''
<div style="font-weight: bold; font-size: 16px">Incremental Reading v%s</div>
<div style="font-size: 14px">Maintainer: Luo Li-Yan</div>
<div style="font-size: 14px">
Contributors: Tiago Barroso, Frank Kmiec, Aleksej
</div>''' % __version__
    label.setText(text)

    buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
    buttonBox.accepted.connect(dialog.accept)

    layout = QVBoxLayout()
    layout.addWidget(label)
    layout.addWidget(buttonBox)

    dialog.setLayout(layout)
    dialog.setWindowTitle('About')
    dialog.exec_()
