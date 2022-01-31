import re
import os
import operator
from functools import partial

from PySide6.QtCore import Slot, QUrl, Signal
from PySide6.QtGui import QImage, Qt, QTextDocument, QTextCursor, QMovie
from PySide6.QtWidgets import QTextBrowser

from library.config import peakLoad

URL_REGEX = re.compile(r'\(\.(\/.+)\)')

DESCRIPTION_STYLE = """
<style type="text/css">
table {
    border-color: rgb(64,64,64);
    border-collapse: collapse;
}
h3 {
    text-align: center;
    margin-top: 64px;
    margin-bottom: 64px;
    color: rgb(200, 200, 200);
}
h2 {
    color: rgb(128, 150, 200);
}
h1 {
    color: rgb(230, 230, 230);
}
td {
  padding: 6px;
  text-align: center;
  border: 2px solid rgb(64,64,64);
  margin-top: 26px;
}
thead {
    color: rgb(200, 175, 125);
}
body {
  padding: 0;
  margin:auto auto;
  background-color: rgb(89, 89, 89);
}
</style>
"""


class descriptionTextBrowser(QTextBrowser):

    linkToDescription = Signal(str)

    def __init__(self, *args, **kwargs):
        super(descriptionTextBrowser, self).__init__(*args, **kwargs)
        self.movies = {}
        self.anchorClicked.connect(self.handleLink)

    def setMarkdown(self, markdown_path):
        with open(str(markdown_path), 'r') as fp:
            text = fp.read()

        # Find all relative paths.
        matcher = re.findall(URL_REGEX, text)

        # Update the markdown document source paths.
        image_root = str(markdown_path.parents(0) / 'source_images')
        updated_paths = text.replace('(./', f'({image_root}/')
        super(QTextBrowser, self).setMarkdown(updated_paths)

        html_from_markdown = self.toHtml()
        new = html_from_markdown.replace('type="circle"', 'type="disc"')
        new = new.replace('color:#0000ff;', 'color:rgb(105,125,245);')
        
        # Set Description Media
        root_append = partial(operator.add, image_root)
        paths = map(root_append, matcher)
        list(map(self.addAnimation, paths))
        # Set the modified markdown using HTML.
        self.setHtml(DESCRIPTION_STYLE + new)

    @Slot(QUrl)
    def handleLink(self, url):
        scheme = url.scheme()
        if scheme in ['https', 'http']:
            os.startfile(url.toString())
        elif scheme == 'peak':
            path = url.toString().replace('peak:///', '')
            peakLoad(path)

    @Slot()
    def searchPage(self, text):
        textCursor = self.textCursor()
        textCursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor, 1)
        self.setTextCursor(textCursor)
        self.find(text)

    @Slot(bool)
    def findNextInPage(self, *args, **kwargs):
        sender = self.sender()
        if sender:
            self.find(sender.text())

    @Slot(int)
    def movieCallback(self, url, value):
        new_img = self.movies[url].currentPixmap()
        self.document().addResource(QTextDocument.ImageResource, url, new_img)
        self.setLineWrapColumnOrWidth(self.lineWrapColumnOrWidth())
        self.update()

    def addAnimation(self, url):
        movie = QMovie(url)
        self.movies[url] = movie
        movie.setCacheMode(QMovie.CacheAll)
        callback = partial(self.movieCallback, url)
        movie.frameChanged.connect(callback)
        movie.start()

    def keyPressEvent(self, event):
        super(descriptionTextBrowser, self).keyPressEvent(event)
        key = event.key()
        mods = event.modifiers()
        if mods == Qt.ControlModifier and key == Qt.Key_C:
            clipboard = self.copy()
            if not clipboard:
                self.linkToDescription.emit('description')