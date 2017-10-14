function highlight(bgColor, textColor) {
    if (window.getSelection) {
        var range, sel = window.getSelection();

        if (sel.rangeCount && sel.getRangeAt) {
            range = sel.getRangeAt(0);
        }

        document.designMode = "on";
        if (range) {
            sel.removeAllRanges();
            sel.addRange(range);
        }

        document.execCommand("foreColor", false, textColor);
        document.execCommand("hiliteColor", false, bgColor);

        document.designMode = "off";
        sel.removeAllRanges();
    }
}

function removeText() {
    var range, sel = window.getSelection();
    if (sel.rangeCount && sel.getRangeAt) {
        range = sel.getRangeAt(0);
        var startNode = document.createElement('span');
        range.insertNode(startNode);
        var endNode = document.createElement('span');
        range.collapse(false);
        range.insertNode(endNode);
        range.setStartAfter(startNode);
        range.setEndBefore(endNode);
        sel.addRange(range);
        range.deleteContents();
    }
}

function getPlainText() {
    return window.getSelection().toString();
}

function getHtmlText() {
    var selection = window.getSelection();
    var range = selection.getRangeAt(0);
    var div = document.createElement('div');
    div.appendChild(range.cloneContents());
    return div.innerHTML;
}
