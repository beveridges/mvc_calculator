# -*- coding: utf-8 -*-
# utilities/plot_controller.py

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.backend_bases import MouseButton
import numpy as np

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QRadioButton,
    QButtonGroup, QVBoxLayout, QPushButton, QSizePolicy
)


from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import QSize


from config.defaults import BEST_OF
from processors.processors import Processor

class PlotController:
    def __init__(self, parent=None, container=None, main_window=None):
        self.parent = parent
        self.main_window = main_window

        fig = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(fig)
        self.toolbar = NavigationToolbar(self.canvas, container)

        if container.layout() is None:
            layout = QVBoxLayout(container)
            layout.addWidget(self.toolbar)
            layout.addWidget(self.canvas)
        else:
            container.layout().addWidget(self.toolbar)
            container.layout().addWidget(self.canvas)

        self.canvas.setVisible(False)
        self.toolbar.setVisible(False)

        self.axes = []
        self._press_cid = None
        self._draw_cid = None
        self._active_row = 0
        self._selections = {}
        self._patches = {}
        self._overlay_items = []
        self._row_group = None
        self._data = None
        self._labels = None
        self._processor = None

        self._live_rect = None

        
        
    # def bind_ui_controls(self):
    #     """Kept for compatibility with main.py. Connect extra signals here if needed."""
    #     return


    # ============================================================
    #                        PLOTTING
    # ============================================================
    
    
    def plot_mat_arrays(self, data, labels, max_rows=6, source_path=None):
        self._data = data
        self._labels = labels
        self._source_path = source_path
    
        nrows = min(int(max_rows), int(data.shape[0]))
        npts = int(data.shape[1])
        x = np.arange(npts)
        xlim = (0, npts - 1)
    
        fig = self.canvas.figure
        fig.clear()
        axes = fig.subplots(nrows, 1, sharex=True)
        if not isinstance(axes, (list, np.ndarray)):
            axes = [axes]
        self.axes = list(axes)
    
        for i, ax in enumerate(self.axes):
            ax.plot(x, data[i, :], lw=1.0, zorder=1)
            ax.set_xlim(xlim)
            ax.autoscale(enable=False, axis='x')
            ax.relim()
            ax.autoscale_view(scalex=False, scaley=True)
            ax.grid(True, which="both", linestyle="--", alpha=0.6, zorder=0)
            ax.set_title(""); ax.set_xlabel(""); ax.set_ylabel("")
            ax.set_xticks([]); ax.set_yticks([])
    
        fig.subplots_adjust(left=0.02, right=0.985, top=0.985, bottom=0.06, hspace=0.15)
    
        # Build the overlay buttons and initialize data containers
        self._build_qt_overlays(self.axes, labels)
        self._selections = {i: [] for i in range(nrows)}
        self._patches = {i: [] for i in range(nrows)}
    
        try:
            self.toolbar.mode = ""
        except Exception:
            pass
    
        # Connect mouse handlers (your existing method)
        self._attach_mouse_handlers()
    
        # --- ✅ NEW: Bold the first row initially ---
        self._active_row = 0
        for i, ax in enumerate(self.axes):
            lw = 2.2 if i == self._active_row else 0.8
            for sp in ax.spines.values():
                sp.set_linewidth(lw)
    
        self.canvas.setVisible(True)
        self.toolbar.setVisible(True)
        self.canvas.draw_idle()

    def _attach_mouse_handlers(self):
        """Up to 'BEST_OF' spans per active row; Shift-click deletes; shows live rectangle."""
        self._click_x = None
    
        def shift_held(event):
            ge = getattr(event, "guiEvent", None)
            if ge is not None:
                try:
                    return bool(ge.modifiers() & Qt.ShiftModifier)
                except Exception:
                    pass
            key = (getattr(event, "key", "") or "").lower()
            return "shift" in key
    
        def px_to_data_x(ax, px):
            bb = ax.get_window_extent()
            if bb.width <= 0:
                return 0.0
            x0, x1 = ax.get_xlim()
            return (x1 - x0) / bb.width * px
    
        # --------------------------------------------------------------
        def on_press(event):
            if event.button != MouseButton.LEFT or event.inaxes is None:
                return
    
            # ✅ Enforce single-row selection
            if event.inaxes != self.axes[self._active_row]:
                print(f"[skip] Click ignored — not in active row ({self._active_row})")
                return
    
            row = self._active_row
    
            # --- Handle Shift+Click (delete span) ---
            if shift_held(event):
                if row not in self._selections:
                    return
                ax = self.axes[row]
                if event.xdata is None:
                    return
                x_click = float(event.xdata)
                tol = px_to_data_x(ax, 6.0)
                best_idx, best_dist = None, None
                for j, (lo, hi) in enumerate(self._selections[row]):
                    dist = 0.0 if lo <= x_click <= hi else min(abs(x_click - lo), abs(x_click - hi))
                    if dist <= tol and (best_dist is None or dist < best_dist):
                        best_idx, best_dist = j, dist
                if best_idx is not None:
                    self._patches[row][best_idx].remove()
                    self._patches[row].pop(best_idx)
                    self._selections[row].pop(best_idx)
                    self.canvas.draw_idle()
                return
    
            # --- Start new span ---
            self._click_x = event.xdata
    
            # 🟧 Remove any old live rectangle
            if self._live_rect is not None:
                try:
                    self._live_rect.remove()
                except Exception:
                    pass
                self._live_rect = None
    
            # 🟧 Create temporary rectangle for live feedback
            ax = self.axes[self._active_row]
            y0, y1 = ax.get_ylim()
            from matplotlib.patches import Rectangle
            self._live_rect = Rectangle(
                (self._click_x, y0),
                0,
                y1 - y0,
                color="orange",
                alpha=0.2,
                zorder=5
            )
            ax.add_patch(self._live_rect)
            self.canvas.draw_idle()
    
        # --------------------------------------------------------------
        def on_motion(event):
            """Update live rectangle width while dragging."""
            if self._click_x is None or self._live_rect is None:
                return
            if event.inaxes != self.axes[self._active_row] or event.xdata is None:
                return
    
            x0, x1 = self._click_x, event.xdata
            lo, hi = sorted([x0, x1])
            self._live_rect.set_x(lo)
            self._live_rect.set_width(hi - lo)
            self.canvas.draw_idle()
    
        # --------------------------------------------------------------
        def on_release(event):
            if event.button != MouseButton.LEFT or event.inaxes is None:
                return
            if self._click_x is None or event.xdata is None:
                return
    
            # ✅ Single-row enforcement again
            if event.inaxes != self.axes[self._active_row]:
                self._click_x = None
                return
    
            row = self._active_row
            lo, hi = sorted([self._click_x, event.xdata])
            if abs(hi - lo) < 1e-6:
                return
    
            # remove live rectangle
            if self._live_rect is not None:
                try:
                    self._live_rect.remove()
                except Exception:
                    pass
                self._live_rect = None
    
            if len(self._selections[row]) >= BEST_OF:
                print(f"[limit] 'BEST_OF' selections already on row {row}. Ignored.")
                self._click_x = None
                self.canvas.draw_idle()
                return
    
            ax = self.axes[row]
            patch = ax.axvspan(lo, hi, color="orange", alpha=0.3)
            self._selections[row].append((lo, hi))
            self._patches[row].append(patch)
            self._click_x = None
            self.canvas.draw_idle()
    
        # --------------------------------------------------------------
        # Safe reconnection
        if self._press_cid:
            try:
                self.canvas.mpl_disconnect(self._press_cid)
            except Exception:
                pass
        if hasattr(self, "_release_cid") and self._release_cid:
            try:
                self.canvas.mpl_disconnect(self._release_cid)
            except Exception:
                pass
        if hasattr(self, "_motion_cid") and self._motion_cid:
            try:
                self.canvas.mpl_disconnect(self._motion_cid)
            except Exception:
                pass
    
        self._press_cid = self.canvas.mpl_connect("button_press_event", on_press)
        self._release_cid = self.canvas.mpl_connect("button_release_event", on_release)
        self._motion_cid = self.canvas.mpl_connect("motion_notify_event", on_motion)

    # ============================================================
    #                CLEAR / ENERGY DETECTION
    # ============================================================

    def detect_bursts_with_energy(self, fs: int, min_silence: float = 0.080, min_sound: float = 0.200):
        if self._data is None or not self.axes:
            raise RuntimeError("No data or axes in PlotController.")

        row = int(self._active_row)
        x = self._data[row, :].astype(float).ravel()
        energy = np.abs(x) ** 2
        L = max(1, int(round(min_silence * fs)))
        b = np.ones(L, dtype=float) / L
        moving_ave = np.convolve(energy, b, mode="same")
        if moving_ave.max() > 0:
            moving_ave /= moving_ave.max()

        mask = (moving_ave >= 0.010).astype(np.uint8)
        min_sound_samples = max(1, int(round(min_sound * fs)))
        run = 0
        for i in range(len(mask)):
            if mask[i]:
                run += 1
            else:
                if 0 < run < min_sound_samples:
                    mask[i - run:i] = 0
                run = 0
        if 0 < run < min_sound_samples:
            mask[-run:] = 0

        intervals = []
        i = 0
        while i < len(mask):
            if mask[i]:
                j = i
                while j < len(mask) and mask[j]:
                    j += 1
                intervals.append((i, j))
                i = j
            else:
                i += 1

        ax = self.axes[row]
        x0, x1 = ax.get_xlim()
        for p in list(self._patches[row]):
            try: p.remove()
            except Exception: pass
        self._patches[row].clear()
        self._selections[row].clear()

        for (lo, hi) in intervals[:BEST_OF]:
            patch = ax.axvspan(lo, hi, color="orange", alpha=0.3)
            self._patches[row].append(patch)
            self._selections[row].append((lo, hi))
        ax.set_xlim(x0, x1)
        self.canvas.draw_idle()

    def clear_row_selections(self, row: int):
        if row not in self._patches or row not in self._selections:
            return
        ax = self.axes[row]
        for p in list(self._patches[row]):
            try: p.remove()
            except Exception: pass
        self._patches[row].clear()
        self._selections[row].clear()
        ax.figure.canvas.draw_idle()

    def clear_all_selections(self):
        for r in range(len(self.axes)):
            for p in self._patches.get(r, []):
                try: p.remove()
                except Exception: pass
            self._patches[r] = []
            self._selections[r] = []
        self._active_row = None
        self.canvas.draw_idle()

    # ============================================================
    #                OVERLAYS (Qt Widgets)
    # ============================================================

    def _build_qt_overlays(self, axes, labels):
        for itm in self._overlay_items:
            for key in ("widget_top", "widget_bottom"):
                try: itm[key].deleteLater()
                except Exception: pass
        self._overlay_items = []

        if self._row_group:
            try: self._row_group.idClicked.disconnect(self._on_row_clicked)
            except Exception: pass
        self._row_group = QButtonGroup(self.canvas)
        self._row_group.setExclusive(True)
        self._row_group.idClicked.connect(self._on_row_clicked)

        radio_style = """
            QRadioButton { margin: 0px; padding: 0px; }
            QRadioButton::indicator { width: 18px; height: 18px; margin: 0px; }
            QRadioButton::indicator:unchecked {
                border: 3px solid black; border-radius: 13px; background: white;
            }
            QRadioButton::indicator:checked {
                border: 3px solid black; border-radius: 13px; background: #3daee9;
            }
        """
        label_style = """
            QLabel {
                font-size: 18px; font-weight: 700; color: black;
                background: rgba(255,255,255,230);
                border-radius: 6px; padding: 2px 10px;
            }
        """

        for i, ax in enumerate(axes):
            w_top = QWidget(self.canvas)
            w_top.setAttribute(Qt.WA_NoSystemBackground, True)
            w_top.setAttribute(Qt.WA_TranslucentBackground, True)
            w_top.setStyleSheet("background: transparent;")
            lay_top = QHBoxLayout(w_top)
            lay_top.setContentsMargins(8, 4, 0, 4)
            lay_top.setSpacing(6)

            label_text = str(labels[i]) if labels is not None and len(labels) > i else f"EMG {i+1}"
            lbl = QLabel(label_text, w_top)
            lbl.setStyleSheet(label_style)

            rdo = QRadioButton(w_top)
            rdo.setStyleSheet(radio_style)
            rdo.setChecked(i == 0)
            self._row_group.addButton(rdo, i)

            lay_top.addWidget(lbl, 1)
            lay_top.addWidget(rdo, 0, alignment=Qt.AlignRight | Qt.AlignTop)

            w_bottom = QWidget(self.canvas)
            w_bottom.setAttribute(Qt.WA_NoSystemBackground, True)
            w_bottom.setAttribute(Qt.WA_TranslucentBackground, True)
            lay_bottom = QHBoxLayout(w_bottom)
            lay_bottom.setContentsMargins(0, 0, 0, 0)
            lay_bottom.setSpacing(0)
            
            from PyQt5.QtGui import QPixmap, QIcon
            from PyQt5.QtCore import QSize
            
            btn_clear = QPushButton(w_bottom)
            btn_clear.setFixedSize(30, 30)  # 🔹 slightly larger than 24×24 radio
            btn_clear.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            
            # --- Load and scale the broom PNG properly ---
            pixmap = QPixmap("resources/icons/icn_broom.png")
            # scale to fill the button but preserve aspect ratio
            scaled = pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon = QIcon(scaled)
            btn_clear.setIcon(icon)
            btn_clear.setIconSize(QSize(28, 28))  # 🔹 ensure icon fills almost entire button
            
            # --- Button styling ---
            btn_clear.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: transparent;
                }
                QPushButton:pressed {
                    background-color: #f4a742;
                }
            """)
            
            btn_clear.setToolTip("Clear selections for this row")
            btn_clear.clicked.connect(lambda _, r=i: self.clear_row_selections(r))
            lay_bottom.addStretch(1)
            lay_bottom.addWidget(btn_clear, 0, alignment=Qt.AlignRight | Qt.AlignBottom)




            # btn_clear = QPushButton(w_bottom)
            # btn_clear.setFixedSize(40, 40)
            # btn_clear.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            
            # # --- Force proper scaling and sharp rendering ---
            # pixmap = QPixmap("resources/icons/icn_broom.png")
            # scaled = pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # icon = QIcon()
            # icon.addPixmap(scaled, QIcon.Normal, QIcon.Off)
            
            # btn_clear.setIcon(icon)
            # btn_clear.setIconSize(QSize(28, 28))   # Force icon to fill button
            
            # btn_clear.setStyleSheet("""
            #     QPushButton {
            #         border: none;
            #         background: transparent;
            #         padding: 0;
            #         margin: 0;
            #     }
            #     QPushButton:hover {
            #         background-color: rgba(255,165,0,0.15);
            #         border-radius: 6px;
            #     }
            #     QPushButton:pressed {
            #         background-color: rgba(255,165,0,0.3);
            #         border-radius: 6px;
            #     }
            # """)
            
            # btn_clear.setToolTip("Clear all selections for this row")
            # btn_clear.clicked.connect(lambda _, r=i: self.clear_row_selections(r))
            # lay_bottom.addStretch(1)
            # lay_bottom.addWidget(btn_clear, 0, alignment=Qt.AlignRight | Qt.AlignBottom)



            # btn_clear = QPushButton("", w_bottom)
            # btn_clear.setFixedSize(24, 24)
            # btn_clear.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            # btn_clear.setStyleSheet("""
            #     QPushButton {
            #         font-size: 14px;
            #         font-weight: bold;
            #         color: black;
            #         background-color: white;
            #         border: 2.5px solid black;
            #         border-radius: 4px;
            #         padding: 0;
            #         margin: 0;
            #         outline: none;
            #         box-sizing: border-box;
            #     }
            #     QPushButton:hover {
            #         background-color: #f4f4f4;
            #     }
            #     QPushButton:pressed {
            #         background-color: red;
            #         color: white;
            #         border: 2.5px solid black;
            #     }
            # """)



            # btn_clear.setStyleSheet("""
            #     QPushButton {
            #         font-size: 14px;
            #         font-weight: bold;
            #         color: black;
            #         background-color: white;
            #         border: 3px solid black;
            #     }
            #     QPushButton:pressed {
            #         background-color: red;
            #         color: white;
            #     }
            # """)
            btn_clear.clicked.connect(lambda _, r=i: self.clear_row_selections(r))
            lay_bottom.addStretch(1)
            lay_bottom.addWidget(btn_clear, 0, alignment=Qt.AlignRight | Qt.AlignBottom)

            self._overlay_items.append({
                "ax": ax,
                "widget_top": w_top,
                "widget_bottom": w_bottom,
                "label": lbl,
                "radio": rdo,
                "row_index": i,
                "clear_btn": btn_clear,
            })

        if self._draw_cid:
            try: self.canvas.mpl_disconnect(self._draw_cid)
            except Exception: pass
        self._draw_cid = self.canvas.mpl_connect("draw_event", self._on_canvas_draw)
        self.canvas.draw_idle()


    def _on_row_clicked(self, row_id: int):
        """Handle radio button click → make that row active, bold it, and clear the previous row's selections."""
        prev_row = self._active_row
        new_row = int(row_id)

        # 🧹 If switching to a new row, clear all selections from the previous one
        if prev_row is not None and prev_row != new_row:
            self.clear_row_selections(prev_row)

        # Update active row
        self._active_row = new_row

        # Bold the active row; unbold others
        for i, ax in enumerate(self.axes):
            lw = 2.2 if i == self._active_row else 0.8
            for sp in ax.spines.values():
                sp.set_linewidth(lw)

        # Also thicken waveform line for the active row
        for i, ax in enumerate(self.axes):
            for line in ax.lines:
                line.set_linewidth(2.2 if i == self._active_row else 1.0)

        # Ensure radio button reflects state
        if self._row_group is not None:
            btn = self._row_group.button(self._active_row)
            if btn and not btn.isChecked():
                btn.setChecked(True)

        self.canvas.draw_idle()


    # def _on_row_clicked(self, row_id: int):
    #     """Handle radio button click → make that row active and bold its border."""
    #     self._active_row = int(row_id)
    
    #     # Bold the active row; unbold others
    #     for i, ax in enumerate(self.axes):
    #         lw = 2.2 if i == self._active_row else 0.8
    #         for sp in ax.spines.values():
    #             sp.set_linewidth(lw)
    
    #     self.canvas.draw_idle()


    def _on_canvas_draw(self, _event):
        if not self.axes or not self._overlay_items:
            return
        W_TOP, H_TOP = 160, 40
        W_BTN, H_BTN = 40, 40
        margin_x, margin_y = 10, 8
        cW, cH = self.canvas.width(), self.canvas.height()
        for itm in self._overlay_items:
            ax = itm["ax"]
            bbox = ax.get_position()
            x_right = int(bbox.x1 * cW - margin_x)
            x0_top = x_right - W_TOP
            y0_top = int((1.0 - bbox.y1) * cH + margin_y)
            itm["widget_top"].setGeometry(x0_top, y0_top, W_TOP, H_TOP)
            itm["widget_top"].raise_()
            x0_btn = x_right - W_BTN - 7
            y0_btn = int((1.0 - bbox.y0) * cH - H_BTN - margin_y)
            itm["widget_bottom"].setGeometry(x0_btn, y0_btn, W_BTN, H_BTN)
            itm["widget_bottom"].raise_()
            
            
    def _set_active_row(self, row: int, reattach_cb=None):
        """Switch active EMG row and visually highlight it."""
        # deactivate previous
        if self._active_row is not None and self._active_row != row:
            for sp in self.axes[self._active_row].spines.values():
                sp.set_linewidth(0.8)
    
        self._active_row = int(row)
    
        # visually highlight new active row
        for i, ax in enumerate(self.axes):
            lw = 2.2 if i == self._active_row else 0.8
            for sp in ax.spines.values():
                sp.set_linewidth(lw)
    
        # also thicken the waveform line itself for the active row
        for i, ax in enumerate(self.axes):
            for line in ax.lines:
                line.set_linewidth(2.2 if i == self._active_row else 1.0)
    
        # ensure radio button reflects state if you use them
        if self._row_group is not None:
            btn = self._row_group.button(self._active_row)
            if btn and not btn.isChecked():
                btn.setChecked(True)
    
        self.canvas.draw_idle()
        
        
    # ============================================================
    #                EXPORT PAYLOAD (for XML)
    # ============================================================

    def get_export_payload(self, filename: str, require_three: bool = True):
        """
        Return a structured payload for XML export.
        Contains filename, active row index, selections, and computed MVC.
        """
        if self._data is None or self._active_row is None:
            return None

        row = int(self._active_row)
        bursts = self._selections.get(row, [])
        if require_three and len(bursts) < BEST_OF:
            return None

        mvc_val = getattr(self, "_mvc_result", None)
        if mvc_val is None and bursts:
            mvc_val = self._compute_mvc_from_bursts(row, bursts[:BEST_OF])

        return {
            "filename": filename,
            "row": row,
            "bursts": bursts[:BEST_OF],
            "mvc": mvc_val,
        }

    def _compute_mvc_from_bursts(self, row: int, bursts):
        if self._data is None:
            return None
        if self._processor is None:
            try:
                self._processor = Processor()
            except Exception:
                self._processor = None
                return None

        signal = self._data[row, :]
        mvc_values = []
        for lo, hi in bursts:
            lo_i = int(lo)
            hi_i = int(hi)
            segment = signal[lo_i:hi_i]
            if segment.size == 0:
                continue
            try:
                mvc_val, _ = self._processor.mvc_matlab(segment)
                mvc_values.append(mvc_val)
            except Exception:
                continue

        if not mvc_values:
            return None
        return max(mvc_values)


