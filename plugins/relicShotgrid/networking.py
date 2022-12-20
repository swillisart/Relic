from collections import deque
from functools import partial
# -- Third-Party --
from relic.qt import *

from shotgun_api3 import Shotgun


class ShotgridCall(QObject):

    callback = Signal(dict)
    sg = None

    def __init__(self):
        super(ShotgridCall, self).__init__()

    #def execute(self, *args, **kwargs):
    #    result = super(ShotgridCall, self).execute(*args, **kwargs)


class FindAssets(ShotgridCall):

    def execute(self, filters):
        fields = [
            'code',
            'sg_asset_type',
            'sg_status_list',
            'created_at',
            'image',
            'assets',
        ]
        result = self.sg.find('Asset', filters, fields)
        return result

class FindShots(ShotgridCall):

    def execute(self, filters):
        fields = [
            'code',
        ]
        result = self.sg.find('Shot', filters, fields)
        return result

class GetThumbnail(ShotgridCall):

    def execute(self, url):
        return result

class Downloader(QNetworkAccessManager):

    def doRequest(self, url, callback=None):
        request = QNetworkRequest(url)
        response = self.get(request)
        response.finished.connect(partial(self.requestFinished, response, callback))

    def requestFinished(self, response, callback):
        content_type = response.header(QNetworkRequest.ContentTypeHeader)
        if content_type == 'image/jpeg':
            data = QPixmap()
            data.loadFromData(response.readAll(), 'JPG')
        callback(data)


class ShotgridClientSession(QThread):

    def __init__(self):
        super(ShotgridClientSession, self).__init__()
        ShotgridCall.sg = Shotgun(
            'https://crafty-staging.shotgunstudio.com',
            'interface',
            'z?akmjrsbqo6evajovZqsptqz'
        )

        self.find_assets = FindAssets()
        self.find_shots = FindShots()
        self.get_thumbnail = FindShots()

        self.queue = deque()
        self.mutex = QMutex()
        self.condition = QWaitCondition()

    def addToQueue(self, command):
        with QMutexLocker(self.mutex):
            self.queue.append(command)

        if not self.isRunning():
            self.start()
        else:
            self.condition.wakeOne()

    def run(self):
        while self.queue:
            self.mutex.lock()
            command, arg = self.queue.popleft()
            self.mutex.unlock()
            
            result = command.execute(arg)
            self.mutex.lock()
            command.callback.emit(result)
            self.condition.wait(self.mutex)
            self.mutex.unlock()

'''
sgshotid = sg.find_one("Shot", [['id', 'is', shotid]])
sgcode = sg.find_one("Shot", [['id', 'is', shotid]], ["code", 'description'])
projectid = sg.find_one("Project", [['name', 'is', 'shipsNshit']])

sgdata = {
    'code': sgcode['code'] + "_v001",
    'project': projectid,
    'sg_path_to_frames': sgcode['description'],
    'entity': {'type': 'Shot', 'id': sgshotid['id']},
}

result = sg.create('Version', sgdata)
sg.upload('Version', result['id'], qt, 'sg_uploaded_movie')


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    session = ShotgridClientSession()
    filters = [['project.Project.id', 'is', 70]]
    session.find_assets.execute(filters)
    #session.find_shots.execute(filters)
    sys.exit(app._exec())
'''