from PySide6.QtGui import QPainter


class ContextPainter(QPainter):
    def __init__(self, *args, **kwargs):
        super(ContextPainter, self).__init__(*args, **kwargs)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

    def __enter__(self):
        self.save()
        return self

    def __exit__(self, *exc):
        self.restore()
        return False


class SinglePainter(QPainter):
    def __init__(self, *args, **kwargs):
        super(SinglePainter, self).__init__(*args, **kwargs)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.end()
        return False