#!/usr/bin/env python3

from re import sub

from markdown2 import markdown


def main():
    """Covert GitHub mardown to AnkiWeb HTML."""
    # permitted tags: img, a, b, i, code, ul, ol, li

    translate = [
        (r'<h1>([^<]+)</h1>', r''),
        (r'<h2>([^<]+)</h2>', r'<b><i>\1</i></b>\n\n'),
        (r'<h3>([^<]+)</h3>', r'<b>\1</b>\n\n'),
        (r'<strong>([^<]+)</strong>', r'<b>\1</b>'),
        (r'<em>([^<]+)</em>', r'<i>\1</i>'),
        (r'<kbd>([^<]+)</kbd>', r'<code><b>\1</b></code>'),
        (r'</a></p>', r'</a></p>\n'),
        (r'<p>', r''),
        (r'</p>', r'\n\n'),
        (r'</(ol|ul)>(?!</(li|[ou]l)>)', r'</\1>\n'),
    ]

    with open('README.md', encoding='utf-8') as f:
        html = ''.join(filter(None, markdown(f.read()).split('\n')))

    for a, b in translate:
        html = sub(a, b, html)

    with open('README.html', 'w', encoding='utf-8') as f:
        f.write(html.strip())


if __name__ == '__main__':
    main()
