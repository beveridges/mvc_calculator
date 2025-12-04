# ui_initializer.py

from PyQt5.QtWidgets import QAction, QLabel
from PyQt5.QtGui import QKeySequence, QIcon, QPixmap, QCursor, QMouseEvent
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5 import uic

# -- CUSTOM ---------------------
from plot_controller import PlotController
from utilities.path_utils import base_path, resource_path


class UIInitializer:
    def __init__(self, main_window, plot_controller):
        self.main_window = main_window
        self.plot_controller = plot_controller
        self.main_window.plot_controller = plot_controller
        self.setup_ui()

    def setup_ui(self):
        uic.loadUi(base_path("uis", "main.ui"), self.main_window)

        mw = self.main_window

        # Menus
        mw.file_menu = mw.menuBar().addMenu("&File")
        mw.help_menu = mw.menuBar().addMenu("&Help")
        mw.menuBar().setStyleSheet("font-size: 10pt; font-family: 'Helvetica';")

        # File Actions
        mw.load_MAT_action = QAction("&Import MAT files")
        mw.importXMLmot_action = QAction("&Import XML file")
        mw.exportXMLmot_action = QAction("&Export XML file")
        mw.exitAction = QAction("&Exit")
        
        mw.aboutAction = QAction("&About")
        mw.indexAction = QAction("&Documentation")
        mw.licenseInfoAction = QAction("&Request License...")

        mw.file_menu.addAction(mw.load_MAT_action)
        mw.file_menu.addAction(mw.importXMLmot_action)
        mw.file_menu.addSeparator()
        mw.file_menu.addAction(mw.exportXMLmot_action) 
        mw.file_menu.addSeparator()
        mw.file_menu.addAction(mw.exitAction)
        
        mw.help_menu.addAction(mw.aboutAction)
        mw.help_menu.addSeparator()
        mw.help_menu.addAction(mw.licenseInfoAction)
        mw.help_menu.addAction(mw.indexAction)

        mw.load_MAT_action.setShortcut(QKeySequence("Ctrl+L"))
        mw.importXMLmot_action.setShortcut(QKeySequence("Ctrl+X"))
        mw.exportXMLmot_action.setShortcut(QKeySequence("Ctrl+E"))
        mw.exitAction.setShortcut(QKeySequence("Ctrl+Q"))

        mw.load_MAT_action.triggered.connect(mw.load_mat_files)
        mw.importXMLmot_action.triggered.connect(mw.import_mvc_xml)
        mw.exportXMLmot_action.triggered.connect(mw.export_mvc_xml)
        mw.exitAction.triggered.connect(mw.close)
        
        mw.aboutAction.triggered.connect(mw.launch_about)
        mw.licenseInfoAction.triggered.connect(mw.show_license_info)
        mw.indexAction.triggered.connect(mw.launch_help)

        # Set moviolabs logo image (Qt resource system not used, so set directly)
        moviolabs_label = mw.findChild(QLabel, "lbl_moviolabs_url")
        if moviolabs_label:
            img_path = resource_path("icons", "moviolabs_TINY.png")
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                # Set the pixmap directly
                moviolabs_label.setPixmap(pixmap)
                moviolabs_label.setAlignment(Qt.AlignCenter)
                # Make it clickable - override mousePressEvent
                original_mousePressEvent = moviolabs_label.mousePressEvent
                def click_handler(event: QMouseEvent):
                    if event.button() == Qt.LeftButton:
                        QDesktopServices.openUrl(QUrl("https://www.moviolabs.com"))
                    else:
                        original_mousePressEvent(event)
                moviolabs_label.mousePressEvent = click_handler
                moviolabs_label.setCursor(QCursor(Qt.PointingHandCursor))
            else:
                # Fallback: just set the link text if image not found
                moviolabs_label.setText('<a href="https://www.moviolabs.com">moviolabs.com</a>')
                moviolabs_label.setOpenExternalLinks(True)

        # mw.importDOTmot_action.triggered.connect(
        #     lambda: mw.plot_controller.load_dot_mot())


def setup(main_window, plot_controller):
    ui = UIInitializer(main_window, plot_controller)
    return ui
