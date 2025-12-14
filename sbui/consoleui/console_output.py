import logging, os
from PyQt5.QtWidgets import QPlainTextEdit, QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QDialogButtonBox, QProgressDialog, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication
from .console_redirector import redirect_stdout
from .email_utils import send_email, SENDER_EMAIL, RECIPIENT_EMAIL, APP_PASSWORD


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
        """Send the current log file via email with optional user message."""
        if not self._logfile or not os.path.exists(self._logfile):
            logging.error("send_log: No logfile available to send")
            return False
        
        # Get parent window from target widget
        parent = None
        if self._target:
            parent = self._target.window()
        
        # Show dialog to get user message
        dialog = SendLogDialog(parent)
        if dialog.exec_() == QDialog.Accepted:
            user_message = dialog.get_message()
            logging.info(f"Sending session log with user message...")
            
            # Show progress dialog
            progress = QProgressDialog("Sending email...", None, 0, 0, parent)
            progress.setWindowTitle("Sending Log File")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.setMinimumWidth(400)
            progress.show()
            QApplication.processEvents()
            
            from datetime import datetime
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subject = f"MVCCalc Session Log — {now}"
            
            # Build email body with user message
            body = "Please find attached the session log."
            if user_message and user_message.strip():
                body += f"\n\n--- User Message ---\n{user_message.strip()}"
            
            # Send email
            success = send_email(
                subject=subject,
                body=body,
                attachments=[self._logfile],
                recipient=RECIPIENT_EMAIL,
                sender=SENDER_EMAIL,
                password=APP_PASSWORD
            )
            
            # Close progress dialog
            progress.close()
            
            if success:
                logging.info("Log file sent successfully.")
                QMessageBox.information(
                    parent,
                    "Email Sent",
                    "The email was sent successfully."
                )
            else:
                logging.error("Failed to send log file.")
                QMessageBox.warning(
                    parent,
                    "Email Failed",
                    "Failed to send the email. Please check your connection and try again."
                )
            
            return success
        else:
            # User cancelled
            logging.info("Send log cancelled by user.")
            return False


class SendLogDialog(QDialog):
    """Dialog for entering a message when sending log files."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Send Log File")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        
        layout = QVBoxLayout(self)
        
        # Label
        label = QLabel("Add an optional message to include with the log file:")
        label_font = label.font()
        label_font.setPointSize(11)
        label.setFont(label_font)
        layout.addWidget(label)
        
        # Text area for message
        self.message_edit = QTextEdit(self)
        self.message_edit.setPlaceholderText("Enter your message here (optional)...")
        self.message_edit.setMinimumHeight(150)
        # Increase font size for better readability
        font = self.message_edit.font()
        font.setPointSize(12)
        self.message_edit.setFont(font)
        layout.addWidget(self.message_edit)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        # Increase button text size
        button_font = button_box.font()
        button_font.setPointSize(11)
        button_box.setFont(button_font)
        layout.addWidget(button_box)
    
    def get_message(self):
        """Get the user's message."""
        return self.message_edit.toPlainText()