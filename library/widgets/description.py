import re
import os
import operator
from functools import partial

from PySide6.QtCore import Slot, QUrl, Signal
from PySide6.QtGui import QImage, Qt, QTextDocument, QTextCursor, QMovie, QColor
from PySide6.QtWidgets import QTextBrowser, QTextEdit, QApplication, QInputDialog, QLineEdit

from library.config import peakLoad
from sequence_path.main import SequencePath as Path

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
    color: rgb(215, 215, 215);
}
h2 {
    color: rgb(190, 190, 190);
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
  background-color: rgb(80, 80, 80);
}
</style>
"""

image_template = "![Image Url](./{})"

class DescriptionTextEdit(QTextEdit):


    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()
        
        if mods == Qt.ControlModifier and key == Qt.Key_V:
            destination_folder = self.markdown_path.parent / 'source_images'
            clipboard = QApplication.clipboard()
            clip_img = clipboard.image()
            mime = clipboard.mimeData()
            if not clip_img.isNull():
                name, ok = QInputDialog.getText(self, 'Insert Image',
                        "Name:", QLineEdit.Normal)
                if not ok:
                    return
                out_file = destination_folder / f'{name}.jpg'
                clip_img.save(str(out_file))
                self.insertImage(out_file.stem)

            elif mime.hasUrls():
                for url in mime.urls():
                    file_path = Path(url.toLocalFile())
                    out_file = destination_folder / file_path.stem
                    file_path.copyTo(out_file)
                    self.insertImage(out_file.stem)

        super(DescriptionTextEdit, self).keyPressEvent(event)

    def insertImage(self, path):
        text = image_template.format(path)
        self.textCursor().insertText(text)


class descriptionTextBrowser(QTextBrowser):

    linkToDescription = Signal(str)
    assetClicked = Signal(str)
    matchCountChanged = Signal(str)

    def __init__(self, *args, **kwargs):
        super(descriptionTextBrowser, self).__init__(*args, **kwargs)
        self.movies = {}
        self.anchorClicked.connect(self.handleLink)
        self.setMinimumSize(795, 942)
        self.search_matches = []
        self.current_match_index = 0

    def setMarkdown(self, markdown_path, text=None):
        if markdown_path:
            self.markdown_path = markdown_path
        if not text:
            with open(str(markdown_path), 'r') as fp:
                text = fp.read()

        # Find all relative paths.
        matcher = re.findall(URL_REGEX, text)

        # Update the markdown document source paths.
        image_root = str(self.markdown_path.parent / 'source_images')
        updated_paths = text.replace('(./', f'({image_root}/')
        updated_paths = updated_paths.replace('\n\n', '\n\n&nbsp;\n')

        super(QTextBrowser, self).setMarkdown(updated_paths)

        html_from_markdown = self.toHtml()
        new = html_from_markdown.replace('type="circle"', 'type="disc"')
        new = new.replace('color:#0000ff;', 'color:rgb(125,130,250);')
        # Set Description Media
        root_append = partial(operator.add, image_root)
        paths = map(root_append, matcher)
        list(map(self.addAnimation, paths))
        # Set the modified markdown using HTML.
        self.setHtml(DESCRIPTION_STYLE + new)
        return text

    @Slot(QUrl)
    def handleLink(self, url):
        scheme = url.scheme()
        path = url.toString()
        if scheme in ['https', 'http']:
            os.startfile(path)
        elif scheme == 'peak':
            path = path.replace('peak:///', '')
            peakLoad(path)
        elif scheme == 'relic':
            path = path.replace('relic:///', 'relic://')
            self.assetClicked.emit(path)

    @Slot()
    def searchPage(self, text):
        self.current_match_index = 0
        textCursor = self.textCursor()
        textCursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor, 1)
        self.setTextCursor(textCursor)
        self.search_matches.clear()
        bg_color = QColor(Qt.yellow).lighter(125)
        text_color = QColor(Qt.darkGray).darker(150)

        while self.find(text):
            match = QTextEdit.ExtraSelection()
            match.format.setBackground(bg_color) 
            match.format.setForeground(text_color) 
            match.cursor = self.textCursor()
            self.search_matches.append(match)
        self.setExtraSelections(self.search_matches)
        self.setTextCursor(textCursor)
        self.changeMatch()

    @Slot(bool)
    def findNextInPage(self, *args, **kwargs):
        sender = self.sender()
        if self.current_match_index == len(self.search_matches):
            return self.searchPage(sender.text())
        self.current_match_index += 1
        f'{self.current_match_index}/{len(self.search_matches)}'
        self.changeMatch()
        self.find(sender.text())

    def changeMatch(self):
        self.matchCountChanged.emit(f'{self.current_match_index}/{len(self.search_matches)}')

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

    @Slot(str)
    def onPlainTextEditChanged(self):
        text_edit = self.sender()
        self.setMarkdown(None, text_edit.toPlainText())
        v = text_edit.verticalScrollBar().value()
        self.verticalScrollBar().setValue(v)
