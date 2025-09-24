# -*- coding: utf-8 -*-
# utilities/plot_controller.py

"""
PlotController
--------------
Owns the Matplotlib canvas embedded in a Qt container and draws:
- the MOT data trace
- the “upper” (arriba) coloured bands + red line
- the “lower” (abajo) coloured bands + red line

This file **does not** wire unrelated app buttons. It only connects
signals that affect the plot and the band widgets that live on the
same tab.
"""

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.patches as patches
import pandas as pd

from PyQt5.QtCore import QSignalBlocker
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QVBoxLayout


class PlotController:
    def __init__(self, parent=None, container=None, main_window=None):
        self.parent = parent
        self.main_window = main_window

        fig = Figure(figsize=(5, 4))
        self.ax = fig.add_subplot(111)
        self.canvas = FigureCanvas(fig)
        self.toolbar = NavigationToolbar(self.canvas, container)

        # # Ensure canvas+toolbar are added to the container layout
        # if container.layout() is None:
            # layout = QVBoxLayout(container)
            # layout.addWidget(self.toolbar)
            # layout.addWidget(self.canvas)
        # else:
            # container.layout().addWidget(self.toolbar)
            # container.layout().addWidget(self.canvas)

        # self.canvas.setVisible(False)
        # self.toolbar.setVisible(False)

        # # runtime state
        # self.mot_data = None
        # self.x_min = None
        # self.x_max = None
        # self.SAVE_INITIAL_minnX = None
        # self.SAVE_INITIAL_maxxX = None
        # self.SAVE_INITIAL_minnY = None
        # self.SAVE_INITIAL_maxxY = None

        # # convenience
        # self.overlays_alpha = 0.35  # use same alpha for top/bottom so colours match

    # @property
    # def mw(self):
        # return self.main_window
    
    
    # # ---------- Axis spinboxes → apply ----------
    # def apply_x_limits(self):
        # x_min = self.mw.dsb_x_axis_min.value()
        # x_max = self.mw.dsb_x_axis_max.value()
        # self.set_x_limits(x_min, x_max)

    # def apply_y_limits(self):
        # y_min = self.mw.dsb_y_axis_min.value()
        # y_max = self.mw.dsb_y_axis_max.value()
        # self.set_y_limits(y_min, y_max)
        # if self.mw.tgl_arriba_rDa.isChecked():
            # self.rango_de_articulacion_arriba_limite()
        # if self.mw.tgl_abajo_rDa.isChecked():
            # self.rango_de_articulacion_abajo_limite()

    # def bind_ui_controls(self):
        # mw = self.mw

        # # Column selector → replot
        # mw.cbx_imported_mot_y.currentTextChanged.connect(
            # self.plot_spinbox_changed)

        # # Title + legend text/size
        # mw.led_titulo_text.textEdited.connect(
            # lambda: self.set_title(
                # mw.led_titulo_text.text(), mw.spb_titulo_text_size.value())
        # )
        # mw.spb_titulo_text_size.valueChanged.connect(
            # lambda: self.set_title(
                # mw.led_titulo_text.text(), mw.spb_titulo_text_size.value())
        # )
        # mw.led_legend_text.textEdited.connect(
            # lambda: self.set_legend(
                # mw.led_legend_text.text(), mw.spb_legend_text_size.value())
        # )
        # mw.spb_legend_text_size.valueChanged.connect(
            # lambda: self.set_legend(
                # mw.led_legend_text.text(), mw.spb_legend_text_size.value())
        # )

        # # Styling
        # mw.spb_thickness_of_line.valueChanged.connect(
            # lambda: self.set_line_thickness(mw.spb_thickness_of_line.value())
        # )
        # mw.spb_label_size.valueChanged.connect(
            # lambda: self.set_label_font_size(mw.spb_label_size.value())
        # )
        # mw.spb_tick_size.valueChanged.connect(
            # lambda: self.set_tick_font_size(mw.spb_tick_size.value())
        # )

        # # Axis spinboxes
        # mw.dsb_x_axis_min.valueChanged.connect(self.apply_x_limits)
        # mw.dsb_x_axis_max.valueChanged.connect(self.apply_x_limits)
        # mw.dsb_y_axis_min.valueChanged.connect(self.apply_y_limits)
        # mw.dsb_y_axis_max.valueChanged.connect(self.apply_y_limits)

        # # Reset axis
        # mw.btn_reset_x_axis.clicked.connect(self.reset_x_axis)
        # mw.btn_reset_y_axis.clicked.connect(self.reset_y_axis)

        # # Upper range spinboxes + toggle + reset
        # mw.RdAa_min.valueChanged.connect(self.update_RdAa_limite_bounds)
        # mw.RdAa_max.valueChanged.connect(self.update_RdAa_limite_bounds)
        # mw.RdAa_limite.valueChanged.connect(
            # self.rango_de_articulacion_arriba_limite)
        # mw.tgl_arriba_rDa.toggled.connect(self.toggle_upper_overlay)
        
        # mw.btn_reset_arriba.clicked.connect(self.reset_rdaa_defaults)
        # mw.btn_reset_abajo.clicked.connect(self.reset_rdaab_defaults)

        # # Lower range spinboxes + toggle
        # mw.RdAaB_min.valueChanged.connect(self.update_RdAaB_limite_bounds)
        # mw.RdAaB_max.valueChanged.connect(self.update_RdAaB_limite_bounds)
        # mw.RdAaB_limite.valueChanged.connect(
            # self.rango_de_articulacion_abajo_limite)
        # mw.tgl_abajo_rDa.toggled.connect(self.toggle_lower_overlay)

        # mw.dsb_y_axis_max.valueChanged.connect(
            # lambda v: mw.RdAa_max.setValue(v))
        # mw.RdAa_max.valueChanged.connect(
            # lambda v: mw.dsb_y_axis_max.setValue(v))

        # mw.dsb_y_axis_min.valueChanged.connect(
            # lambda v: mw.RdAaB_min.setValue(v))
        # mw.RdAaB_min.valueChanged.connect(
            # lambda v: mw.dsb_y_axis_min.setValue(v))
        
        
        


    # # ---------- Init / enable UI ----------
    # def initialize_graph_sizes(self):
        # self.mw.spb_thickness_of_line.setMaximum(6)
        # self.mw.spb_thickness_of_line.setMinimum(1)
        # self.mw.spb_thickness_of_line.setValue(2)

    # def initialize_plotting_widgets(self):
        # for gb in [
            # "_graficando_variables_",
            # "_graficando_tab_",
            # "_limites_de_eje_",
            # "_limites_de_rango_",
        # ]:
            # if hasattr(self.mw, gb):
                # getattr(self.mw, gb).setEnabled(True)
                # getattr(self.mw, gb).setStyleSheet(
                    # "QGroupBox::title{ color: black}")

    # def load_dot_mot(self):
        # file_path, _ = QFileDialog.getOpenFileName(
            # self.mw, "Seleccionar archivo MOT", "", "Archivos MOT (*.mot)"
        # )
        # if file_path:
            # self.load_and_prepare_mot_file(file_path)

    # def load_and_prepare_mot_file(self, path):
        # try:
            # # Avoid pandas regex warning by using engine='python'
            # df = pd.read_csv(path, skiprows=6, sep=r'\t+', engine='python')
        # except Exception as e:
            # QMessageBox.critical(
                # self.mw, "Error", f"No se pudo leer el archivo:\n{e}")
            # return

        # self.mot_data = df

        # # enable the whole tab & groups
        # self.initialize_plotting_widgets()
        # self.initialize_graph_sizes()

        # # Populate Y column combo (ignore 'time')
        # valid_cols = [c for c in df.columns if c.lower() !=
                      # "time" and df[c].notna().any()]
        # if not valid_cols:
            # QMessageBox.warning(self.mw, "Archivo inválido",
                                # "El archivo MOT no contiene datos válidos para graficar.")
            # return

        # cbx = self.mw.cbx_imported_mot_y
        # blocker = QSignalBlocker(cbx)
        # cbx.clear()
        # cbx.addItems(sorted(valid_cols))
        # del blocker
        # cbx.setCurrentIndex(0)

        # # First plot
        # self.plot_mot(df, cbx.currentText())
        # self.canvas.setVisible(True)
        # self.toolbar.setVisible(True)



    # # ---------- Core plotting ----------
    # def plot_mot(self, df: pd.DataFrame, y_col: str):
        # self.ax.clear()

        # # X range
        # x = df["time"] if "time" in df.columns else df.index
        # y = df[y_col].astype(float)
        # self.ax.plot(x, y, linewidth=self.mw.spb_thickness_of_line.value())

        # # Save initial limits (for Reset buttons)
        # self.SAVE_INITIAL_minnX, self.SAVE_INITIAL_maxxX = self.ax.get_xlim()
        # self.SAVE_INITIAL_minnY, self.SAVE_INITIAL_maxxY = self.ax.get_ylim()

        # # Update spinboxes to reflect the plotted range
        # self.update_axis_limit_widgets()

        # # Compute defaults for **upper** band = top 2/5 of Y
        # y_min, y_max = self.SAVE_INITIAL_minnY, self.SAVE_INITIAL_maxxY
        # y_rng = y_max - y_min if y_max > y_min else 1.0

        # rdaa_min = y_max - (2.0/5.0) * y_rng
        # rdaa_lim = (y_max + rdaa_min) / 2.0

        # self.mw.RdAa_max.setValue(y_max)
        # self.mw.RdAa_min.setValue(rdaa_min)
        # self.mw.RdAa_limite.setValue(rdaa_lim)

        # # Defaults for **lower** band = bottom 2/5 of Y
        # rdaab_max = y_min + (2.0/5.0) * y_rng
        # rdaab_lim = (y_min + rdaab_max) / 2.0

        # self.mw.RdAaB_min.setValue(y_min)
        # self.mw.RdAaB_max.setValue(rdaab_max)
        # self.mw.RdAaB_limite.setValue(rdaab_lim)

        # # Draw overlays if toggles are on
        # if self.mw.tgl_arriba_rDa.isChecked():
            # self.rango_de_articulacion_arriba_limite()
        # if self.mw.tgl_abajo_rDa.isChecked():
            # self.rango_de_articulacion_abajo_limite()

        # # Titles / legend / grid
        # self.mw.led_titulo_text.setText(y_col)
        # self.mw.led_legend_text.setText(y_col)
        # self.reapply_plot_settings()
        # self.canvas.draw_idle()

    # def plot_spinbox_changed(self):
        # col = self.mw.cbx_imported_mot_y.currentText()
        # if not col or self.mot_data is None or col not in self.mot_data.columns:
            # return
        # self.plot_mot(self.mot_data, col)

    # # ---------- Overlays (upper) ----------
    # def toggle_upper_overlay(self, checked: bool):
        # if checked:
            # self.rango_de_articulacion_arriba_limite()
        # else:
            # self.remove_overlay_by_name("arriba")
            # self.canvas.draw_idle()

    # def rango_de_articulacion_arriba_limite(self):
        # if self.mot_data is None:
            # return

        # y_min = self.mw.dsb_y_axis_min.value()
        # y_max = self.mw.dsb_y_axis_max.value()

        # rdaa_min = self.mw.RdAa_min.value()
        # rdaa_lim = self.mw.RdAa_limite.value()

        # if not (y_min < rdaa_min < y_max) or not (y_min < rdaa_lim < y_max) or not (rdaa_min < rdaa_lim):
            # return

        # self.clear_limit_overlays("arriba")

        # # Orange (top) band: limite → y_max
        # top_patch = self.ax.axhspan(rdaa_lim, y_max, xmin=0, xmax=1,
                                    # facecolor="#ffa836", alpha=self.overlays_alpha, zorder=0)
        # top_patch.set_gid("overlay_arriba_orange")

        # # Yellow (middle) band: rdaa_min → limite
        # mid_patch = self.ax.axhspan(rdaa_min, rdaa_lim, xmin=0, xmax=1,
                                    # facecolor="#ffe060", alpha=self.overlays_alpha, zorder=0)
        # mid_patch.set_gid("overlay_arriba_yellow")

        # # Red line at limite
        # red = self.ax.axhline(rdaa_lim, color="red", linewidth=2.0, zorder=1)
        # red.set_gid("overlay_arriba_line")

        # self.canvas.draw_idle()

    # # ---------- Overlays (lower) ----------
    # def toggle_lower_overlay(self, checked: bool):
        # if checked:
            # self.rango_de_articulacion_abajo_limite()
        # else:
            # self.remove_overlay_by_name("abajo")
            # self.canvas.draw_idle()

    # def rango_de_articulacion_abajo_limite(self):
        # if self.mot_data is None:
            # return

        # y_min = self.mw.RdAaB_min.value()
        # y_max = self.mw.RdAaB_max.value()
        # limite = self.mw.RdAaB_limite.value()

        # if not (y_min < limite < y_max):
            # return

        # self.clear_limit_overlays("abajo")

        # # Orange bottom band: y_min → limite
        # bot_orange = self.ax.axhspan(y_min, limite, xmin=0, xmax=1,
                                     # facecolor="#ffa836", alpha=self.overlays_alpha, zorder=0)
        # bot_orange.set_gid("overlay_abajo_orange")

        # # Yellow second band: limite → y_max
        # bot_yellow = self.ax.axhspan(limite, y_max, xmin=0, xmax=1,
                                     # facecolor="#ffe060", alpha=self.overlays_alpha, zorder=0)
        # bot_yellow.set_gid("overlay_abajo_yellow")

        # # Red line
        # red = self.ax.axhline(limite, color="red", linewidth=2.0, zorder=1)
        # red.set_gid("overlay_abajo_line")

        # self.canvas.draw_idle()

    # # ---------- Overlay cleanup ----------
    # def clear_limit_overlays(self, overlay_name=None):
        # def gid_of(o):
            # return getattr(o, "get_gid", lambda: None)() or getattr(o, "gid", None)

        # for line in list(self.ax.lines):
            # gid = gid_of(line)
            # if gid and gid.startswith(f"overlay_{overlay_name}_"):
                # line.remove()

        # for patch in list(self.ax.patches):
            # gid = gid_of(patch)
            # if gid and gid.startswith(f"overlay_{overlay_name}_"):
                # patch.remove()

    # def remove_overlay_by_name(self, name: str):
        # self.clear_limit_overlays(name)

    # # ---------- Resets ----------
    # def reset_rdaa_defaults(self):
        # # recompute from current Y spinboxes (top 2/5)
        # y_min = self.mw.dsb_y_axis_min.value()
        # y_max = self.mw.dsb_y_axis_max.value()
        # rng = max(y_max - y_min, 1e-9)
        # rdaa_min = y_max - (2.0/5.0) * rng
        # rdaa_lim = (y_max + rdaa_min) / 2.0
        # self.mw.RdAa_max.setValue(y_max)
        # self.mw.RdAa_min.setValue(rdaa_min)
        # self.mw.RdAa_limite.setValue(rdaa_lim)
        # if self.mw.tgl_arriba_rDa.isChecked():
            # self.rango_de_articulacion_arriba_limite()
            
            
    # def reset_rdaab_defaults(self):
        # # Recompute lower defaults from current Y-axis limits (bottom 2/5)
        # y_min = self.mw.dsb_y_axis_min.value()
        # y_max = self.mw.dsb_y_axis_max.value()
        # rng = max(y_max - y_min, 1e-9)
    
        # rdaab_max = y_min + (2.0/5.0) * rng
        # rdaab_lim = (y_min + rdaab_max) / 2.0
    
        # # Update spinboxes
        # self.mw.RdAaB_min.setValue(y_min)
        # self.mw.RdAaB_max.setValue(rdaab_max)
        # self.mw.RdAaB_limite.setValue(rdaab_lim)
    
        # # Redraw overlays if toggle is on
        # if self.mw.tgl_abajo_rDa.isChecked():
            # self.rango_de_articulacion_abajo_limite()

            
            
    

    # def reset_x_axis(self):
        # if self.SAVE_INITIAL_minnX is None or self.SAVE_INITIAL_maxxX is None:
            # return
        # x_min = min(self.SAVE_INITIAL_minnX, self.SAVE_INITIAL_maxxX)
        # x_max = max(self.SAVE_INITIAL_minnX, self.SAVE_INITIAL_maxxX)
        # self.ax.set_xlim(x_min, x_max)
        # self.mw.dsb_x_axis_min.setValue(x_min)
        # self.mw.dsb_x_axis_max.setValue(x_max)
        # self.canvas.draw_idle()

    # def reset_y_axis(self):
        # if self.SAVE_INITIAL_minnY is None or self.SAVE_INITIAL_maxxY is None:
            # return
        # y_min = min(self.SAVE_INITIAL_minnY, self.SAVE_INITIAL_maxxY)
        # y_max = max(self.SAVE_INITIAL_minnY, self.SAVE_INITIAL_maxxY)
        # self.ax.set_ylim(y_min, y_max)
        # self.mw.dsb_y_axis_min.setValue(y_min)
        # self.mw.dsb_y_axis_max.setValue(y_max)
        # self.canvas.draw_idle()
        # if self.mw.tgl_arriba_rDa.isChecked():
            # self.rango_de_articulacion_arriba_limite()
        # if self.mw.tgl_abajo_rDa.isChecked():
            # self.rango_de_articulacion_abajo_limite()





    # # ---------- Styling ----------
    # def reapply_plot_settings(self):
        # self.ax.set_xlabel(
            # "Tiempo (s)", fontsize=self.mw.spb_label_size.value())
        # self.ax.set_ylabel(
            # "Grados (°)", fontsize=self.mw.spb_label_size.value())
        # self.ax.tick_params(
            # axis='both', labelsize=self.mw.spb_tick_size.value())

        # leg_text = self.mw.led_legend_text.text().strip(
        # ) or self.mw.cbx_imported_mot_y.currentText()
        # self.ax.legend(
            # [leg_text], fontsize=self.mw.spb_legend_text_size.value(), loc='upper right')

        # title_text = self.mw.led_titulo_text.text().strip(
        # ) or self.mw.cbx_imported_mot_y.currentText()
        # self.ax.set_title(
            # title_text, fontsize=self.mw.spb_titulo_text_size.value())

        # self.ax.grid(True)



    # # ---------- Simple setters ----------
    # def set_title(self, text: str, size: int):
        # self.ax.set_title(text, fontsize=size)
        # self.canvas.draw_idle()

    # def set_legend(self, text: str, size: int):
        # self.ax.legend([text], fontsize=size, loc='upper right')
        # self.canvas.draw_idle()

    # def set_line_thickness(self, thickness: float):
        # if self.ax.lines:
            # self.ax.lines[0].set_linewidth(thickness)
            # self.canvas.draw_idle()

    # def set_label_font_size(self, size: int):
        # self.ax.set_xlabel(self.ax.get_xlabel(), fontsize=size)
        # self.ax.set_ylabel(self.ax.get_ylabel(), fontsize=size)
        # self.canvas.draw_idle()

    # def set_tick_font_size(self, size: int):
        # self.ax.tick_params(axis='both', labelsize=size)
        # self.canvas.draw_idle()

    # def set_x_limits(self, x_min, x_max):
        # self.ax.set_xlim(x_min, x_max)
        # self.canvas.draw_idle()

    # def set_y_limits(self, y_min, y_max):
        # self.ax.set_ylim(y_min, y_max)
        # self.canvas.draw_idle()


    # def update_axis_limit_widgets(self):
        # x_min, x_max = self.ax.get_xlim()
        # y_min, y_max = self.ax.get_ylim()
        # self.mw.dsb_x_axis_min.setValue(x_min)
        # self.mw.dsb_x_axis_max.setValue(x_max)
        # self.mw.dsb_y_axis_min.setValue(y_min)
        # self.mw.dsb_y_axis_max.setValue(y_max)
        
    # # ---------- Keep limite inside its bounds ----------
    # def update_RdAa_limite_bounds(self):
        # min_val = self.mw.RdAa_min.value()
        # max_val = self.mw.RdAa_max.value()
        # if min_val >= max_val:
            # return
        # cur = self.mw.RdAa_limite.value()
        # self.mw.RdAa_limite.blockSignals(True)
        # self.mw.RdAa_limite.setMinimum(min_val)
        # self.mw.RdAa_limite.setMaximum(max_val)
        # if cur < min_val or cur > max_val:
            # self.mw.RdAa_limite.setValue((min_val + max_val) / 2.0)
        # self.mw.RdAa_limite.blockSignals(False)
        # if self.mw.tgl_arriba_rDa.isChecked():
            # self.rango_de_articulacion_arriba_limite()

    # def update_RdAaB_limite_bounds(self):
        # min_val = self.mw.RdAaB_min.value()
        # max_val = self.mw.RdAaB_max.value()
        # if min_val >= max_val:
            # return
        # cur = self.mw.RdAaB_limite.value()
        # self.mw.RdAaB_limite.blockSignals(True)
        # self.mw.RdAaB_limite.setMinimum(min_val)
        # self.mw.RdAaB_limite.setMaximum(max_val)
        # if cur < min_val or cur > max_val:
            # self.mw.RdAaB_limite.setValue((min_val + max_val) / 2.0)
        # self.mw.RdAaB_limite.blockSignals(False)
        # if self.mw.tgl_abajo_rDa.isChecked():
            # self.rango_de_articulacion_abajo_limite()