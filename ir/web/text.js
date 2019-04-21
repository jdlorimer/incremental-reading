/*
 * Copyright 2013 Tiago Barroso
 * Copyright 2013 Frank Kmiec
 * Copyright 2017-2018 Joseph Lorimer <joseph@lorimer.me>
 *
 * Permission to use, copy, modify, and distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
 * SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION
 * OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN
 * CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 */

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


function format(style) {
    var selection = window.getSelection().getRangeAt(0);
    var selectedText = selection.extractContents();
    var span = document.createElement("span");

    span.className = "ir-highlight " + style;
    span.setAttribute("ir-overlay", "on");
    span.appendChild(selectedText);

    selection.insertNode(span);
}


function toggleOverlay() {
    var elems = document.getElementsByClassName("ir-highlight");
    for (var i = 0; i < elems.length; i++) {
        if (elems[i].getAttribute("ir-overlay") == "off") {
            elems[i].setAttribute("ir-overlay", "on")
        } else {
            elems[i].setAttribute("ir-overlay", "off")
        }
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
