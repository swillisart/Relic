import operator
import os
import re
from functools import partial

import markdown
from library.config import RELIC_PREFS, peakLoad
from library.io.util import readMovieFrames
from PySide6.QtCore import (QEvent, QFile, QObject, QTextStream, QTimer, QUrl,
                            Signal, Slot, QSignalBlocker)
from PySide6.QtGui import (QFont, QColor, QFontMetrics, QImage, QKeySequence, QMovie,
                           QShortcut, Qt, QTextCursor, QTextDocument, QTextOption)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog,
                               QDialogButtonBox, QInputDialog, QLineEdit,
                               QTextBrowser, QTextEdit, QWidget)
from relic.qt.widgets import FilterBox
from sequence_path.main import SequencePath as Path

URL_REGEX = re.compile(r'\(\.(\/.+)\)')
H_3_5 = re.compile(r'>(.+<\/h[3-5]>)')
TEXT_REGEX = re.compile(r'[^a-zA-Z0-9]')
PRE_BLOCK = re.compile(r'<blockquote>')
END_BLOCK = re.compile(r'<\/blockquote>')

pre_blockquote_elems = """
<table cellspacing=0 width='100%'>
<tr>
<td width=6 bgcolor='#2399DC' class='quote'/>
<td bgcolor='#37414B' style='padding: 4 4px;'>
"""

post_quote_elems = """
</td>
</tr>
</table>
"""

def readTextFromResource(path):
    this_file = QFile(path)
    if not this_file.exists():
        return ''
    this_file.open(QFile.ReadOnly | QFile.Text)
    result = QTextStream(this_file).readAll()
    this_file.close()
    return result


MARKDOWN_STYLE = readTextFromResource(':/resources/style/markdown_style.css')

MARKDOWN = markdown.Markdown(
    extensions = [
        'codehilite', 'tables', 'nl2br', 'toc', 'sane_lists',
        'admonition', 'fenced_code'],
    output_format="html5"
    )

image_template = "![Image Url](./{})"

class TextEdit(QTextEdit):

    def __init__(self, *args, **kwargs):
        super(TextEdit, self).__init__(*args, **kwargs)
        font_width = QFontMetrics(self.currentCharFormat().font()).averageCharWidth()
        self.setTabStopDistance(4 * font_width)
        self.setWordWrapMode(QTextOption.WordWrap)

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
                out_file = destination_folder / f'{name}.png'
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
        self.setWordWrapMode(QTextOption.WordWrap)

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
        # Add non-breaking spaces after markdown headers.
        gen_html = MARKDOWN.convert(updated_paths)

        gen_html = gen_html.replace('/h1>', '/h1><hr>')
        gen_html = gen_html.replace('/h2>', '/h2><hr>')

        # insert spaces on header 3-5 titles. 
        # NB: "\\1" is a backreference to the first regex capture group.
        gen_html = re.sub(H_3_5, '>&nbsp;\\1', gen_html)

        # Hack the blockquote to utilize a spreadsheet / grid for borders.
        gen_html = re.sub(PRE_BLOCK, pre_blockquote_elems, gen_html)
        gen_html = re.sub(END_BLOCK, post_quote_elems, gen_html)

        # Set Description Media
        root_append = partial(operator.add, image_root)
        paths = map(root_append, matcher)
        list(map(self.addAnimation, paths))
        # Set the modified markdown using HTML.
        rep = gen_html.replace('\n</code></pre>', '</code></pre>')
        self.setHtml(MARKDOWN_STYLE + rep + '<br>'*2)

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
        self.changeMatchCount()

    @Slot(bool)
    def findNextInPage(self, *args, **kwargs):
        sender = self.sender()
        if self.current_match_index == len(self.search_matches):
            return self.searchPage(sender.text())
        self.current_match_index += 1
        self.changeMatchCount()
        self.find(sender.text())

    def changeMatchCount(self):
        counter = f'{self.current_match_index}/{len(self.search_matches)}'
        self.matchCountChanged.emit(counter)

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
            if not self.textCursor().selectedText():
                self.linkToDescription.emit('description')


from library.ui.description import Ui_DescriptionDialog


class Window(Ui_DescriptionDialog, QDialog):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        self.text_browser.matchCountChanged.connect(self.found_results_label.setText)
        self.filter_box = FilterBox(self)
        self.filter_box.button.setChecked(True)
        self.filter_box.editor.textChanged.connect(self.text_browser.searchPage)
        self.filter_box.editor.returnPressed.connect(self.text_browser.findNextInPage)
        self.filter_layout.insertWidget(0, self.filter_box)
        self.button_box.clicked.connect(self.onDescriptionButtonClicked)
        self.text_edit.textChanged.connect(self.onTextEditorChanged)

        QShortcut(QKeySequence('ctrl+f'), self, self.filter_box.editor.setFocus)
        QShortcut(QKeySequence('ctrl+b'), self, self.emboldenSelection)
        QShortcut(QKeySequence('ctrl+i'), self, self.italicizeSelection)
        self.base_width = self.width()
        self.edit_scroller = self.text_edit.verticalScrollBar()
        self.view_scroller = self.text_browser.verticalScrollBar()
        self.edit_scroller.valueChanged.connect(self.moveOtherSlider)
        self.view_scroller.valueChanged.connect(self.moveOtherSlider)
        self.source_asset = None
    
    @Slot()
    def moveOtherSlider(self, value: int):
        sender = self.sender()
        edit = self.edit_scroller
        view = self.view_scroller
        if sender is edit:
            other = view
            this = edit
        elif sender is view:
            this = view
            other = edit
        normalized = self.normalizedScrollValue(this)
        other.valueChanged.disconnect(self.moveOtherSlider)
        other.setValue(normalized * other.maximum())
        other.valueChanged.connect(self.moveOtherSlider)

    @staticmethod
    def normalizedScrollValue(scroller):
        v = scroller.value() or 1
        m = scroller.maximum() or 1
        return v / m

    @Slot()
    def onTextEditorChanged(self, content=True):
        markdown_text = self.text_edit.toPlainText()
        self.text_browser.setMarkdown(markdown_text)

        cursor = self.text_edit.textCursor()
        position = cursor.block().position() or 1
        length = len(self.text_edit.toPlainText()) or 1
        normalized_position = position / length
        edit_scroller = self.text_edit.verticalScrollBar()
        view_scroller = self.text_browser.verticalScrollBar()
        edit_max = edit_scroller.maximum() or 1
        view_max = view_scroller.maximum() or 1
        mult = view_max / edit_max
        value = edit_max * normalized_position
        if normalized_position > 0.95:
            tc = self.text_browser.textCursor()
            tc.movePosition(QTextCursor.End, QTextCursor.MoveAnchor, 1)
            self.text_browser.setTextCursor(tc)
        else:
            view_scroller.setValue(int(value * mult))

    def italicizeSelection(self):
        this_cursor = self.text_edit.textCursor()
        start = this_cursor.selectionStart()
        end = this_cursor.selectionEnd()
        this_cursor.beginEditBlock()
        this_cursor.setPosition(start)
        this_cursor.insertText('_')
        this_cursor.setPosition(end+1)
        this_cursor.insertText('_')
        this_cursor.endEditBlock()

    def emboldenSelection(self):
        this_cursor = self.text_edit.textCursor()
        start = this_cursor.selectionStart()
        end = this_cursor.selectionEnd()
        this_cursor.beginEditBlock()
        this_cursor.setPosition(start)
        this_cursor.insertText('**')
        this_cursor.setPosition(end+2)
        this_cursor.insertText('**')
        this_cursor.endEditBlock()

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

    def fromResource(self, path):
        # The source markdown is from an embedded uneditable resource.
        self.editor_frame.setVisible(False)
        markdown_text = readTextFromResource(path)
        self.text_browser.markdown_path = Path('')
        self.text_edit.markdown_path = Path('')
        self.showMarkdown(markdown_text, edit_mode=False)

    def fromAsset(self, asset, edit_mode=False):
        # The source is an asset path.
        self.source_asset = asset
        path = asset.network_path
        if not path.ext.endswith('.md'):
            path = path.suffixed('_description', '.md')
        if not path.exists():
            path.touch()

        with open(str(path), 'r', encoding='utf-8') as fp:
            markdown_text = fp.read()
        self.text_browser.markdown_path = path
        self.text_edit.markdown_path = path
        self.showMarkdown(markdown_text, edit_mode)

    @Slot(Path)
    def showMarkdown(self, text_contents, edit_mode):
        self.editor_frame.setVisible(edit_mode)
        self.text_browser.setMarkdown(text_contents)
        self.text_edit.setPlainText(text_contents)
        width = self.base_width * (edit_mode + 1) # double width in edit mode
        self.resize(width, self.height())
        self.show()
        # Raise to front in case where we are launching via documentation link.
        self.activateWindow() 

    @Slot(QAbstractButton)
    def onDescriptionButtonClicked(self, button):
        role = self.button_box.buttonRole(button)
        if role == QDialogButtonBox.ResetRole:
            self.fromAsset(self.source_asset)
        elif role == QDialogButtonBox.AcceptRole:
            text = self.text_edit.toPlainText()
            with open(str(self.text_browser.markdown_path), 'w', encoding='utf-8') as fp:
                fp.write(text)
            self.updateAsset(text)
            self.close()
        elif role == QDialogButtonBox.HelpRole:
            mdc = ':resources/app/MarkdownCheatsheet.md'
            new_window = PopupDescription(self).fromResource(mdc)

    def updateAsset(self, text):
        asset = self.source_asset
        if asset:
            # Construct description text using the document title.
            value = 'Documentation' # default
            for line in text.split('\n'):
                if line.startswith('#'):
                    # Sanitize title string removing special characters.
                    value = re.sub(r'[^a-zA-Z0-9\s]', '', line)
                    # Trim leading and trailing whitespace.
                    value = re.sub(r'^\s+|\s+$', '', value) 
                    break
            asset.description = value
            asset.filesize = asset.network_path.parent.size.kilobytes
            asset.update(fields=['description', 'filesize'])


class PopupDescription(Window):
    @Slot(QEvent)
    def closeEvent(self, event):
        QDialog.closeEvent(self, event)
        self.deleteLater()
