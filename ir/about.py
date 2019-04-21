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

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from aqt import mw

from ._version import __version__

IR_GITHUB_URL = 'https://github.com/luoliyan/incremental-reading'


def showAbout():
    dialog = QDialog(mw)

    label = QLabel()
    label.setStyleSheet('QLabel { font-size: 14px; }')
    names = [
        'Tiago Barroso',
        'Frank Kmiec',
        'Aleksej',
        'Christian Weiß',
        'Timothée Chauvin',
    ]
    text = '''
<div style="font-weight: bold">Incremental Reading v%s</div>
<div>Joseph Lorimer &lt;joseph@lorimer.me&gt;</div>
<div>Contributors: %s</div>
<div>Website: <a href="%s">%s</a></div>
''' % (
        __version__,
        ', '.join(names),
        IR_GITHUB_URL,
        IR_GITHUB_URL,
    )
    label.setText(text)

    buttonBox = QDialogButtonBox(QDialogButtonBox.Ok)
    buttonBox.accepted.connect(dialog.accept)

    layout = QVBoxLayout()
    layout.addWidget(label)
    layout.addWidget(buttonBox)

    dialog.setLayout(layout)
    dialog.setWindowTitle('About')
    dialog.exec_()
