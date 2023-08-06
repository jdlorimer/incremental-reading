# Copyright 2023 DarkSun <lujun9972@gmail.com>
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

from urllib.parse import urlencode, urlsplit

from anki.utils import is_mac, is_win
from aqt.utils import askUser, openLink, showCritical, showInfo

from requests import post

import os
import re
import xml.etree.ElementTree as ET
import zipfile
import tempfile

def nov_container_content_filename(filename):
    """Return the content filename for CONTENT."""
    query = "{*}rootfiles/{*}rootfile[@media-type='application/oebps-package+xml']"
    doc = ET.parse(filename)
    root = doc.getroot()
    node = root.find(query)
    if node is not None:
        return node.get('full-path')
    return "OEBPS/Content.opf"

def nov_content_version(root):
    """Return the EPUB version for ROOT."""
    version = root.get('version') if root is not None else None
    if not version:
        raise ValueError("Version not specified")
    return float(version)

def nov_content_manifest(directory, root):
    """Extract an alist of manifest files for CONTENT in DIRECTORY.
    Each alist item consists of the identifier and full path."""
    query = "{*}manifest/{*}item"
    nodes = root.findall(query)
    return {node.get('id'):os.path.join(directory, node.get('href')) for node in nodes}

def nov_content_spine(root):
    """Extract a list of spine identifiers for CONTENT."""
    query = "{*}spine/{*}itemref"
    nodes = root.findall(query)
    return [node.get('idref') for node in nodes]

def nov_content_epub2_toc_file(root, manifest):
    """Return toc file for EPUB 2."""
    node = root.find("{*}spine[@toc]")
    if node is None:
        raise ValueError("EPUB 2 NCX ID not found")

    toc_id = node.get('toc')
    if toc_id is None:
        raise ValueError("EPUB 2 NCX ID not found")

    toc_file = manifest.get(toc_id)

    if toc_file is None:
        raise ValueError("EPUB 2 NCX file not found")

    return toc_file


def nov_content_epub3_toc_file(root, manifest):
    """Return toc file for EPUB 3."""
    node = root.find("{*}manifest/{*}item[@properties~=nav]")
    if node is None:
        raise ValueError("EPUB 3 <nav> ID not found")

    toc_id = node.get('id')
    if toc_id is None:
        raise ValueError("EPUB 3 <nav> ID not found")

    toc_file = manifest.get(toc_id)

    if toc_file is None:
        raise ValueError("EPUB 3 <nav> file not found")

    return toc_file
def nov_content_epub2_files(root, manifest, files):
    """Return updated files list for EPUB 2."""
    node = root.find("{*}spine[@toc]")
    if node is None:
        raise ValueError("EPUB 2 NCX ID not found")

    toc_id = node.get('toc')
    if toc_id is None:
        raise ValueError("EPUB 2 NCX ID not found")

    toc_file = manifest.get(toc_id)

    if toc_file is None:
        raise ValueError("EPUB 2 NCX file not found")

    files[toc_id] = toc_file
    return files


def nov_content_epub3_files(root, manifest, files):
    """Return updated files list for EPUB 3."""
    node = root.find("{*}manifest/{*}item[@properties~=nav]")
    if node is None:
        raise ValueError("EPUB 3 <nav> ID not found")

    toc_id = node.get('id')
    if toc_id is None:
        raise ValueError("EPUB 3 <nav> ID not found")

    toc_file = manifest.get(toc_id)

    if toc_file is None:
        raise ValueError("EPUB 3 <nav> file not found")

    files[toc_id] = toc_file
    return files

def nov_content_toc_file(content_dir, root):
    "Return toc file from content ROOT"
    manifest = nov_content_manifest(content_dir,root)
    spine = nov_content_spine(root)
    files = {item:manifest[item] for item in spine}
    version = nov_content_version(root)
    if version < 3.0:
        toc_filename = nov_content_epub2_toc_file(root, manifest)
    else:
        toc_filename = nov_content_epub3_toc_file(root, manifest)
    return toc_filename

def nov_toc_files(content_dir, root):
    query = '{*}navMap//{*}navPoint'
    nav_points = root.findall(query)
    files = []
    for point in nav_points:
        text_node = point.find('{*}navLabel/{*}text')
        content_node = point.find('{*}content')
        text = text_node.text
        href = os.path.join(content_dir, content_node.get('src'))
        scheme, netloc, path, *_ = urlsplit(href)
        data = {"text": text, "href": path}
        files.append({'text':text, "data": data})
    return files


def get_extract_dir(filename):
    'get extract directory by epub filename.'
    tempdir = tempfile.gettempdir()
    basename = os.path.basename(filename)
    nonextension = os.path.splitext(basename)[0]
    return os.path.join(tempdir, nonextension)

def unzip_epub(file_path):
    extract_dir = get_extract_dir(file_path)
    if not os.path.exists(extract_dir):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    return extract_dir



def get_epub_toc(epub_file_path):
    extract_dir = unzip_epub(epub_file_path)
    container_filename = os.path.join(extract_dir,"META-INF","container.xml")
    content_filename = nov_container_content_filename(container_filename)
    content_filename = os.path.join(extract_dir, content_filename)
    content_dir = os.path.dirname(content_filename)
    content_doc = ET.parse(content_filename)
    content_root = content_doc.getroot()
    toc_filename = nov_content_toc_file(content_dir, content_root)
    toc_file = os.path.join(content_dir, toc_filename)
    toc_doc = ET.parse(toc_file)
    toc_root = toc_doc.getroot()
    return nov_toc_files(content_dir, toc_root)
