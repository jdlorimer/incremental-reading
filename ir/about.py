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

from aqt import mw
from aqt.qt import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from ._version import __version__

IR_GITHUB_URL = "https://github.com/tvhong/incremental-reading"


def showAbout():
    dialog = QDialog(mw)

    label = QLabel()
    label.setStyleSheet("QLabel { font-size: 14px; }")
    contributors = [
        "Joseph Lorimer <joseph@lorimer.me>" "Timothée Chauvin",
        "Christian Weiß",
        "Aleksej",
        "Frank Kmiec",
        "Tiago Barroso",
    ]
    text = f"""
<div style="font-weight: bold">Incremental Reading v{__version__}</div>
<div>Vy Hong &lt;contact@vyhong.me&gt;</div>
<div>Contributors: {", ".join(contributors)}</div>
<div>Website: <a href="{IR_GITHUB_URL}">{IR_GITHUB_URL}</a></div>
"""
    label.setText(text)

    buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
    buttonBox.accepted.connect(dialog.accept)

    layout = QVBoxLayout()
    layout.addWidget(label)
    layout.addWidget(buttonBox)

    dialog.setLayout(layout)
    dialog.setWindowTitle("About")
    dialog.exec()
