# load_mat_dialog.py (top imports)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QThread, QObject, QCoreApplication, QUrl
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QListWidgetItem,
    QMessageBox,
    QProgressDialog,
    QProgressBar,
    QListWidget,
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5 import uic
import scipy.io
import os

# -- CUSTOM --------------------- #
from utilities.path_utils import resource_path
from utilities.path_utils import base_path


# ---------------- Worker that runs in a background thread ----------------
class ImportWorker(QObject):
    progress = pyqtSignal(int, int, str)
    fileImported = pyqtSignal(dict)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self, paths):
        super().__init__()
        self._paths = list(paths)
        self._cancel = False

    @pyqtSlot()
    def run(self):
        results = []
        total = len(self._paths)
        for i, path in enumerate(self._paths):
            if self._cancel:
                self.finished.emit(results)
                return
            try:
                self.progress.emit(i, total, os.path.basename(path))
                mat = scipy.io.loadmat(path, struct_as_record=False, squeeze_me=True)
                key = next((k for k in mat.keys() if not k.startswith("__")), None)
                if key:
                    tl = mat[key]
                    results.append({
                        "path": path,
                        "data": tl.Analog.Data,
                        "labels": tl.Analog.Labels,
                    })
            except Exception as e:
                self.error.emit(f"{os.path.basename(path)}: {e}")
        self.finished.emit(results)

    @pyqtSlot()
    def cancel(self):
        self._cancel = True


# ---------------- Your dialog class ----------------
class LoadMat(QDialog):
    matsImported = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        ui_path = os.path.join(base_path("uis", "loadMat.ui"))
        uic.loadUi(ui_path, self)

        self.setWindowIcon(QIcon(resource_path("icons", "icn_matlab.png")))
        # Set minimum width to accommodate larger button text
        self.setMinimumWidth(720)
        self.paths = []

        # Increase font sizes for better readability
        self._increase_font_sizes()

        # Buttons
        self.btnSelectFiles.clicked.connect(lambda: self.select_files("*.mat"))
        self.btnImport.clicked.connect(self.on_import_clicked)
        self.btnClose.clicked.connect(self.close_dialog)
        self.btnClear.clicked.connect(self.clear_list)
        self.btnRemoveSelected.clicked.connect(self.remove_selected_files)  # NEW

        # Enable multi-selection for Ctrl/Shift delete
        self.listFiles.setSelectionMode(QListWidget.ExtendedSelection)

        # Enable drag & drop
        self.listFiles.setAcceptDrops(True)
        self.listFiles.dragEnterEvent = self.dragEnterEvent
        self.listFiles.dropEvent = self.dropEvent

        # Worker/thread holders
        self._thread = None
        self._worker = None
        self._progress = None

    # ---------------------- FONT SIZE INCREASE ----------------------
    def _increase_font_sizes(self):
        """Increase font sizes for all UI elements in the dialog."""
        # Increase button font sizes to 11pt
        button_font_size = 11
        for button in [self.btnSelectFiles, self.btnImport, self.btnClose, 
                      self.btnClear, self.btnRemoveSelected]:
            if button:
                font = button.font()
                font.setPointSize(button_font_size)
                button.setFont(font)
        
        # Increase list widget font size to 12pt for better readability
        if self.listFiles:
            font = self.listFiles.font()
            font.setPointSize(12)
            self.listFiles.setFont(font)
        
        # Increase progress dialog label font size (will be applied when dialog is created)
        # This is handled in _ensure_progress_dialog

    # ---------------------- CLEAR BUTTON ----------------------
    def clear_list(self):
        self.paths = []
        self.listFiles.clear()
        QMessageBox.information(self, "Cleared", "File list has been cleared.")

    # ---------------------- REMOVE SELECTED -------------------
    def remove_selected_files(self):
        selected = self.listFiles.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Select items to remove.")
            return

        for item in selected:
            path = item.text()
            if path in self.paths:
                self.paths.remove(path)
            self.listFiles.takeItem(self.listFiles.row(item))

    # ---------------------- DRAG & DROP SUPPORT -------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        new_files = []

        for url in urls:
            file_path = url.toLocalFile()
            if file_path.lower().endswith(".mat"):
                new_files.append(file_path)

        if not new_files:
            QMessageBox.warning(self, "Unsupported", "Only .mat files are allowed.")
            return

        self.paths.extend(new_files)

        for path in new_files:
            item = QListWidgetItem(path)
            item.setToolTip(path)
            # Set larger font for file names
            font = item.font()
            font.setPointSize(13)
            item.setFont(font)
            self.listFiles.addItem(item)

    # ------------------- FILE SELECTION ------------------------
    def select_files(self, file_extension):
        files, _ = QFileDialog.getOpenFileNames(self, "Open", "", file_extension)
        if files:
            self.paths = files
            self.listFiles.clear()
            for path in files:
                item = QListWidgetItem(path)
                item.setToolTip(path)
                # Set larger font for file names
                font = item.font()
                font.setPointSize(12)
                item.setFont(font)
                self.listFiles.addItem(item)

            self.listFiles.setWordWrap(False)
            self.listFiles.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.listFiles.setUniformItemSizes(True)

    # ------------------- PROGRESS DIALOG ------------------------
    def _ensure_progress_dialog(self, total):
        dlg = QProgressDialog("Importing MAT files...", "Cancel", 0, total, self)
        dlg.setWindowTitle("Import")
        dlg.setWindowModality(Qt.WindowModal)
        dlg.setAutoClose(False)
        dlg.setAutoReset(False)
        dlg.setMinimumDuration(0)
        dlg.setValue(0)
        # Make the progress dialog wider so the progress bar is easier to see
        dlg.setMinimumWidth(500)

        bar = dlg.findChild(QProgressBar)
        if bar:
            bar.setTextVisible(True)
            bar.setFormat("%p%")
            # Increase progress bar font size
            font = bar.font()
            font.setPointSize(11)
            bar.setFont(font)
        
        # Increase progress dialog label font size
        # Find the label in the progress dialog
        from PyQt5.QtWidgets import QLabel
        labels = dlg.findChildren(QLabel)
        for label in labels:
            font = label.font()
            font.setPointSize(11)
            label.setFont(font)
        
        dlg.show()
        QCoreApplication.processEvents()
        return dlg

    @pyqtSlot()
    def on_import_clicked(self):
        if not self.paths:
            QMessageBox.warning(self, "No files", "Please select MAT files first.")
            return

        self._progress = self._ensure_progress_dialog(len(self.paths))

        self._thread = QThread(self)
        self._worker = ImportWorker(self.paths)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_worker_progress)
        self._worker.error.connect(self._on_worker_error)
        self._worker.finished.connect(self._on_worker_finished)

        self._progress.canceled.connect(self._worker.cancel)

        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    @pyqtSlot(int, int, str)
    def _on_worker_progress(self, i, total, name):
        if self._progress:
            self._progress.setLabelText(f"Importing: {name} ({i+1}/{total})")
            self._progress.setMaximum(total)
            self._progress.setValue(i)
            QCoreApplication.processEvents()

    @pyqtSlot(str)
    def _on_worker_error(self, msg):
        QMessageBox.warning(self, "Import error", msg)

    @pyqtSlot(list)
    def _on_worker_finished(self, results):
        if self._progress:
            self._progress.setValue(self._progress.maximum())
            self._progress.close()
            self._progress = None

        if results:
            self.matsImported.emit(results)
            QMessageBox.information(
                self,
                "Import complete",
                f"Imported {len(results)} file(s) successfully.",
            )
            self.accept()
        else:
            QMessageBox.information(self, "Import", "No files were imported.")

    def close_dialog(self):
        if self._worker and self._thread and self._thread.isRunning():
            self._worker.cancel()
        self.reject()
