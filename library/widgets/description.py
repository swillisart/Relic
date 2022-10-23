import re
import os
import operator
from functools import partial
import markdown

from PySide6.QtCore import Slot, QUrl, Signal, QFile, QTextStream, QEvent, QObject, QTimer
from PySide6.QtGui import QImage, Qt, QTextDocument, QTextCursor, QMovie, QColor, QFontMetrics
from PySide6.QtWidgets import QDialogButtonBox, QTextBrowser, QTextEdit, QApplication, QInputDialog, QLineEdit, QWidget, QAbstractButton, QDialog

from library.config import peakLoad, RELIC_PREFS
from library.io.util import readMovieFrames
from sequence_path.main import SequencePath as Path
from relic.qt.widgets import FilterBox

URL_REGEX = re.compile(r'\(\.(\/.+)\)')

style_file = QFile(':/resources/style/markdown_style.css')
style_file.open(QFile.ReadOnly | QFile.Text)
style_sheet = QTextStream(style_file)
MARKDOWN_STYLE = style_sheet.readAll()

MARKDOWN = markdown.Markdown(
    extensions = ['codehilite', 'tables', 'nl2br', 'toc', 'sane_lists', 'admonition', 'fenced_code'],
    output_format="html5"
    )

image_template = "![Image Url](./{})"

class TextEdit(QTextEdit):

    def __init__(self, *args, **kwargs):
        super(TextEdit, self).__init__(*args, **kwargs)
        font_width = QFontMetrics(self.currentCharFormat().font()).averageCharWidth()
        self.setTabStopDistance(4 * font_width)

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
                out_file.createParentFolders()
                clip_img.save(str(out_file))
                self.insertImage(out_file.stem)
                return
            elif mime.hasUrls():
                for url in mime.urls():
                    file_path = Path(url.toLocalFile())
                    out_file = destination_folder / file_path.stem
                    file_path.copyTo(out_file)
                    self.insertImage(out_file.stem)
                    return

        super(TextEdit, self).keyPressEvent(event)

    def insertImage(self, path):
        text = image_template.format(path)
        self.textCursor().insertText(text)


class MiniMovie(QObject):
    def __init__(self, path):
        super(MiniMovie, self).__init__()
        self.frames = readMovieFrames(path)
        self.frame_number = 0

    def currentFrame(self):
        return self.frames[self.frame_number]

    def toNextFrame(self):
        self.frame_number += 1
        if self.frame_number >= len(self.frames):
            self.frame_number = 0


class TextBrowser(QTextBrowser):

    linkToDescription = Signal(str)
    assetClicked = Signal(str)
    matchCountChanged = Signal(str)

    def __init__(self, *args, **kwargs):
        super(TextBrowser, self).__init__(*args, **kwargs)
        font_width = QFontMetrics(self.currentCharFormat().font()).averageCharWidth()
        self.setTabStopDistance(2 * font_width)

        self.movies = {}
        self.anchorClicked.connect(self.handleLink)
        self.search_matches = []
        self.current_match_index = 0

        self.movie_timer = QTimer()
        self.movie_timer.setInterval(1000/24) # 24 fps in milliseconds
        self.movie_timer.timeout.connect(self.updateMovieFrames)

    def updateMovieFrames(self):
        for url, movie in self.movies.items():
            movie.toNextFrame()

            new_img = movie.currentFrame()
            self.document().addResource(QTextDocument.ImageResource, url, new_img)
            self.setLineWrapColumnOrWidth(self.lineWrapColumnOrWidth())
        self.update()

    def setMarkdown(self, text):
        # Find all relative paths.
        matcher = re.findall(URL_REGEX, text)

        # Update the markdown document source paths.
        image_root = str(self.markdown_path.parent / 'source_images')
        updated_paths = text.replace('(./', f'({image_root}/')
        gen_html = MARKDOWN.convert(updated_paths)

        # Set Description Media
        root_append = partial(operator.add, image_root)
        paths = map(root_append, matcher)
        list(map(self.addAnimation, paths))
        # Set the modified markdown using HTML.
        self.setHtml(MARKDOWN_STYLE + gen_html + '<br>'*3)

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

    def addAnimation(self, url):
        if not url.endswith('mp4') or not Path(url).exists or url in self.movies.keys():
            return
        movie = MiniMovie(url)
        self.movies[url] = movie
        if not self.movie_timer.isActive():
            self.movie_timer.start()

    def keyPressEvent(self, event):
        super(TextBrowser, self).keyPressEvent(event)
        key = event.key()
        mods = event.modifiers()
        if mods == Qt.ControlModifier and key == Qt.Key_C:
            clipboard = self.copy()
            if not clipboard:
                self.linkToDescription.emit('description')

    @Slot(str)
    def onPlainTextEditChanged(self):
        text_edit = self.sender()
        markdown_text = text_edit.toPlainText()
        self.setMarkdown(markdown_text)
        v = text_edit.verticalScrollBar().value()
        self.verticalScrollBar().setValue(v)

from library.ui.description import Ui_DescriptionDialog

class Window(Ui_DescriptionDialog, QDialog):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.text_browser.matchCountChanged.connect(self.found_results_label.setText)
        self.filter_box = FilterBox(self)
        self.filter_box.editor.textChanged.connect(self.text_browser.searchPage)
        self.filter_box.editor.returnPressed.connect(self.text_browser.findNextInPage)
        self.filter_layout.insertWidget(0, self.filter_box)
        self.button_box.clicked.connect(self.onDescriptionButtonClicked)
        self.text_edit.textChanged.connect(self.text_browser.onPlainTextEditChanged)

    @Slot(Path)
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            return
        super(Window, self).keyPressEvent(event)

    @Slot(QEvent)
    def closeEvent(self, event):
        self.hide()
        self.text_browser.movies = {}
        event.ignore()

    @Slot(Path)
    def showMarkdown(self, path):
        if not path.exists():
            return
        self.editor_frame.setVisible(int(RELIC_PREFS.edit_mode))
        
        with open(str(path), 'r') as fp:
            markdown_text = fp.read()
            
        self.text_browser.markdown_path = path
        self.text_browser.setMarkdown(markdown_text)
        self.text_edit.markdown_path = path
        self.text_edit.setPlainText(markdown_text)

        self.show()
        self.activateWindow()

    @Slot(QAbstractButton)
    def onDescriptionButtonClicked(self, button):
        role = self.button_box.buttonRole(button)
        if role == QDialogButtonBox.ResetRole:
            self.showMarkdown(self.text_browser.markdown_path)
        elif role == QDialogButtonBox.AcceptRole:
            text = self.text_edit.toPlainText()
            with open(str(self.text_browser.markdown_path), 'w') as fp:
                fp.write(text)
            self.close()
        elif role == QDialogButtonBox.HelpRole:
            pass
