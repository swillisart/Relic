
def bakeIes(afile, renderer=None):
    """Bakes IES preview from supplied render standalone
    
    Args:
        afile (alPath): library file path 
        renderer (str, optional): renderer name EXAMPLE: vray. Defaults to None.
    """
    if renderer == 'vray':
        regex = re.compile(r'ies_file="(.+)";')
        baker = AL_INSTALL_LOCATION / "generators/ies_bake.vrscene"
        render_path = alPrefs.getPref('renderer_executable')

    with open(str(baker), 'r') as fp:
        data = fp.read()
        substitute = 'ies_file="{}";'.format(afile)
    
    tmpfile = Path(tempfile.mkdtemp()) / baker.name

    with open(str(tmpfile), 'w') as fp:
        fp.write(re.sub(regex, substitute, data))

    proxy = afile.path.with_name(afile.name + '_proxy.exr')
    cmd = '"{render}" -sceneFile="{scn}" -imgFile="{img}" \
        -display=0 -verboseLevel=0 -numThreads=1'.format(
        render=render_path,
        scn=tmpfile,
        img=proxy
        )
    subprocess.call(cmd)
    os.remove(tmpfile)
    icon = proxy.with_name(afile.name + '_icon.jpg')
    makeIconFile(proxy, icon)


def resolve_asset_source_destination(fpath, destination, relative=0):
    """Puts the file type into a specified folder for the type.

    Example:
        (/path/to/source.tx, /library/category/asset, relative=0)
    
    Arguments:
        fpath {alPath} -- the input filepath to process.
        destination {str} -- library folder path to the asset.
    
    Keyword Arguments:
        relative {int} -- 1 returns out as a relative path without the 
        destination (default: {0})
    
    Returns:
        alPath -- the resolved location for the depenedent source file.
    """

    if fpath.path.suffix in TEXTURE_EXT:
        new_destination = "{}_sources/images/{}".format(destination.name, fpath.name)
    elif fpath.path.suffix in APP_EXT:
        new_destination = "{}_sources/scenes".format(destination.name)
    elif fpath.path.suffix in CACHE_EXT:
        new_destination = "{}_sources/caches".format(destination.name)
    else:
        new_destination = destination.name + "_sources"
    if relative:
        out = alPath("{}/{}".format(new_destination, fpath.path.name))
    else:
        out = alPath(destination.path / new_destination)
    return out


def remove_empty_folders(afile):
    # Remove the old sources folder if it's empty
    afile = alPath(afile)
    if not [x for x in afile.path.rglob("*")]:
        if afile.path.exists():
            try:
                os.rmdir(str(afile))
            except Exception as exerr:
                print(exerr)



class moveFileThread(QRunnable):
    def __init__(self, source, asset_fields, parent=None):
        """Moves a file in the filesystem.

        On completion emits completed signal with this data:
            {'category': 'tool', 'Parent': 'color', 'Path': 'tool/color/nfile/nfile.exr' }

        Args:
            source (str/alPath): Source file path
            asset_fields (dict): # EX: {'category': 'tool', 'Parent': 'color'}
            parent (QWidget, optional): Defaults to None.
        """
        super(moveFileThread, self).__init__(parent)
        self.parent = parent
        self.source = source
        self.asset_fields = asset_fields
        self.signals = alResourceSignals()
        self.library_storage = Path(alPrefs.getPref('library_storage_dir'))

    def run(self):
        source = self.source
        if isinstance(source, str):
            source = alPath(source)

        if not source.exists:
            source = alPath(self.library_storage / str(source), checksequence=True)

        relative_destination = "{}/{}/{}/{}".format(
            self.asset_fields['category'], self.asset_fields['Parent'], source.name, source.path.name
        )
        destination = alPath(self.library_storage / relative_destination)
        try:
            destination.path.parent.mkdir(parents=True)
        except WindowsError:
            pass

        pluginFileHandler = plugins.getFileIngestHandler(source.ext)
        if pluginFileHandler is not None:
            pluginFileHandler(source, destination.parents(0))

        # If the source is sequence copy all the frames
        if isinstance(source.sequence_path, str):
            for x in glob.iglob(source.sequence_path):
                transferFile(x, destination.parent)
            # Make library relative destination use
            # expression notation file.1001.exr > file.%04d.exr 
            relative_destination = "{}/{}/{}/{}".format(
                self.asset_fields['category'],
                self.asset_fields['Parent'],
                source.name,
                source.name + source.frame_expr + source.ext
            )

        # only move if the destination isn't already there
        elif not destination.exists:
            transferFile(source, destination.parent)
        
        # Copy all the support files (proxies, QT's, previews)
        for x in glob.iglob(str(source.path.parent / (source.name + '_*'))):
            transferFile(x, destination.parent)
        
        # transfer the hash text group.
        hash_proxy = source.parents(0) / 'hashes_proxy.txt' 
        transferFile(str(hash_proxy), destination.parent)

        if self.asset_fields['Parent'] != 'unsorted':
            remove_empty_folders(source.parent)

        self.asset_fields['Path'] = relative_destination
        destination.checkSequence()
        time.sleep(0.003)
        self.signals.completed.emit((destination, self.asset_fields))


class trashFiles(QRunnable):
    def __init__(self, queue, parent=None):
        super(trashFiles, self).__init__(parent)
        self.parent = parent
        self.queue = queue
        self.library_storage = Path(self.parent.getPref('library_storage_dir'))

    def run(self):
        source = alPath(self.queue)
        if not source.exists:
            source = alPath(self.library_storage / str(source.parent))
        destination = self.library_storage / 'trash' / source.name
        try:
            destination.mkdir(parents=True)
        except WindowsError:
            pass

        transferFile(source, destination)

        remove_empty_folders(source.parent)


class alThread(QThread):
    """Base class for all asset library threads
    has stopping and signal mechanisms built in
    """

    def __init__(self, parent=None, signals=None):
        super(alThread, self).__init__(parent)
        self.mutex = QMutex()
        self.signals = signals
        self.stopped = False
        self.progress = 0

    def stop(self):
        with QMutexLocker(self.mutex):
            self.stopped = True

    def isStopped(self):
        try:
            self.mutex.lock()
            return self.stopped
        finally:
            self.mutex.unlock()

    def setQueue(self, queue):
        self.queue = queue
        self.queue_length = len(self.queue)

    def setProgress(self, value):
        self.progress += value
        percentage = int((self.progress * 100) / self.queue_length)
        self.signals.progress.emit(percentage)

    def complete(self, data):
        self.signals.completed.emit(data)
        self.stop()
        self.exit()


class alThreadPull(alThread):
    def __init__(self, parent=None, signals=None):
        super(alThreadPull, self).__init__(parent, signals)
        self.pool = QThreadPool.globalInstance()
        self.destination = None
        self.allpaths = []
        self.library_storage = alPrefs.getPref('library_storage_dir')

    def setDestination(self, destination):
        self.destination = destination

    def run(self):
        while not self.isStopped() and self.destination:
            if self.queue:
                qued = alPath(str(self.queue.pop(0)), checksequence=True)
                self.sendRepathing(qued)
                sources_folder = qued.path.parent / (qued.name + "_sources")
                if sources_folder.exists():
                    for x in sources_folder.rglob("*"):
                        if x.is_file():
                            self.queue_length += 1
                            time.sleep(0.003)
                            self.setupWorker(str(x))

                if qued.sequence_path:
                    self.queue_length = (self.queue_length - 1)
                    for x in glob.iglob(qued.sequence_path):
                        self.queue_length += 1

                        self.setupWorker(x)
                else:
                    self.setupWorker(qued)
            else:
                self.stop()

    def sendRepathing(self, qued):        
        item = resolve_asset_source_destination(qued, self.destination)

        repathed = alPath(qued.path.as_posix().replace(self.library_storage, str(self.destination)+'/'))
        self.signals.completed.emit(str(repathed))

    def setupWorker(self, item):
        if isinstance(item, str):
            item = alPath(item)
        repathed = alPath(
            item.path.as_posix().replace(self.library_storage, str(self.destination)+'/')
        )

        if repathed.exists:
            self.setProgress(1)
            return
        worker = copyFileThread(
            item, alPath(repathed.parent), signals=alThreadSignals()
        )
        worker.signals.progress.connect(self.setProgress)
        self.pool.start(worker)
        time.sleep(0.02)


class alThreadPush(alThread):
    def __init__(self, parent=None, signals=None):
        super(alThreadPush, self).__init__(parent, signals)
        self.pool = QThreadPool.globalInstance()
        self.destination = None

    def setDestination(self, destination):
        self.destination = alPath(destination)

    def run(self):
        while not self.isStopped() and self.destination:
            if self.queue:
                qued = alPath(self.queue.pop(0), checksequence=True)
                if qued.sequence_path:
                    for x in glob.iglob(qued.sequence_path):
                        self.queue_length += 1
                        self.setupWorker(x, sequence=1)
                else:
                    self.setupWorker(qued)
            else:
                self.complete(str(self.destination))


    def setupWorker(self, item, sequence=0):
        if isinstance(item, str):
            item = alPath(item)

        destination = resolve_asset_source_destination(item, self.destination)

        worker = copyFileThread(item, destination, signals=alThreadSignals())
        worker.signals.progress.connect(self.setProgress)
        self.pool.start(worker)
        time.sleep(0.02)


class copyFileThread(QRunnable):
    """Copies file from source to destination
    also emits a progress signal to connect
    """

    def __init__(self, source, destination, parent=None, signals=None):
        super(copyFileThread, self).__init__(parent, signals)
        self.source = source
        self.destination = destination
        self.signals = signals

    def run(self):
        try:
            self.destination.path.mkdir(parents=True)
        except Exception:
            pass
        try:
            if self.source.exists:
                transferFile(self.source, self.destination, copy=True)
        except Exception:
            pass
        self.signals.progress.emit(1)


class progressNotifier(QDialog):
    def __init__(self, parent, panel, dependent_files, destination, function=None):
        super(progressNotifier, self).__init__(parent)
        self.parent = parent
        self.panel = panel
        self.function = function
        self.destination = destination
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 0, 5, 5)
        self.layout.setSpacing(4)
        self.setLayout(self.layout)
        self.label = QLabel("Synchronizing Files Counting...")
        self.label.setAlignment(Qt.AlignCenter)
        self.progressBar = QProgressBar(self)
        self.progressBar.setFixedHeight(11)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.progressBar)

        # Resize / move Event filters
        self.resize(self.sizeHint())

        # Threading / Worker
        thread = QThread(self)
        self.worker = progressWorker()
        self.worker.moveToThread(thread)
        self.worker.progress.connect(self.updateProgress)
        self.worker.completed.connect(self.updateCompletion)
        self.worker.setupWorker(dependent_files, destination)
        thread.started.connect(self.worker.run)
        thread.start()
        self.show()
        self.temp = []

    def updateCompletion(self, val):
        self.temp.append(val)

    def updateProgress(self, val):
        try:
            if val == 100:
                # Pass the destination to function with main category and close
                log.debug('Finished synchronization with files{}'.format(self.temp))

                for x in self.temp:
                    self.function(x)
                self.close()

            self.progressBar.setValue(val)
            self.label.setText("Synchronizing Files... {}%...".format(val))
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_tb(exc_traceback)
            
    def contextMenu(self):
        context_menu = QMenu(self)
        collapseall = context_menu.addAction("Close")
        collapseall.triggered.connect(self.close)
        context_menu.exec_(QCursor.pos())

    def sizeHint(self):
        return QSize(320, 24)


class progressWorker(QObject):
    progress = Signal(int)
    completed = Signal(str)

    def run(self):
        self.pull.start()

    def setupWorker(self, dependent_files, destination):
        self.pull = alThreadPull(signals=alThreadSignals())
        self.pull.setQueue(dependent_files)
        self.pull.signals.progress.connect(self.progress.emit)
        self.pull.signals.completed.connect(self.completed.emit)
        self.pull.setDestination(destination)
