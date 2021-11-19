from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import numpy as np
from .paint_dock import Ui_PaintDock
import cv2
import glm


class colorSampler(QDialog):

	def __init__(self, parent=None):
		super(colorSampler, self).__init__(parent)
		self.setGeometry(QRect(0, 0, 170, 52))
		self.setWindowFlags(Qt.FramelessWindowHint)
		self.setAttribute(Qt.WA_StaticContents)
		self.lut_vec3data = self.raw_vec3data = (0, 0, 0)
		self.view = None
		self.font = QFont("Consolas", 8)
		self.setStyleSheet(
			"QDialog {font-weight: bold; border: 1px solid rgb(66, 118, 150)}"
		)
		self.hide()

	def setRGB(self, lutsample, rawsample, view):
		self.hide()
		self.view = view
		self.lut_vec3data = lutsample
		self.raw_vec3data = rawsample
		size_str = ''.join(["{:.3f}".format(x) for x in rawsample])
		size_str += view
		window_width = QFontMetrics(self.font).boundingRect(size_str).width()
		self.setGeometry(QRect(0, 0, window_width + 56, 52))
		self.update()
		self.show()

	def paintEvent(self, event):
		qp = QPainter(self)
		qp.setRenderHint(QPainter.Antialiasing)
		qp.setFont(self.font)

		# Paint frame
		self.paintRGB(qp, self.lut_vec3data, self.view)
		yoffset = 25
		space = self.paintRGB(qp, self.raw_vec3data, 'RAW', offset=yoffset)

	@staticmethod
	def paintRGB(painter, rgb_vec, name, offset=0):
		nr, ng, nb = np.clip(np.multiply(255, rgb_vec), 0, 255)
		r, g, b = ["{:.3f}".format(x) for x in rgb_vec]

		# Constants
		height = 6 + offset
		size = 16
		space = 0
		spacing = 4
		text_height = height + (size / 2) + 3

		# Swatch
		qrgb = QColor(nr, ng, nb)
		painter.setBrush(qrgb)
		space += spacing + 3
		painter.drawRect(space, height, size, size)

		# RGB
		space += (size + spacing)
		painter.setPen(QColor(235, 100, 75))
		painter.drawText(space, text_height, r)

		space += (colorSampler.getTextWidth(painter, r) + spacing)

		painter.setPen(QColor(75, 225, 75))
		painter.drawText(space, text_height, g)

		space += (colorSampler.getTextWidth(painter, g) + spacing)
		painter.setPen(QColor(75, 100, 250))
		painter.drawText(space, text_height, b)

		# Label
		painter.setPen(QColor(200, 200, 200))
		space += (colorSampler.getTextWidth(painter, b) + spacing)
		painter.drawText(space, text_height, str('({})'.format(name)))

		return space

	@staticmethod
	def getTextWidth(painter, text):
		return painter.fontMetrics().boundingRect(text).width()


saturation_style = """QSlider::groove:horizontal {{
	background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgb(85, 85, 85), stop:1 rgb({}, {}, {}));
	padding-top: -6px;
	padding-bottom: -6px;
	margin-top: 5px;
	margin-bottom: 5px;
}}
QSlider::handle:horizontal {{
	background: rgb(0, 0, 0);
	border: 2px solid rgb(225, 225, 225);
	width: 2px;
	border-radius: 3px;
	padding-top: -6px;
	padding-bottom: -6px;
	margin-top: 5px;
	margin-bottom: 5px;
}}"""


class PaintDockWidget(Ui_PaintDock, QDockWidget):

	colorChanged = Signal(QColor)
	toolChanged = Signal(int)
	onClosed = Signal()
	Brush = 0
	Shape = 1
	Text = 2

	def __init__(self, *args, **kwargs):
		super(PaintDockWidget, self).__init__(*args, **kwargs)
		self.setupUi(self)
		self._color = QColor(255,255,255)

		self.colorWheelGLView.userPickedColor.connect(self.colorPicked)
		self.opacitySlider.valueChanged.connect(self.opacity_from_slider)
		self.opacityControl.valueChanged.connect(self.opacity_from_control)
		self.valueSlider.valueChanged.connect(self.value_from_slider)
		self.valueControl.valueChanged.connect(self.value_from_control)
		self.saturationSlider.valueChanged.connect(self.saturation_from_slider)
		self.saturationControl.valueChanged.connect(self.saturation_from_control)
		self.brushToolButton.toggled.connect(self.setBrushMode)
		self.shapeToolButton.toggled.connect(self.setShapeMode)
		self.textToolButton.toggled.connect(self.setTextMode)
		self.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable|QDockWidget.DockWidgetClosable)

	def closeEvent(self, event):
		event.ignore()
		msg = 'Closing will lose any unsaved annotations.'
		message = QMessageBox(QMessageBox.Warning, 'Are you sure?', msg,
					QMessageBox.NoButton, self)
		message.addButton('Yes', QMessageBox.AcceptRole)
		message.addButton('Cancel', QMessageBox.RejectRole)

		if message.exec_() == QMessageBox.RejectRole:
			return
		self.onClosed.emit()

	def setBrushMode(self, value):
		self.disableSignals()
		self.shapeToolButton.setChecked(Qt.Unchecked)
		self.textToolButton.setChecked(Qt.Unchecked)
		self.enableSignals()
		self.toolChanged.emit(self.Brush)

	def setShapeMode(self, value):
		self.disableSignals()
		self.brushToolButton.setChecked(Qt.Unchecked)
		self.textToolButton.setChecked(Qt.Unchecked)
		self.enableSignals()
		self.toolChanged.emit(self.Shape)

	def setTextMode(self, value):
		self.disableSignals()
		self.brushToolButton.setChecked(Qt.Unchecked)
		self.shapeToolButton.setChecked(Qt.Unchecked)
		self.enableSignals()
		self.toolChanged.emit(self.Text)

	def disableSignals(self):
		self.brushToolButton.blockSignals(True)
		self.shapeToolButton.blockSignals(True)
		self.textToolButton.blockSignals(True)
		self.saturationSlider.blockSignals(True)
		self.valueSlider.blockSignals(True)
		self.opacitySlider.blockSignals(True)
		self.saturationControl.blockSignals(True)
		self.valueControl.blockSignals(True)
		self.opacityControl.blockSignals(True)

	def enableSignals(self):
		self.brushToolButton.blockSignals(False)
		self.shapeToolButton.blockSignals(False)
		self.textToolButton.blockSignals(False)
		self.saturationSlider.blockSignals(False)
		self.valueSlider.blockSignals(False)
		self.opacitySlider.blockSignals(False)
		self.saturationControl.blockSignals(False)
		self.valueControl.blockSignals(False)
		self.opacityControl.blockSignals(False)

	@property
	def color(self):
		return self._color

	@color.setter
	def color(self, color):
		self._color = color
		r, g, b, a = color.getRgb()

		self.disableSignals()
		# Update Sliders
		self.saturationSlider.setValue(int(color.saturationF() * 1000))
		self.valueSlider.setValue(int(color.valueF() * 1000))
		self.opacitySlider.setValue(int(color.alphaF() * 1000))

		# Update Controls (SpinBoxes)
		self.saturationControl.setValue(color.saturationF())
		self.valueControl.setValue(color.valueF())
		self.opacityControl.setValue(color.alphaF())

		# Update Styles
		rgb_scaled = (np.array([r, g, b]) - min(r, g, b))
		rgb_scaled = rgb_scaled / max(rgb_scaled)
		rgb_scaled = (rgb_scaled * 255)
		
		self.saturationSlider.setStyleSheet(saturation_style.format(*rgb_scaled))
		self.colorPickerToolButton.setStyleSheet(
			'background-color: rgb({}, {}, {});'.format(r, g, b)
		)
		self.enableSignals()
		self.colorChanged.emit(self._color)

	@Slot()
	def value_from_control(self, val):
		h, s, v, a = self.color.getHsvF()
		new_color = QColor.fromHsvF(h, s, val, a)
		self.color = new_color

	@Slot()
	def value_from_slider(self, val):
		value = val / 1000
		self.value_from_control(value)

	@Slot()
	def opacity_from_control(self, opacity):
		h, s, v, a = self.color.getHsvF()
		new_color = QColor.fromHsvF(h, s, v, opacity)
		self.color = new_color

	@Slot()
	def opacity_from_slider(self, val):
		opacity = val / 1000
		self.opacity_from_control(opacity)

	@Slot()
	def saturation_from_control(self, sat):
		self.colorWheelGLView.positionFromSaturation(sat)
		h, s, v, a = self.color.getHsvF()
		new_color = QColor.fromHsvF(h, sat, v, a)
		self.color = new_color

	@Slot()
	def saturation_from_slider(self, sat):
		sat = (sat / 1000)
		self.saturation_from_control(sat)

	@Slot()
	def colorPicked(self, value, hue):
		rgb = value[:3]

		# Normalize to 0-1
		rgb_scaled = (rgb - min(rgb))
		if max(rgb_scaled) == 0:
			color = QColor.fromHsv(
				hue,
				self.color.saturation(),
				self.color.value(),
				self.color.alpha(),
			)
		else:
			r, g, b = rgb*self.color.valueF()
			color = QColor.fromRgbF(r, g, b, self.color.alphaF())
		self.color = color
