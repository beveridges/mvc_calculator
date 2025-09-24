import logging, os
from PyQt5.QtWidgets import QPlainTextEdit
from .console_redirector import redirect_stdout
from .email_utils import email_file, SENDER_EMAIL, RECIPIENT_EMAIL, APP_PASSWORD


class QtPlainTextEditHandler(logging.Handler):
    """Logging handler that sends log records to a QPlainTextEdit."""

    def __init__(self, target, formatter=None):
        super().__init__()
        self._target = target
        if formatter:
            self.setFormatter(formatter)

    def emit(self, record):
        msg = self.format(record)
        try:
            if self._target is not None and isinstance(self._target, QPlainTextEdit):
                self._target.appendPlainText(msg)
                # Scroll to bottom
                sb = self._target.verticalScrollBar()
                sb.setValue(sb.maximum())
            elif hasattr(self._target, "appendPlainText"):
                self._target.appendPlainText(msg)
        except RuntimeError:
            # widget was deleted — remove handler to avoid future crashes
            logging.getLogger().removeHandler(self)

class SBConsoleOutput:
    '''
    target:  the target QPlainTextEdit
    
    '''
    
    DEFAULT_STYLE = """
    QPlainTextEdit {
        background-color: #1e1e1e;
        color: #00ff00;
        font-family: Consolas, monospace;
        font-size: 10pt;
    }
    """
    def __init__(self, target=None, style=None, formatter=None, send_button=None, logfile=None):
        self._target = target
        self._style = style or self.DEFAULT_STYLE
        self._formatter = formatter
        self._logfile = logfile 
    
        if self._target and hasattr(self._target, "setStyleSheet"):
            self._target.setStyleSheet(self._style)
    
        # 1) Redirect print() → QPlainTextEdit
        if self._target:
            redirect_stdout(self._target.appendPlainText)
    
        # 2) Attach logging handler
        if self._target:
            self.set_target(self._target, self._style)
    
        # 3) Connect button if provided        
        if send_button is not None:
            send_button.clicked.connect(self.send_log)
            

    
    # def __init__(self, target=None, style=None, formatter=None, send_button=None, logfile=None):
    #     self._target = target
    #     self._style = style or self.DEFAULT_STYLE
    #     self._formatter = formatter
    #     self._logfile = logfile 
        
    #     if self._target and hasattr(self._target, "setStyleSheet"):
    #         self._target.setStyleSheet(self._style)

    #     # Connect button if provided        
    #     if send_button is not None:
    #         send_button.clicked.connect(self.send_log)



    def set_target(self, target, style=None):
        """Attach a QPlainTextEdit as the logging output."""
        self._target = target
        if hasattr(self._target, "setStyleSheet"):
            self._target.setStyleSheet(style or self._style or "")

        if self._target:
            handler = QtPlainTextEditHandler(self._target, formatter=self._formatter)
            logging.getLogger().addHandler(handler)


    def send_log(self):
        """Send the current log file via email."""
        if not self._logfile or not os.path.exists(self._logfile):
            logging.error("send_log: No logfile available to send")
            return False
    
        success = email_file(
            filepath=self._logfile,
            recipient=RECIPIENT_EMAIL,
            sender=SENDER_EMAIL,
            password=APP_PASSWORD
        )
        return success