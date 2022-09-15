/*
 * Copyright 2017 Joseph Lorimer <joseph@lorimer.me>
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

function restoreScroll() {{
    window.scrollTo(0, {savedPos});
}}

function getMovementFactor(keyCode) {{
    switch (keyCode) {{
        case "ArrowUp":
            return -{lineScrollFactor};
        case "ArrowDown":
            return {lineScrollFactor};
        case "PageUp":
            return -{pageScrollFactor};
        case "PageDown":
            return {pageScrollFactor};
        default:
            return 0;
    }}
}}

document.addEventListener("keydown", (e) => {{
    if (["ArrowUp", "ArrowDown", "PageUp", "PageDown"].includes(e.code)) {{
        let currentPos = window.pageYOffset;

        let movementSize = window.innerHeight * getMovementFactor(e.code);
        let newPos = currentPos + movementSize;
        newPos = Math.max(newPos, 0);
        newPos = Math.min(newPos, document.body.scrollHeight);

        window.scrollTo(0, newPos);

        e.preventDefault();
    }}
}});

onUpdateHook.push(restoreScroll);
