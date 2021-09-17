import subprocess
from PySide2.QtMultimedia import (
    QAudioDeviceInfo,
    QAudioFormat,
    QAudioInput
)
from PySide2.QtCore import QObject
CREATE_NO_WINDOW = 0x08000000

class AudioRecord(QObject):
    def __init__(self, audio_path):
        super(AudioRecord, self).__init__()
        inputDevice = QAudioDeviceInfo.defaultInputDevice()
        formatAudio = QAudioFormat()
        #formatAudio.setSampleRate(8000)
        formatAudio.setSampleRate(44100)
        formatAudio.setChannelCount(1) # 1 mono, 2 stereo
        formatAudio.setSampleSize(8)
        formatAudio.setCodec("audio/pcm")
        formatAudio.setByteOrder(QAudioFormat.LittleEndian)
        formatAudio.setSampleType(QAudioFormat.UnSignedInt)

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
        self.audioInput = QAudioInput(inputDevice, formatAudio, self)
        self.ioDevice = self.audioInput.start()
        self.ioDevice.readyRead.connect(self._readyRead)

    def stop(self):
        self.ffproc.stdin.close()
        self.audioInput.stop()

    def _readyRead(self):
        data = self.ioDevice.readAll()
        self.ffproc.stdin.write(data.data())