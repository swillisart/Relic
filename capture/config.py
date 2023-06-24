import os
import logging

# -- Third-party --
from qt_logger import attachHandler

logging.basicConfig(
    filename='{}/.relic/capture.log'.format(os.environ.get('USERPROFILE')),
    level=os.environ.get('LOGLEVEL', logging.WARNING),
)
#attachHandler(logging.getLogger('libav'))
