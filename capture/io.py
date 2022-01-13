import subprocess
from PySide6.QtMultimedia import (
    QAudioFormat,
    QMediaDevices,
    QAudioSource,
)
from PySide6.QtCore import QObject
CREATE_NO_WINDOW = 0x08000000

class AudioRecord(QObject):
    def __init__(self, audio_path):
        super(AudioRecord, self).__init__()
        input_device = QMediaDevices.defaultAudioInput()
        audio_format = QAudioFormat()
        audio_format.setSampleRate(44100)
        audio_format.setChannelCount(1) # 1 mono, 2 stereo
        audio_format.setSampleFormat(QAudioFormat.UInt8)

        self.cmd = [
            'ffmpeg',
            '-loglevel', 'error',
            '-y', # Always Overwrite
            '-r', '24', # FPS
            '-ar', '44100',
            '-ac', '1',
            '-f', 'u8',
            '-i', '-',
            str(audio_path),
        ]
        self.ffproc = subprocess.Popen(
            self.cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW,
        )

        self._audio_input = QAudioSource(input_device, audio_format, self)
        self._io_device = self._audio_input.start()
        self._io_device.readyRead.connect(self._readyRead)

    def stop(self):
        self.ffproc.stdin.close()
        self._audio_input.stop()

    def _readyRead(self):
        data = self._io_device.readAll()
        self.ffproc.stdin.write(data.data())
