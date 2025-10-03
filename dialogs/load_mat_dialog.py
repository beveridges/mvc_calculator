# load_mat_dialog.py (top imports)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QThread, QObject, QCoreApplication
from PyQt5.QtWidgets import QDialog, QFileDialog, QListWidgetItem, QMessageBox, QProgressDialog, QProgressBar, QPushButton, QListWidget
from PyQt5.QtGui import QIcon
from PyQt5 import uic
import scipy.io
import os



# -- CUSTOM --------------------- # 
from utilities.path_utils import resource_path 
from utilities.path_utils import base_path

# ---------------- Worker that runs in a background thread ----------------
class ImportWorker(QObject):
    progress = pyqtSignal(int, int, str)     # current, total, filename
    fileImported = pyqtSignal(dict)          # emits each parsed {path, data, labels}
    finished = pyqtSignal(list)              # emits final list
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
                # --- heavy work here (off GUI thread) ---
                mat = scipy.io.loadmat(path, struct_as_record=False, squeeze_me=True)
                key = next((k for k in mat.keys() if not k.startswith("__")), None)
                if key:
                    tl = mat[key]
                    results.append({
                        "path": path,
                        "data": tl.Analog.Data,
                        "labels": tl.Analog.Labels
                    })
            except Exception as e:
                self.error.emit(f"{os.path.basename(path)}: {e}")
                # keep going to next file
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
        self.setWindowIcon(QIcon(resource_path('icons', 'icn_matlab.png')))
        self.paths = []
        self.btnSelectFiles.clicked.connect(lambda: self.select_files("*.mat"))
        self.btnImport.clicked.connect(self.on_import_clicked)
        self.btnClose.clicked.connect(self.close_dialog)

        # keep references so they don’t get GC’d
        self._thread = None
        self._worker = None
        self._progress = None

    def select_files(self, file_extension):
        files, _ = QFileDialog.getOpenFileNames(self, "Open", "", file_extension)
        if files:
            self.paths = files
            self.listFiles.clear()
            for path in files:
                item = QListWidgetItem(path)   # <-- full path (was: os.path.basename(path))
                item.setToolTip(path)          # keep tooltip too
                self.listFiles.addItem(item)
        
            # (optional) nicer view for long paths:
            self.listFiles.setWordWrap(False)
            self.listFiles.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.listFiles.setUniformItemSizes(True)
    
    def _ensure_progress_dialog(self, total):
        # Make sure the dialog paints immediately and shows a proper bar at 0%
        dlg = QProgressDialog("Importing MAT files...", "Cancel", 0, total, self)
        dlg.setWindowTitle("Import")
        dlg.setWindowModality(Qt.WindowModal)
        dlg.setAutoClose(False)     # we’ll close explicitly on finish
        dlg.setAutoReset(False)
        dlg.setMinimumDuration(0)   # show immediately (no delay threshold)
        dlg.setValue(0)
        
        dlg.setMinimumWidth(400)
        dlg.setSizeGripEnabled(False)
        
        # Style the embedded bar
        bar = dlg.findChild(QProgressBar)
        if bar:
            bar.setTextVisible(True)
            bar.setFormat("%p%")
            bar.setMinimumWidth(250)
            bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #555;
                    border-radius: 6px;
                    text-align: center;
                    background: #f0f0f0;
                    min-height: 18px;
                }
                QProgressBar::chunk {
                    background-color: #3daee9;
                    margin: 1px;
                }
            """)
        dlg.show()
        QCoreApplication.processEvents()  # force immediate paint
        return dlg

    @pyqtSlot()
    def on_import_clicked(self):
        if not self.paths:
            QMessageBox.warning(self, "No files", "Please select MAT files first.")
            return

        # 1) Build progress dialog up-front (no blank UI)
        self._progress = self._ensure_progress_dialog(len(self.paths))

        # 2) Spin up worker thread
        self._thread = QThread(self)
        self._worker = ImportWorker(self.paths)
        self._worker.moveToThread(self._thread)

        # 3) Wire signals
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_worker_progress)
        self._worker.fileImported.connect(lambda _: None)  # optional per-file hook
        self._worker.error.connect(self._on_worker_error)
        self._worker.finished.connect(self._on_worker_finished)

        # cancel → tell worker to stop
        self._progress.canceled.connect(self._worker.cancel)

        # ensure thread cleanup
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        # 4) Go
        self._thread.start()

    @pyqtSlot(int, int, str)
    def _on_worker_progress(self, i, total, name):
        if self._progress is None:
            return
        # Update label and step; show from 0% (no jump)
        self._progress.setLabelText(f"Importing: {name} ({i+1}/{total})")
        self._progress.setMaximum(total)
        self._progress.setValue(i)  # shows 0,1,2,... BEFORE file is appended
        QCoreApplication.processEvents()

    @pyqtSlot(str)
    def _on_worker_error(self, msg):
        # Non-blocking toast-ish message; avoid modal stalls during long runs
        # You can also collect and show once at the end if preferred.
        QMessageBox.warning(self, "Import error", msg)

    @pyqtSlot(list)
    def _on_worker_finished(self, results):
        # Step to 100% and close immediately
        if self._progress:
            self._progress.setValue(self._progress.maximum())
            self._progress.close()
            self._progress = None

        # Emit to main window → plot tabs
        if results:
            self.matsImported.emit(results)
            # This message pops instantly now (GUI thread is free)
            QMessageBox.information(self, "Import complete", f"Imported {len(results)} file(s) successfully.")
            self.accept()
        else:
            QMessageBox.information(self, "Import", "No files were imported.")
            # stay open so user can try again

    def close_dialog(self):
        # If user closes the dialog manually, try to cancel gracefully
        if self._worker and self._thread and self._thread.isRunning():
            self._worker.cancel()
        self.reject()
