from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from aqt import mw

from ._version import __version__

IR_GITHUB_URL = 'https://github.com/luoliyan/incremental-reading'


def showAbout():
    dialog = QDialog(mw)

    label = QLabel()
    label.setStyleSheet('QLabel { font-size: 14px; }')
    text = '''
<div style="font-weight: bold">Incremental Reading v%s</div>
<div>Maintainer: Luo Li-Yan</div>
<div>Contributors: Tiago Barroso, Frank Kmiec, Aleksej</div>
<div>Website: <a href="%s">%s</a></div>
''' % (__version__, IR_GITHUB_URL, IR_GITHUB_URL)
    label.setText(text)

    buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
    buttonBox.accepted.connect(dialog.accept)

    layout = QVBoxLayout()
    layout.addWidget(label)
    layout.addWidget(buttonBox)

    dialog.setLayout(layout)
    dialog.setWindowTitle('About')
    dialog.exec_()
