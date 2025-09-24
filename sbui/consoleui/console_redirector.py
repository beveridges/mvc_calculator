import sys
from PyQt5.QtCore import QObject, pyqtSignal

class EmittingStream(QObject):
    text_written = pyqtSignal(str)

    def write(self, text):
        if text.strip():
            self.text_written.emit(text)

    def flush(self):
        pass

def redirect_stdout(target_signal):
    """Redirects sys.stdout to the given signal."""
    stream = EmittingStream()
    stream.text_written.connect(target_signal)
    sys.stdout = stream
    return stream
