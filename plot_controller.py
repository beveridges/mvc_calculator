# -*- coding: utf-8 -*-
# utilities/plot_controller.py

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector
from matplotlib.backend_bases import MouseButton

import numpy as np

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QRadioButton, QButtonGroup, QVBoxLayout,  QPushButton, QSizePolicy

class PlotController:
    def __init__(self, parent=None, container=None, main_window=None):
        self.parent = parent
        self.main_window = main_window

        fig = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(fig)
        self.toolbar = NavigationToolbar(self.canvas, container)

        # Ensure canvas+toolbar are added to the container layout
        if container.layout() is None:
            layout = QVBoxLayout(container)
            layout.addWidget(self.toolbar)
            layout.addWidget(self.canvas)
        else:
            container.layout().addWidget(self.toolbar)
            container.layout().addWidget(self.canvas)

        self.canvas.setVisible(False)
        self.toolbar.setVisible(False)

        # Runtime state
        self.axes = []
        self._span = None
        self._press_cid = None
        self._draw_cid = None
        self._active_row = 0
        self._selections = {}
        self._patches = {}
        self._overlay_items = []   # [{ax, widget, label, radio, row_index}]
        self._row_group = None

        # Cache for export
        self._data = None
        self._labels = None

    @property
    def mw(self):
        return self.main_window
    
    
    def bind_ui_controls(self):
        """No-op placeholder kept for compatibility with main.py.
        Add signal/slot hookups here if you need them later.
        """
        return
    
    
    # def clear_row_selections(self, row: int):
    #     """Remove all selections from one row."""
    #     if row not in self._patches:
    #         return
    #     for patch in list(self._patches[row]):
    #         try:
    #             patch.remove()
    #         except Exception:
    #             pass
    #     self._patches[row].clear()
    #     self._selections[row].clear()
    #     self.canvas.draw_idle()
    
    #     if self.main_window:
    #         self.main_window.ledt_output.appendPlainText(
    #             f"[info] Cleared selections for row {row+1}"
    #         )

    # def clear_row_selections(self, row: int):
    #     """Remove all span selections (patches) from one row, then redraw."""
    #     if row not in self._patches or row not in self._selections:
    #         return
    
    #     # Safely remove all patches
    #     for p in list(self._patches[row]):
    #         try:
    #             p.remove()   # remove from matplotlib axes
    #         except Exception:
    #             pass
    #     self._patches[row].clear()
    #     self._selections[row].clear()
    
    #     # Force refresh of the canvas
    #     if row < len(self.axes):
    #         self.axes[row].figure.canvas.draw_idle()
    
    # def clear_row_selections(self, row: int):
    #     """Forcefully clear all spans from one row."""
    #     if row not in self._patches or row not in self._selections:
    #         return
    
    #     ax = self.axes[row]
    
    #     # Remove tracked patches
    #     for p in list(self._patches[row]):
    #         try:
    #             p.remove()
    #         except Exception:
    #             pass
    
    #     # Extra cleanup: remove any leftover orange patches in the Axes
    #     ax.patches = [p for p in ax.patches if not (
    #         hasattr(p, "get_facecolor") and p.get_facecolor()[0:3] == (1.0, 0.6470588235, 0.0)  # orange-ish
    #     )]
    
    #     self._patches[row].clear()
    #     self._selections[row].clear()
    
    #     # Redraw everything
    #     ax.figure.canvas.draw_idle()
    #     ax.figure.canvas.flush_events()
    
    
    # def clear_row_selections(self, row: int):
    #     """Forcefully clear all spans from one row."""
    #     if row not in self._patches or row not in self._selections:
    #         return
    
    #     ax = self.axes[row]
    
    #     # Remove only the tracked patches
    #     for p in list(self._patches[row]):
    #         try:
    #             p.remove()
    #         except Exception:
    #             pass
    
    #     # Also check for any leftover orange spans (SpanSelector artifacts etc.)
    #     for p in list(ax.patches):
    #         try:
    #             fc = p.get_facecolor()
    #             if fc and (round(fc[0], 1), round(fc[1], 1), round(fc[2], 1)) == (1.0, 0.6, 0.0):  # orange-ish
    #                 p.remove()
    #         except Exception:
    #             pass
    
    #     # Reset your tracking lists
    #     self._patches[row].clear()
    #     self._selections[row].clear()
    
    #     # Redraw
    #     ax.figure.canvas.draw_idle()
    #     ax.figure.canvas.flush_events()
    
    def clear_row_selections(self, row: int):
        """Clear all spans from one row, including SpanSelector preview."""
        if row not in self._patches or row not in self._selections:
            return
    
        ax = self.axes[row]
    
        # Remove tracked spans
        for p in list(self._patches[row]):
            try:
                p.remove()
            except Exception:
                pass
        self._patches[row].clear()
        self._selections[row].clear()
    
        # --- Extra: clear SpanSelector’s live patch if this is the active row ---
        if row == self._active_row and self._span is not None:
            try:
                if hasattr(self._span, "rect") and self._span.rect is not None:
                    self._span.rect.set_visible(False)
                    self._span.rect = None
            except Exception:
                pass
    
        # Redraw
        ax.figure.canvas.draw_idle()

    
    
    
    
    
    
    # def clear_row_selections(self, row: int):
    #     """Remove all orange span selections from one row."""
    #     if row not in self._patches:
    #         return
    #     # Remove all patches from the axes
    #     for patch in list(self._patches[row]):
    #         try:
    #             patch.remove()
    #         except Exception:
    #             pass
    #     # Reset tracking
    #     self._patches[row].clear()
    #     self._selections[row].clear()
    #     self.canvas.draw_idle()
    
    #     if self.main_window:
    #         self.main_window.ledt_output.appendPlainText(
    #             f"[info] Cleared selections for row {row+1}"
    #         )

    
    def detect_bursts_with_energy(self, fs: int, min_silence: float = 0.080, min_sound: float = 0.200):
        """
        Run energy-detection on the ACTIVE row (self._active_row) of the current tab
        and visualize up to 3 detected bursts as orange spans.
    
        Assumes self._data (2D: rows x samples) was set by plot_mat_arrays.
        """
        # sanity
        if not hasattr(self, "_data") or self._data is None:
            raise RuntimeError("No data cached in PlotController. Plot a file first.")
        if not hasattr(self, "axes") or not self.axes:
            raise RuntimeError("No axes present to draw on.")
        row = int(getattr(self, "_active_row", 0))
        if row < 0 or row >= self._data.shape[0]:
            raise RuntimeError(f"Active row {row} out of range.")
    
        x = self._data[row, :].astype(float).ravel()
        if x.size == 0:
            raise RuntimeError("Active row contains no samples.")
    
        # ---- NumPy port of MATLAB energyDetection ----
        # energy & moving average over 'min_silence' window
        energy = np.abs(x) ** 2
        L = max(1, int(round(min_silence * fs)))
        b = np.ones(L, dtype=float) / L
        moving_ave = np.convolve(energy, b, mode="same")
        ma_max = moving_ave.max() if moving_ave.size else 1.0
        if ma_max > 0:
            moving_ave = moving_ave / ma_max
    
        # threshold to get initial mask
        mask = np.ones(x.size, dtype=np.uint8)
        mask[moving_ave < 0.010] = 0
    
        # enforce minimum sound length
        min_sound_samples = max(1, int(round(min_sound * fs)))
        run = 0
        for i in range(mask.size):
            if mask[i]:
                run += 1
            else:
                if 0 < run < min_sound_samples:
                    mask[i - run:i] = 0
                run = 0
        if 0 < run < min_sound_samples:
            mask[mask.size - run:mask.size] = 0
    
        # ---- Convert mask → contiguous (start,end) intervals in sample indices
        intervals = []
        i = 0
        n = mask.size
        while i < n:
            if mask[i] == 1:
                j = i + 1
                while j < n and mask[j] == 1:
                    j += 1
                # interval spans [i, j-1] → we’ll use [i, j) in plotting
                intervals.append((int(i), int(j)))
                i = j
            else:
                i += 1
    
        # ---- Paint the first three intervals as spans on the ACTIVE row
        # ensure selection containers exist
        if not hasattr(self, "_selections") or not hasattr(self, "_patches"):
            self._selections = {k: [] for k in range(len(self.axes))}
            self._patches    = {k: [] for k in range(len(self.axes))}
    
        # clear any existing spans on this row
        for p in list(self._patches[row]):
            try:
                p.remove()
            except Exception:
                pass
        self._patches[row].clear()
        self._selections[row].clear()
    
        ax = self.axes[row]
        # lock X limits so they don't creep
        x0, x1 = ax.get_xlim()
        for (lo, hi) in intervals[:3]:
            # draw as [lo, hi) in sample index coords
            patch = ax.axvspan(lo, hi, color="orange", alpha=0.30)
            self._patches[row].append(patch)
            self._selections[row].append((lo, hi))
        ax.set_xlim(x0, x1)
    
        # keep bolding on the active row & redraw
        for i_ax, a in enumerate(self.axes):
            lw = 2.2 if i_ax == row else 0.8
            for sp in a.spines.values():
                sp.set_linewidth(lw)
    
        self.canvas.draw_idle()


    # ---------------------- PUBLIC: plot MAT arrays ----------------------
    def plot_mat_arrays(self, data, labels, max_rows=6, source_path=None):
        """
        Plot stacked EMG rows and build big Qt radios+labels in the TOP-RIGHT
        of each subplot. EMG order is axes order: axes[0] (top) == EMG 1.
        Left-drag on ACTIVE row creates spans (max 3). Shift+Left removes nearest.
        """
        self._data = data
        self._labels = labels
        self._source_path = source_path

        nrows = min(int(max_rows), int(data.shape[0]))
        npts  = int(data.shape[1])
        x = np.arange(npts)
        xlim = (0, npts - 1)

        # --- figure & axes ---
        fig = self.canvas.figure
        fig.clear()

        axes = fig.subplots(nrows, 1, sharex=True)
        if not isinstance(axes, (list, np.ndarray)):
            axes = [axes]
        self.axes = list(axes)  # axes[0] is TOP

        # === Add super title here ===
        import os
        if hasattr(self, "_source_path"):
            fname = os.path.basename(self._source_path)
        else:
            fname = "EMG Signals"
        fig.suptitle(fname, fontsize=12, fontweight="bold", ha="center")
                # --- draw traces; lock X across rows; strip ticks/labels completely ---
        
        def _strip(ax):
            ax.set_title(""); ax.set_xlabel(""); ax.set_ylabel("")
            ax.set_xticks([]); ax.set_yticks([])
            ax.tick_params(which='both', bottom=False, top=False, left=False, right=False,
                           labelbottom=False, labelleft=False)

        for i, ax in enumerate(self.axes):
            ax.plot(x, data[i, :], lw=1.0, zorder=1)
            ax.set_xlim(xlim)                     # lock X
            ax.autoscale(enable=False, axis='x')  # never change X on autoscale
            ax.relim()
            ax.autoscale_view(scalex=False, scaley=True)  # only Y may change
            ax.grid(True, which="both", linestyle="--", alpha=0.6, zorder=0)
            _strip(ax)

        # fig.subplots_adjust(left=0.06, right=0.985, top=0.985, bottom=0.06, hspace=0.12) ORIGINAL
        fig.subplots_adjust(left=0.02, right=0.985, top=0.985, bottom=0.06, hspace=0.15) 

        # --- build Qt overlay radios+labels in TOP-RIGHT (EMG 1 at top) ---
        self._build_qt_overlays(self.axes, labels)

        # --- reset selections per row ---
        self._selections = {i: [] for i in range(nrows)}
        self._patches    = {i: [] for i in range(nrows)}

        # --- toolbar: leave any pan/zoom so drags reach selector ---
        try:
            self.toolbar.mode = ""
        except Exception:
            pass

        # --- selection creation (left-drag) ---
        def onselect(xmin, xmax):
            if xmin == xmax:
                return
            if len(self._selections[self._active_row]) >= 3:
                return
            lo, hi = sorted([xmin, xmax])
            p = self.axes[self._active_row].axvspan(lo, hi, color="orange", alpha=0.30)
            self._selections[self._active_row].append((lo, hi))
            self._patches[self._active_row].append(p)
            self.canvas.draw_idle()

        # --- deletion (Shift + Left click near/inside span) ---
        def px_to_data_x(ax, px):
            bb = ax.get_window_extent()
            if bb.width <= 0:
                return 0.0
            x0, x1 = ax.get_xlim()
            return (x1 - x0) / bb.width * px

        def shift_held(event) -> bool:
            ge = getattr(event, "guiEvent", None)
            if ge is not None:
                try:
                    return bool(ge.modifiers() & Qt.ShiftModifier)
                except Exception:
                    pass
            key = (getattr(event, "key", "") or "").lower()
            return "shift" in key

        def on_mouse_press(event):
            # only act on active row for deletion
            ax = self.axes[self._active_row]
            if event.inaxes is not ax:
                return
            if event.button is not MouseButton.LEFT or not shift_held(event):
                return
            if event.xdata is None:
                return

            x_click = float(event.xdata)
            tol = px_to_data_x(ax, 6.0)  # ~6px tolerance

            best_idx, best_dist = None, None
            for j, (lo, hi) in enumerate(self._selections[self._active_row]):
                dist = 0.0 if lo <= x_click <= hi else min(abs(x_click - lo), abs(x_click - hi))
                if dist <= tol and (best_dist is None or dist < best_dist):
                    best_dist, best_idx = dist, j

            if best_idx is not None:
                self._patches[self._active_row][best_idx].remove()
                self._patches[self._active_row].pop(best_idx)
                self._selections[self._active_row].pop(best_idx)
                self.canvas.draw_idle()

        # connect (replace old handler if any)
        if self._press_cid:
            try: self.canvas.mpl_disconnect(self._press_cid)
            except Exception: pass
        self._press_cid = self.canvas.mpl_connect("button_press_event", on_mouse_press)

        # attach span to current active row (default 0)
        def reattach_selector(ax_target):
            return SpanSelector(
                ax_target, onselect, direction="horizontal",
                useblit=True, props=dict(alpha=0.3, facecolor="orange"),
                interactive=True, button=MouseButton.LEFT
            )

        self._set_active_row(int(getattr(self, "_active_row", 0)), reattach_cb=reattach_selector)

        # show
        self.canvas.setVisible(True)
        self.toolbar.setVisible(True)
        self.canvas.draw_idle()

    # ---------------------- overlays (Qt) ----------------------
    def _build_qt_overlays(self, axes, labels):
        """
        Two overlays per subplot:
          - widget_top   : [ Label "EMG n" ]  [ BIG QRadioButton ]  (top-right)
          - widget_bottom: [ square Clear Row QPushButton ]         (bottom-right, aligned to radio)
        """
        # clear old overlays
        for itm in self._overlay_items:
            for key in ("widget_top", "widget_bottom"):
                try:
                    itm[key].deleteLater()
                except Exception:
                    pass
        self._overlay_items = []
    
        # fresh exclusive group
        if self._row_group:
            try:
                self._row_group.idClicked.disconnect(self._on_row_clicked)
            except Exception:
                pass
        self._row_group = QButtonGroup(self.canvas)
        self._row_group.setExclusive(True)
        self._row_group.idClicked.connect(self._on_row_clicked)
    
        # styles
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
        button_style = """
            QPushButton {
                font-size: 11px; font-weight: bold; color: black;
                background-color: white;
                border: 3px solid black;      /* bold outline like the radio */
                padding: 0px;                  /* make it tight & square */
                min-width: 0px; min-height: 0px;
            }
            QPushButton:pressed {
                background-color: red; color: white;
            }
        """
    
        # Build overlays per axes (i == 0 is TOP → EMG 1)
        for i, ax in enumerate(axes):
            # --- Top overlay (label + radio) ---
            w_top = QWidget(self.canvas)
            w_top.setAttribute(Qt.WA_NoSystemBackground, True)
            w_top.setAttribute(Qt.WA_TranslucentBackground, True)
            w_top.setStyleSheet("background: transparent;")
            w_top.setVisible(True)
    
            lay_top = QHBoxLayout(w_top)
            # zero right margin so the radio can sit flush to the right edge of w_top
            lay_top.setContentsMargins(8, 4, 0, 4)
            lay_top.setSpacing(6)
    
            label_text = str(labels[i]) if labels is not None and len(labels) > i else f"EMG {i+1}"
            lbl = QLabel(label_text, w_top)
            lbl.setStyleSheet(label_style)
    
            rdo = QRadioButton(w_top)
            rdo.setStyleSheet(radio_style)
            rdo.setChecked(i == int(getattr(self, "_active_row", 0)))
            self._row_group.addButton(rdo, i)
    
            lay_top.addWidget(lbl, 1)
            lay_top.addWidget(rdo, 0, alignment=Qt.AlignRight | Qt.AlignTop)
    
            # --- Bottom overlay (Clear Row pushbutton) ---
            w_bottom = QWidget(self.canvas)
            w_bottom.setAttribute(Qt.WA_NoSystemBackground, True)
            w_bottom.setAttribute(Qt.WA_TranslucentBackground, True)
            w_bottom.setStyleSheet("background: transparent;")
            w_bottom.setVisible(True)
    
            lay_bottom = QHBoxLayout(w_bottom)
            # zero right margin so we can align the button’s right edge precisely
            lay_bottom.setContentsMargins(0, 0, 0, 0)
            lay_bottom.setSpacing(0)
    
            btn_clear = QPushButton("", w_bottom)  # square button with an "x"
            btn_clear.setFixedSize(24, 24)
            btn_clear.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # stops squashing
            btn_clear.setStyleSheet("""
                QPushButton {
                    font-size: 14px;
                    font-weight: bold;
                    color: black;
                    background-color: white;
                    border: 3px solid black;
                    }
                QPushButton:pressed {
                    background-color: red;
                    color: white;
                }
            """)
                                
            # btn_clear.setStyleSheet(button_style)
            btn_clear.clicked.connect(lambda _, r=i: self.clear_row_selections(r))
    
            lay_bottom.addStretch(1)        
            lay_bottom.addWidget(btn_clear, 0, alignment=Qt.AlignRight | Qt.AlignBottom)
    
            # Save both overlays and the radio reference
            self._overlay_items.append({
                "ax": ax,
                "widget_top": w_top,
                "widget_bottom": w_bottom,
                "label": lbl,
                "radio": rdo,
                "row_index": i,
                "clear_btn": btn_clear,
            })
    
        # keep overlays positioned
        if self._draw_cid:
            try:
                self.canvas.mpl_disconnect(self._draw_cid)
            except Exception:
                pass
        self._draw_cid = self.canvas.mpl_connect("draw_event", self._on_canvas_draw)
    
        self.canvas.draw_idle()

    
 
    
 
    
 
    
 
    
 
    
 
    
 
    
 
    
 
    
 
    
 
    
 # def _build_qt_overlays(self, axes, labels):
    #     """
    #     Create two overlay widgets per subplot:
    #     - Top-right: [ Label "EMG n" ]  [ BIG QRadioButton ]
    #     - Bottom-right: [ Clear Row button ]
    #     """
    #     # clear old overlays
    #     for itm in self._overlay_items:
    #         for key in ("widget_top", "widget_bottom"):
    #             try:
    #                 itm[key].deleteLater()
    #             except Exception:
    #                 pass
    #     self._overlay_items = []
    
    #     # fresh exclusive group
    #     if self._row_group:
    #         try:
    #             self._row_group.idClicked.disconnect(self._on_row_clicked)
    #         except Exception:
    #             pass
    #     self._row_group = QButtonGroup(self.canvas)
    #     self._row_group.setExclusive(True)
    #     self._row_group.idClicked.connect(self._on_row_clicked)
    
    #     # styles
    #     radio_style = """
    #         QRadioButton::indicator { width: 18px; height: 18px; }
    #         QRadioButton::indicator:unchecked {
    #             border: 3px solid black; border-radius: 13px; background: white;
    #         }
    #         QRadioButton::indicator:checked {
    #             border: 3px solid black; border-radius: 13px; background: #3daee9;
    #         }
    #     """
    #     label_style = """
    #         QLabel {
    #             font-size: 18px; font-weight: 700; color: black;
    #             background: rgba(255,255,255,230);
    #             border-radius: 6px; padding: 2px 10px;
    #         }
    #     """
    #     button_style = """
    #         QPushButton {
    #             min-width: 20px; min-height: 20px;
    #             max-width: 20px; max-height: 20px;
    #             font-weight: bold;
    #             background-color: white;
    #             border: 3px solid black;
    #         }
    #         QPushButton:pressed {
    #             background-color: red;
    #             color: white;
    #         }
    #     """
    
    #     for i, ax in enumerate(axes):
    #         # --- Top overlay: label + radio ---
    #         w_top = QWidget(self.canvas)
    #         w_top.setAttribute(Qt.WA_NoSystemBackground, True)
    #         w_top.setAttribute(Qt.WA_TranslucentBackground, True)
    #         w_top.setStyleSheet("background: transparent;")
    #         w_top.setVisible(True)
    
    #         lay_top = QHBoxLayout(w_top)
    #         lay_top.setContentsMargins(8, 4, 8, 4)
    #         lay_top.setSpacing(6)
    
    #         label_text = str(labels[i]) if labels is not None and len(labels) > i else f"EMG {i+1}"
    #         lbl = QLabel(label_text, w_top)
    #         lbl.setStyleSheet(label_style)
    
    #         rdo = QRadioButton(w_top)
    #         rdo.setStyleSheet(radio_style)
    #         rdo.setChecked(i == int(getattr(self, "_active_row", 0)))
    #         self._row_group.addButton(rdo, i)
    
    #         lay_top.addWidget(lbl, 1)
    #         lay_top.addWidget(rdo, 0, alignment=Qt.AlignVCenter)
    
    #         # --- Bottom overlay: clear button ---
    #         w_bottom = QWidget(self.canvas)
    #         w_bottom.setAttribute(Qt.WA_NoSystemBackground, True)
    #         w_bottom.setAttribute(Qt.WA_TranslucentBackground, True)
    #         w_bottom.setStyleSheet("background: transparent;")
    #         w_bottom.setVisible(True)
    
    #         lay_bottom = QHBoxLayout(w_bottom)
    #         lay_bottom.setContentsMargins(8, 2, 8, 2)
    
    #         btn_clear = QPushButton("X", w_bottom)
    #         btn_clear.setStyleSheet(button_style)
    #         btn_clear.clicked.connect(lambda _, r=i: self.clear_row_selections(r))
    
    #         lay_bottom.addStretch(1)
    #         lay_bottom.addWidget(btn_clear, 0, alignment=Qt.AlignRight)
    
    #         # Save overlays
    #         self._overlay_items.append({
    #             "ax": ax,
    #             "widget_top": w_top,
    #             "widget_bottom": w_bottom,
    #             "label": lbl,
    #             "radio": rdo,
    #             "clear_btn": btn_clear,
    #             "row_index": i,
    #         })
    
    #     # keep overlays positioned
    #     if self._draw_cid:
    #         try:
    #             self.canvas.mpl_disconnect(self._draw_cid)
    #         except Exception:
    #             pass
    #     self._draw_cid = self.canvas.mpl_connect("draw_event", self._on_canvas_draw)
    
    #     self.canvas.draw_idle()

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # def _build_qt_overlays(self, axes, labels):
    #     """
    #     Create one QWidget per subplot, parented to the canvas, with:
    #     [ Label "EMG n" ]  [ BIG QRadioButton ]  [ Clear Row button ]
    #     All inline in a single horizontal row.
    #     """
    #     # clear old overlays
    #     for itm in self._overlay_items:
    #         try:
    #             itm["widget"].deleteLater()
    #         except Exception:
    #             pass
    #     self._overlay_items = []
    
    #     # fresh exclusive group
    #     if self._row_group:
    #         try:
    #             self._row_group.idClicked.disconnect(self._on_row_clicked)
    #         except Exception:
    #             pass
    #     self._row_group = QButtonGroup(self.canvas)
    #     self._row_group.setExclusive(True)
    #     self._row_group.idClicked.connect(self._on_row_clicked)
    
    #     # styles
    #     radio_style = """
    #         QRadioButton::indicator { width: 18px; height: 18px; }
    #         QRadioButton::indicator:unchecked {
    #             border: 3px solid black; border-radius: 13px; background: white;
    #         }
    #         QRadioButton::indicator:checked {
    #             border: 3px solid black; border-radius: 13px; background: #3daee9;
    #         }
    #     """
    #     label_style = """
    #         QLabel {
    #             font-size: 18px; font-weight: 700; color: black;
    #             background: rgba(255,255,255,230);
    #             border-radius: 6px; padding: 2px 10px;
    #         }
    #     """
    #     button_style = """
    #         QPushButton {
    #             min-width: 18px; min-height: 18px;
    #             max-width: 18px; max-height: 18px;
    #             font-weight: bold;
    #             background-color: white;
    #             border: 3px solid black;
                
    #         }
    #         QPushButton:pressed {
    #             background-color: red;
    #             color: white;
    #         }
    #     """
    
    #     # Build overlay per axes (i == 0 is TOP → EMG 1)
    #     for i, ax in enumerate(axes):
    #         w = QWidget(self.canvas)  # parent to canvas
    #         w.setAttribute(Qt.WA_NoSystemBackground, True)
    #         w.setAttribute(Qt.WA_TranslucentBackground, True)
    #         w.setStyleSheet("background: transparent;")
    #         w.setVisible(True)
    
    #         lay = QHBoxLayout(w)
    #         lay.setContentsMargins(8, 4, 8, 4)
    #         lay.setSpacing(6)
    
    #         # Label
    #         label_text = str(labels[i]) if labels is not None and len(labels) > i else f"EMG {i+1}"
    #         lbl = QLabel(label_text, w)
    #         lbl.setStyleSheet(label_style)
    
    #         # Radio button
    #         rdo = QRadioButton(w)
    #         rdo.setStyleSheet(radio_style)
    #         rdo.setChecked(i == int(getattr(self, "_active_row", 0)))
    #         self._row_group.addButton(rdo, i)
    
    #         # Clear button
    #         btn_clear = QPushButton("X", w)
    #         btn_clear.setStyleSheet(button_style)
    #         btn_clear.clicked.connect(lambda _, r=i: self.clear_row_selections(r))
    
    #         # Add all in one row
    #         lay.addWidget(lbl, 1)
    #         lay.addWidget(rdo, 0, alignment=Qt.AlignVCenter)
    #         lay.addWidget(btn_clear, 0, alignment=Qt.AlignVCenter)
    
    #         # Save overlay item
    #         self._overlay_items.append({
    #             "ax": ax,
    #             "widget": w,
    #             "label": lbl,
    #             "radio": rdo,
    #             "clear_btn": btn_clear,
    #             "row_index": i,
    #         })
    
    #     # keep overlays positioned
    #     if self._draw_cid:
    #         try:
    #             self.canvas.mpl_disconnect(self._draw_cid)
    #         except Exception:
    #             pass
    #     self._draw_cid = self.canvas.mpl_connect("draw_event", self._on_canvas_draw)
    
    #     self.canvas.draw_idle()

    
    
    
    
    
    
    
    
    
    
    
    
    
    # def _build_qt_overlays(self, axes, labels):
    #     """
    #     Create two QWidget overlays per subplot, parented to the canvas:
    #     - Top-right: [ Label "EMG n" ]  [ BIG QRadioButton ]
    #     - Bottom-right: [ Clear Row QPushButton ]
    #     """
    #     # clear old overlays
    #     for itm in self._overlay_items:
    #         for key in ("widget_top", "widget_bottom"):
    #             try:
    #                 itm[key].deleteLater()
    #             except Exception:
    #                 pass
    #     self._overlay_items = []
    
    #     # fresh exclusive group
    #     if self._row_group:
    #         try:
    #             self._row_group.idClicked.disconnect(self._on_row_clicked)
    #         except Exception:
    #             pass
    #     self._row_group = QButtonGroup(self.canvas)
    #     self._row_group.setExclusive(True)
    #     self._row_group.idClicked.connect(self._on_row_clicked)
    
    #     # styles
    #     radio_style = """
    #         QRadioButton::indicator { width: 18px; height: 18px; }
    #         QRadioButton::indicator:unchecked {
    #             border: 3px solid black; border-radius: 13px; background: white;
    #         }
    #         QRadioButton::indicator:checked {
    #             border: 3px solid black; border-radius: 13px; background: #3daee9;
    #         }
    #     """
    #     label_style = """
    #         QLabel {
    #             font-size: 18px; font-weight: 700; color: black;
    #             background: rgba(255,255,255,230);
    #             border-radius: 6px; padding: 2px 10px;
    #         }
    #     """
    #     button_style = """
    #         QPushButton {
    #             font-size: 11px;
    #             font-weight: bold;
    #             color: black;
    #             background-color: white;
    #             border: 3px solid black;
    #             padding: 2px 6px;
    #         }
    #         QPushButton:pressed {
    #             background-color: red;
    #             color: white;
    #         }
    #     """
    
    #     # Build overlays per axes (i == 0 is TOP → EMG 1)
    #     for i, ax in enumerate(axes):
    #         # --- Top overlay (label + radio) ---
    #         w_top = QWidget(self.canvas)
    #         w_top.setAttribute(Qt.WA_NoSystemBackground, True)
    #         w_top.setAttribute(Qt.WA_TranslucentBackground, True)
    #         w_top.setStyleSheet("background: transparent;")
    #         w_top.setVisible(True)
    
    #         lay_top = QHBoxLayout(w_top)
    #         lay_top.setContentsMargins(8, 4, 8, 4)
    #         lay_top.setSpacing(6)
    
    #         label_text = str(labels[i]) if labels is not None and len(labels) > i else f"EMG {i+1}"
    #         lbl = QLabel(label_text, w_top)
    #         lbl.setStyleSheet(label_style)
    
    #         rdo = QRadioButton(w_top)
    #         rdo.setStyleSheet(radio_style)
    #         rdo.setChecked(i == int(getattr(self, "_active_row", 0)))
    #         self._row_group.addButton(rdo, i)
    
    #         lay_top.addWidget(lbl, 1)
    #         lay_top.addWidget(rdo, 0, alignment=Qt.AlignVCenter)
    
    #         # --- Bottom overlay (Clear Row pushbutton) ---
    #         w_bottom = QWidget(self.canvas)
    #         w_bottom.setAttribute(Qt.WA_NoSystemBackground, True)
    #         w_bottom.setAttribute(Qt.WA_TranslucentBackground, True)
    #         w_bottom.setStyleSheet("background: transparent;")
    #         w_bottom.setVisible(True)
    
    #         lay_bottom = QHBoxLayout(w_bottom)
    #         lay_bottom.setContentsMargins(8, 2, 8, 2)
    
    #         btn_clear = QPushButton("", w_bottom)
    #         btn_clear.setFixedSize(22, 22)
    #         btn_clear.setStyleSheet(button_style)
    #         btn_clear.clicked.connect(lambda _, r=i: self.clear_row_selections(r))
    
    #         lay_bottom.addStretch(1)
    #         lay_bottom.addWidget(btn_clear, 0, alignment=Qt.AlignRight)
    
    #         # Save both overlays
    #         self._overlay_items.append({
    #             "ax": ax,
    #             "widget_top": w_top,
    #             "widget_bottom": w_bottom,
    #             "label": lbl,
    #             "radio": rdo,
    #             "row_index": i,
    #             "clear_btn": btn_clear,
    #         })
    
    #     # keep overlays positioned
    #     if self._draw_cid:
    #         try:
    #             self.canvas.mpl_disconnect(self._draw_cid)
    #         except Exception:
    #             pass
    #     self._draw_cid = self.canvas.mpl_connect("draw_event", self._on_canvas_draw)
    
    #     self.canvas.draw_idle()

    
 
    
 
    
 
    
 
    
 
    
 
    
 
    
 
    
 
    
 
    
 
    
 
    
 
    
 
    
 
    
 
    # def _build_qt_overlays(self, axes, labels):
    #     """
    #     Create two QWidget overlays per subplot, parented to the canvas:
    #     - Top-right: [ Label "EMG n" ]  [ BIG QRadioButton ]
    #     - Bottom-right: [ Clear Row button ]
    #     """
    #     # clear old overlays
    #     for itm in self._overlay_items:
    #         for key in ("widget_top", "widget_bottom"):
    #             try:
    #                 itm[key].deleteLater()
    #             except Exception:
    #                 pass
    #     self._overlay_items = []
    
    #     # fresh exclusive group
    #     if self._row_group:
    #         try:
    #             self._row_group.idClicked.disconnect(self._on_row_clicked)
    #         except Exception:
    #             pass
    #     self._row_group = QButtonGroup(self.canvas)
    #     self._row_group.setExclusive(True)
    #     self._row_group.idClicked.connect(self._on_row_clicked)
    
    #     radio_style = """
    #         QRadioButton::indicator { width: 18px; height: 18px; }
    #         QRadioButton::indicator:unchecked {
    #             border: 3px solid black; border-radius: 13px; background: white;
    #         }
    #         QRadioButton::indicator:checked {
    #             border: 3px solid black; border-radius: 13px; background: #3daee9;
    #         }
    #     """
    #     label_style = """
    #         QLabel {
    #             font-size: 18px; font-weight: 700; color: black;
    #             background: rgba(255,255,255,230);
    #             border-radius: 6px; padding: 2px 10px;
    #         }
    #     """
    
    #     # Build overlays per axes (i == 0 is TOP → EMG 1)
    #     for i, ax in enumerate(axes):
    #         # --- Top overlay (label + radio) ---
    #         w_top = QWidget(self.canvas)
    #         w_top.setAttribute(Qt.WA_NoSystemBackground, True)
    #         w_top.setAttribute(Qt.WA_TranslucentBackground, True)
    #         w_top.setStyleSheet("background: transparent;")
    #         w_top.setVisible(True)
    
    #         lay_top = QHBoxLayout(w_top)
    #         lay_top.setContentsMargins(8, 4, 8, 4)
    #         lay_top.setSpacing(6)
    
    #         label_text = str(labels[i]) if labels is not None and len(labels) > i else f"EMG {i+1}"
    #         lbl = QLabel(label_text, w_top)
    #         lbl.setStyleSheet(label_style)
    
    #         rdo = QRadioButton(w_top)
    #         rdo.setStyleSheet(radio_style)
    #         rdo.setChecked(i == int(getattr(self, "_active_row", 0)))
    #         self._row_group.addButton(rdo, i)
    
    #         lay_top.addWidget(lbl, 1)
    #         lay_top.addWidget(rdo, 0, alignment=Qt.AlignVCenter)
    
    #         # --- Bottom overlay (Clear Row button) ---
    #         w_bottom = QWidget(self.canvas)
    #         w_bottom.setAttribute(Qt.WA_NoSystemBackground, True)
    #         w_bottom.setAttribute(Qt.WA_TranslucentBackground, True)
    #         w_bottom.setStyleSheet("background: transparent;")
    #         w_bottom.setVisible(True)
    
    #         lay_bottom = QHBoxLayout(w_bottom)
    #         lay_bottom.setContentsMargins(8, 2, 8, 2)
    
    #         btn_clear = QRadioButton("", w_bottom)  # styled like radio
    #         btn_clear.setStyleSheet(radio_style)
    #         btn_clear.clicked.connect(lambda _, r=i: self.clear_row_selections(r))
    
    #         lay_bottom.addStretch(1)
    #         lay_bottom.addWidget(btn_clear, 0, alignment=Qt.AlignRight)
    
    #         # Save both overlays
    #         self._overlay_items.append({
    #             "ax": ax,
    #             "widget_top": w_top,
    #             "widget_bottom": w_bottom,
    #             "label": lbl,
    #             "radio": rdo,
    #             "row_index": i,
    #             "clear_btn": btn_clear,
    #         })
    
    #     # keep overlays positioned
    #     if self._draw_cid:
    #         try:
    #             self.canvas.mpl_disconnect(self._draw_cid)
    #         except Exception:
    #             pass
    #     self._draw_cid = self.canvas.mpl_connect("draw_event", self._on_canvas_draw)
    
    #     self.canvas.draw_idle()

   # def _build_qt_overlays(self, axes, labels):
    #     """
    #     Create one QWidget per subplot, parented to the canvas, with:
    #     [ Label "EMG n" ]  [ BIG QRadioButton ] + Clear Row button.
    #     Positioned at the TOP-RIGHT of each axes; EMG 1 is the TOP subplot.
    #     """
    #     # clear old overlays
    #     for itm in self._overlay_items:
    #         try:
    #             itm["widget"].deleteLater()
    #         except Exception:
    #             pass
    #     self._overlay_items = []
    
    #     # fresh exclusive group
    #     if self._row_group:
    #         try:
    #             self._row_group.idClicked.disconnect(self._on_row_clicked)
    #         except Exception:
    #             pass
    #     self._row_group = QButtonGroup(self.canvas)
    #     self._row_group.setExclusive(True)
    #     self._row_group.idClicked.connect(self._on_row_clicked)
    
    #     radio_style = """
    #         QRadioButton::indicator { width: 18px; height: 18px; }
    #         QRadioButton::indicator:unchecked {
    #             border: 3px solid black; border-radius: 13px; background: white;
    #         }
    #         QRadioButton::indicator:checked {
    #             border: 3px solid black; border-radius: 13px; background: #3daee9;
    #         }
    #     """
    #     label_style = """
    #         QLabel {
    #             font-size: 18px; font-weight: 700; color: black;
    #             background: rgba(255,255,255,230);
    #             border-radius: 6px; padding: 2px 10px;
    #         }
    #     """
    
    #     # Build overlay per axes (i == 0 is TOP → EMG 1)
    #     for i, ax in enumerate(axes):
    #         w = QWidget(self.canvas)  # parent to canvas
    #         w.setAttribute(Qt.WA_NoSystemBackground, True)
    #         w.setAttribute(Qt.WA_TranslucentBackground, True)
    #         w.setStyleSheet("background: transparent;")
    #         w.setVisible(True)
    
    #         lay = QVBoxLayout(w)
    #         lay.setContentsMargins(8, 4, 8, 4)
    #         lay.setSpacing(4)
    
    #         # top row with label + radio
    #         top_row = QHBoxLayout()
    #         top_row.setContentsMargins(0, 0, 0, 0)
    #         top_row.setSpacing(6)
    
    #         label_text = str(labels[i]) if labels is not None and len(labels) > i else f"EMG {i+1}"
    #         lbl = QLabel(label_text, w)
    #         lbl.setStyleSheet(label_style)
    
    #         rdo = QRadioButton(w)
    #         rdo.setStyleSheet(radio_style)
    #         rdo.setChecked(i == int(getattr(self, "_active_row", 0)))
    #         self._row_group.addButton(rdo, i)   # id == row index
    
    #         top_row.addWidget(lbl, 1)
    #         top_row.addWidget(rdo, 0, alignment=Qt.AlignVCenter)
    
    #         lay.addLayout(top_row)
    
    #         # add Clear Row button below
    #         btn_clear = QPushButton("Clear Row", w)
    #         btn_clear.setFixedHeight(20)
    #         btn_clear.setStyleSheet("font-size: 11px; padding: 1px 6px;")
    #         btn_clear.clicked.connect(lambda _, r=i: self.clear_row_selections(r))
    #         lay.addWidget(btn_clear, 0, alignment=Qt.AlignLeft)
    
    #         # save overlay item
    #         self._overlay_items.append({
    #             "ax": ax,
    #             "widget": w,
    #             "label": lbl,
    #             "radio": rdo,
    #             "row_index": i,
    #             "clear_btn": btn_clear,
    #         })
    
    #     # keep overlays positioned
    #     if self._draw_cid:
    #         try:
    #             self.canvas.mpl_disconnect(self._draw_cid)
    #         except Exception:
    #             pass
    #     self._draw_cid = self.canvas.mpl_connect("draw_event", self._on_canvas_draw)
    
    #     self.canvas.draw_idle()

















    # def _build_qt_overlays(self, axes, labels):
        # """
        # Create one QWidget per subplot, parented to the canvas, with:
        # [ Label "EMG n" ]  [ BIG QRadioButton ]
        # Positioned at the TOP-RIGHT of each axes; EMG 1 is the TOP subplot.
        # """
        # # clear old overlays
        # for itm in self._overlay_items:
        #     try: itm["widget"].deleteLater()
        #     except Exception: pass
        # self._overlay_items = []

        # # fresh exclusive group
        # if self._row_group:
        #     try: self._row_group.idClicked.disconnect(self._on_row_clicked)
        #     except Exception: pass
        # self._row_group = QButtonGroup(self.canvas)
        # self._row_group.setExclusive(True)
        # self._row_group.idClicked.connect(self._on_row_clicked)

        # # big styles
        # radio_style = """
        #     QRadioButton::indicator { width: 18px; height: 18px; }
        #     QRadioButton::indicator:unchecked {
        #         border: 3px solid black; border-radius: 13px; background: white;
        #     }
        #     QRadioButton::indicator:checked {
        #         border: 3px solid black; border-radius: 13px; background: #3daee9;
        #     }
        # """
        # label_style = """
        #     QLabel {
        #         font-size: 18px; font-weight: 700; color: black;
        #         background: rgba(255,255,255,230);
        #         border-radius: 6px; padding: 2px 10px;
        #     }
        # """

        # # Build overlay per axes (i == 0 is TOP → EMG 1)
        # for i, ax in enumerate(axes):
        #     w = QWidget(self.canvas)  # parent to canvas
        #     w.setAttribute(Qt.WA_NoSystemBackground, True)
        #     w.setAttribute(Qt.WA_TranslucentBackground, True)
        #     w.setStyleSheet("background: transparent;")
        #     w.setVisible(True)

        #     lay = QHBoxLayout(w)
        #     lay.setContentsMargins(8, 4, 8, 4)
        #     lay.setSpacing(10)
          
        #     label_text = str(labels[i]) if labels is not None and len(labels) > i else f"EMG {i+1}"
        #     lbl = QLabel(label_text, w)
        #     lbl.setStyleSheet(label_style)

        #     rdo = QRadioButton(w)
        #     rdo.setStyleSheet(radio_style)
        #     rdo.setChecked(i == int(getattr(self, "_active_row", 0)))
        #     self._row_group.addButton(rdo, i)   # id == row index

        #     lay.addWidget(lbl, 1)
        #     lay.addWidget(rdo, 0, alignment=Qt.AlignVCenter)

        #     self._overlay_items.append({
        #         "ax": ax,
        #         "widget": w,
        #         "label": lbl,
        #         "radio": rdo,
        #         "row_index": i,   # 0 = TOP
        #     })

        # # keep overlays positioned
        # if self._draw_cid:
        #     try: self.canvas.mpl_disconnect(self._draw_cid)
        #     except Exception: pass
        # self._draw_cid = self.canvas.mpl_connect("draw_event", self._on_canvas_draw)

        # self.canvas.draw_idle()

    def _on_row_clicked(self, row_id: int):
        # reattach selector & highlight
        def reattach_selector(ax_target):
            return SpanSelector(
                ax_target, lambda a,b: None,  # replaced immediately below
                direction="horizontal", useblit=True,
                props=dict(alpha=0.3, facecolor="orange"),
                interactive=True, button=MouseButton.LEFT
            )
        # we’ll reuse the existing onselect by rebuilding via plot_mat_arrays’ setup
        # Instead just call _set_active_row with current selector’s callback preserved
        # Grab current callback by constructing a new selector in _set_active_row
        self._set_active_row(row_id, reattach_cb=reattach_selector)

    # Keep overlay widgets at top-right of each axes (on draw/resize/pan)
    # def _on_canvas_draw(self, _event):
    #     if not self.axes or not self._overlay_items:
    #         return
    
    #     W, H = 150, 38
    #     margin_x = 10
    #     margin_y = 8
    
    #     cW = self.canvas.width()
    #     cH = self.canvas.height()
    
    #     for itm in self._overlay_items:
    #         ax = itm["ax"]
    #         bbox = ax.get_position()
    
    #         # top overlay (label+radio)
    #         x0_top = int(bbox.x1 * cW - margin_x - W)
    #         y0_top = int((1.0 - bbox.y1) * cH + margin_y)
    #         itm["widget_top"].setGeometry(x0_top, y0_top, W, H)
    
    #         # bottom overlay (Clear Row)
    #         x0_bottom = int(bbox.x1 * cW - margin_x - W)
    #         y0_bottom = int((1.0 - bbox.y0) * cH - H - margin_y)
    #         itm["widget_bottom"].setGeometry(x0_bottom, y0_bottom, W, H)
    
    
    # def _on_canvas_draw(self, _event):
    #     if not self.axes or not self._overlay_items:
    #         return
    
    #     # widget size (px) and margins inside axes
    #     W, H = 180, 38
    #     margin_x = 10
    #     margin_y = 8
    
    #     # canvas pixel size
    #     cW = self.canvas.width()
    #     cH = self.canvas.height()
    
    #     for itm in self._overlay_items:
    #         ax = itm["ax"]
    #         w  = itm["widget"]
    
    #         # axes bbox in figure fraction
    #         bbox = ax.get_position()
    #         # convert to pixel rect inside canvas
    #         x0 = int(bbox.x1 * cW - margin_x - W)   # right align
    #         y0 = int((1.0 - bbox.y1) * cH + margin_y)  # top inside axes
    #         w.setGeometry(x0, y0, W, H)

    # def _on_canvas_draw(self, _event):
    #     """
    #     Position the overlay widgets on each axes:
    #       - widget_top    → top-right inside axes (label + radio)
    #       - widget_bottom → bottom-right inside axes (clear button)
    #     """
    #     if not self.axes or not self._overlay_items:
    #         return
    
    #     # canvas pixel size
    #     cW = self.canvas.width()
    #     cH = self.canvas.height()
    
    #     # overlay sizes & margins (px)
    #     W_TOP, H_TOP = 170, 38          # size of the top overlay (label + radio)
    #     W_BTN, H_BTN = 24, 24           # size of the bottom-right clear button
    #     MARGIN_X = 10                   # right-side margin
    #     MARGIN_Y_TOP = 8                # top margin inside axes
    #     MARGIN_Y_BOTTOM = 8             # bottom margin inside axes
    
    #     for itm in self._overlay_items:
    #         ax = itm["ax"]
    #         bbox = ax.get_position()    # figure fraction coordinates
    
    #         # convert axes bbox to canvas pixels
    #         x0_px = int(bbox.x0 * cW)              # left
    #         x1_px = int(bbox.x1 * cW)              # right
    #         y_top_px = int((1.0 - bbox.y1) * cH)   # top inside canvas
    #         y_bot_px = int((1.0 - bbox.y0) * cH)   # bottom inside canvas
    
    #         # --- TOP-RIGHT (label + radio) ---
    #         tx = x1_px - MARGIN_X - W_TOP
    #         ty = y_top_px + MARGIN_Y_TOP
    #         itm["widget_top"].setGeometry(tx, ty, W_TOP, H_TOP)
    
    #         # --- BOTTOM-RIGHT (clear button) ---
    #         bx = x1_px - MARGIN_X - W_BTN
    #         by = y_bot_px - MARGIN_Y_BOTTOM - H_BTN
    #         itm["widget_bottom"].setGeometry(bx, by, W_BTN, H_BTN)

    # def _on_canvas_draw(self, _event):
    #     if not self.axes or not self._overlay_items:
    #         return
    
    #     # --- sizing for overlays ---
    #     # top strip (label + radio)
    #     W_TOP, H_TOP = 160, 38
    #     # bottom button (square clear)
    #     W_BTN, H_BTN = 24, 24
    
    #     # margins inside each axes box
    #     MARGIN_RIGHT = 10      # distance from right edge (both widgets)
    #     MARGIN_TOP   = 8       # distance from top edge (top widget)
    #     MARGIN_BOT   = 8       # distance from bottom edge (bottom widget)
    
    #     # tiny nudge for the bottom button to move it UP and LEFT slightly
    #     NUDGE_LEFT = 20         # px → move left
    #     NUDGE_UP   = 4         # px → move up
    
    #     cW = self.canvas.width()
    #     cH = self.canvas.height()
    
    #     for itm in self._overlay_items:
    #         ax = itm["ax"]
    
    #         # axes bbox in figure fraction
    #         bbox = ax.get_position()
    
    #         # common right edge in pixels (keeps radio and clear button aligned)
    #         x_right = int(bbox.x1 * cW - MARGIN_RIGHT)
    
    #         # ---- TOP (label + radio) ----
    #         x0_top = x_right - W_TOP
    #         y0_top = int((1.0 - bbox.y1) * cH + MARGIN_TOP)
    #         w_top  = itm.get("widget_top") or itm.get("widget")
    #         if w_top is not None:
    #             w_top.setGeometry(x0_top, y0_top, W_TOP, H_TOP)
    #             w_top.raise_()
    
    #         # ---- BOTTOM (clear button) ----
    #         x0_btn = x_right - W_BTN - NUDGE_LEFT
    #         y0_btn = int((1.0 - bbox.y0) * cH - MARGIN_BOT - H_BTN - NUDGE_UP)
    #         w_bot  = itm.get("widget_bottom")
    #         if w_bot is not None:
    #             w_bot.setGeometry(x0_btn, y0_btn, W_BTN, H_BTN)
    #             w_bot.raise_()
       
    #     # after setting geometry
    #     if w_top is not None:
    #         w_top.setGeometry(x0_top, y0_top, W_TOP, H_TOP)
    #         w_top.raise_()
        
    #     if w_bot is not None:
    #         w_bot.setGeometry(x0_btn, y0_btn, W_BTN, H_BTN)
    #         w_bot.raise_()
            
    #     w_bottom.setAttribute(Qt.WA_TranslucentBackground, True)
    #     w_bottom.setStyleSheet("background: transparent;")

    # def _on_canvas_draw(self, _event):
    #     if not self.axes or not self._overlay_items:
    #         return
    
    #     # --- sizing for overlays ---
    #     W_TOP, H_TOP = 160, 38   # top strip (label + radio)
    #     W_BTN, H_BTN = 24, 24    # bottom button (square clear)
    
    #     # margins inside each axes box
    #     MARGIN_RIGHT = 10
    #     MARGIN_TOP   = 8
    #     MARGIN_BOT   = 8
    
    #     # tiny nudge for the bottom button
    #     NUDGE_LEFT = 20
    #     NUDGE_UP   = 4
    
    #     cW = self.canvas.width()
    #     cH = self.canvas.height()
    
    #     for itm in self._overlay_items:
    #         ax = itm["ax"]
    #         bbox = ax.get_position()
    
    #         # common right edge in pixels
    #         x_right = int(bbox.x1 * cW - MARGIN_RIGHT)
    
    #         # ---- TOP (label + radio) ----
    #         x0_top = x_right - W_TOP
    #         y0_top = int((1.0 - bbox.y1) * cH + MARGIN_TOP)
    #         w_top  = itm.get("widget_top") or itm.get("widget")
    #         if w_top is not None:
    #             w_top.setGeometry(x0_top, y0_top, W_TOP, H_TOP)
    #             w_top.raise_()
    
    #         # ---- BOTTOM (clear button) ----
    #         x0_btn = x_right - W_BTN - NUDGE_LEFT
    #         y0_btn = int((1.0 - bbox.y0) * cH - MARGIN_BOT - H_BTN - NUDGE_UP)
    #         w_bot  = itm.get("widget_bottom")
    #         if w_bot is not None:
    #             w_bot.setGeometry(x0_btn, y0_btn, W_BTN, H_BTN)
    #             w_bot.raise_()
   
    # def _on_canvas_draw(self, _event):
    #     if not self.axes or not self._overlay_items:
    #         return
    
    #     # sizes
    #     W_TOP, H_TOP = 160, 38   # top (label + radio)
    #     W_BTN, H_BTN = 28, 28    # bottom clear button
    
    #     # margins
    #     MARGIN_RIGHT = 10
    #     MARGIN_TOP   = 8
    #     MARGIN_BOT   = 14   # increase bottom margin to keep button inside
    
    #     NUDGE_LEFT = 18
    #     NUDGE_UP   = 0
    
    #     cW = self.canvas.width()
    #     cH = self.canvas.height()
    
    #     for itm in self._overlay_items:
    #         ax = itm["ax"]
    #         bbox = ax.get_position()
    
    #         x_right = int(bbox.x1 * cW - MARGIN_RIGHT)
    
    #         # ---- TOP (label + radio) ----
    #         x0_top = x_right - W_TOP
    #         y0_top = int((1.0 - bbox.y1) * cH + MARGIN_TOP)
    #         w_top  = itm.get("widget_top") or itm.get("widget")
    #         if w_top is not None:
    #             w_top.setGeometry(x0_top, y0_top, W_TOP, H_TOP)
    #             w_top.raise_()
    
    #         # ---- BOTTOM (clear button) ----
    #         # push it *up into* the axes by increasing MARGIN_BOT
    #         x0_btn = x_right - W_BTN - NUDGE_LEFT
    #         y0_btn = int((1.0 - bbox.y0) * cH - MARGIN_BOT - H_BTN - NUDGE_UP)
    #         w_bot  = itm.get("widget_bottom")
    #         if w_bot is not None:
    #             w_bot.setGeometry(x0_btn, y0_btn, W_BTN, H_BTN)
    #             w_bot.raise_()
    
        
    
    # def _on_canvas_draw(self, _event):
    #     if not self.axes or not self._overlay_items:
    #         return
    
    #     W_TOP, H_TOP = 160, 38   # top overlay
    #     W_BTN, H_BTN = 28, 28    # clear button
    
    #     # margins
    #     MARGIN_RIGHT = 20   # was 10 → push both widgets left
    #     MARGIN_TOP   = 8
    #     MARGIN_BOT   = 14
    
    #     cW = self.canvas.width()
    #     cH = self.canvas.height()
    
    #     for itm in self._overlay_items:
    #         ax = itm["ax"]
    #         bbox = ax.get_position()
    
    #         # Right anchor (further inside to avoid clipping)
    #         x_right = int(bbox.x1 * cW - MARGIN_RIGHT)
    
    #         # ---- TOP (label + radio) ----
    #         x0_top = x_right - W_TOP
    #         y0_top = int((1.0 - bbox.y1) * cH + MARGIN_TOP)
    #         w_top = itm.get("widget_top") or itm.get("widget")
    #         if w_top is not None:
    #             w_top.setGeometry(x0_top, y0_top, W_TOP, H_TOP)
    #             w_top.raise_()
    
    #         # ---- BOTTOM (clear button) ----
    #         x0_btn = x_right - W_BTN
    #         y0_btn = int((1.0 - bbox.y0) * cH - MARGIN_BOT - H_BTN)
    #         w_bot = itm.get("widget_bottom")
    #         if w_bot is not None:
    #             w_bot.setGeometry(x0_btn, y0_btn, W_BTN, H_BTN)
    #             w_bot.raise_()
    
    
    # def _on_canvas_draw(self, _event):
    #     """Place top overlay at top-right; align bottom button’s RIGHT edge with the radio’s RIGHT edge."""
    #     if not self.axes or not self._overlay_items:
    #         return
    
    #     # Top overlay bounding size
    #     W_TOP, H_TOP = 200, 38   # allow room for label + radio
    #     # Bottom button size
    #     W_BTN, H_BTN = 24, 24
    
    #     # Insets inside each axes box
    #     AX_RIGHT_PAD = 18   # inset from the axes right edge to avoid clipping
    #     TOP_PAD      = 8
    #     BOTTOM_PAD   = 12
    
    #     # Optional tiny tweaks
    #     ALIGN_TWEAK_X = 0    # +right / -left (pixels)
    #     ALIGN_TWEAK_Y = 0    # +down  / -up   (pixels)
    
    #     cW = self.canvas.width()
    #     cH = self.canvas.height()
    
    #     for itm in self._overlay_items:
    #         ax = itm["ax"]
    #         bbox = ax.get_position()
    
    #         # --------- TOP OVERLAY (label + radio) ---------
    #         x_right = int(bbox.x1 * cW - AX_RIGHT_PAD)      # common right anchor inside the axes
    #         x0_top  = x_right - W_TOP
    #         y0_top  = int((1.0 - bbox.y1) * cH + TOP_PAD)
    
    #         w_top = itm["widget_top"]
    #         w_top.setGeometry(x0_top, y0_top, W_TOP, H_TOP)
    #         w_top.raise_()
    
    #         # --------- Compute radio's RIGHT EDGE in canvas coords ---------
    #         rdo = itm["radio"]
    #         # map the radio widget's top-right to the canvas; that’s our visual right edge for alignment
    #         rdo_right = rdo.mapTo(self.canvas, rdo.rect().topRight()).x()
    
    #         # --------- BOTTOM OVERLAY (clear button) ---------
    #         # Right edges aligned to the radio's right edge.
    #         w_bot = itm["widget_bottom"]
    #         x0_btn = int(rdo_right - W_BTN + ALIGN_TWEAK_X)
    #         y0_btn = int((1.0 - bbox.y0) * cH - BOTTOM_PAD - H_BTN + ALIGN_TWEAK_Y)
    
    #         # Keep it inside the canvas horizontally (safety)
    #         x0_btn = max(0, min(x0_btn, cW - W_BTN))
    
    #         w_bot.setGeometry(x0_btn, y0_btn, W_BTN, H_BTN)
    #         w_bot.raise_()  
    
    def _on_canvas_draw(self, _event):
        if not self.axes or not self._overlay_items:
            return
    
        # Sizes (tweak as needed)
        W_TOP, H_TOP = 160, 38
        W_BTN, H_BTN = 22, 22
        margin_x = 10
        margin_y = 8
    
        cW = self.canvas.width()
        cH = self.canvas.height()
    
        for itm in self._overlay_items:
            ax = itm["ax"]
            bbox = ax.get_position()
    
            # right edge in px
            x_right = int(bbox.x1 * cW - margin_x)
    
            # --- top overlay (label + radio) ---
            x0_top = x_right - W_TOP
            y0_top = int((1.0 - bbox.y1) * cH + margin_y)
            if "widget_top" in itm:
                itm["widget_top"].setGeometry(x0_top, y0_top, W_TOP, H_TOP)
                itm["widget_top"].raise_()
    
            # --- bottom overlay (clear button) ---
            NUDGE_LEFT = 7  # pixels to move left
            x0_btn = x_right - W_BTN - NUDGE_LEFT
            # x0_btn = x_right - W_BTN
            y0_btn = int((1.0 - bbox.y0) * cH - H_BTN - margin_y)
            if "widget_bottom" in itm:
                itm["widget_bottom"].setGeometry(x0_btn, y0_btn, W_BTN, H_BTN)
                itm["widget_bottom"].raise_()
        
    
    
    
    
    
    
    
    
    
    
    
    # def _on_canvas_draw(self, _event):
    #     if not self.axes or not self._overlay_items:
    #         return
    #     # widget size (px) and margins inside axes
    #     W, H = 150, 38
    #     margin_x = 10
    #     margin_y = 8

    #     # canvas pixel size
    #     cW = self.canvas.width()
    #     cH = self.canvas.height()

    #     for itm in self._overlay_items:
    #         ax = itm["ax"]
    #         w  = itm["widget"]
    #         # axes bbox in figure fraction
    #         bbox = ax.get_position()
    #         # convert to pixel rect inside canvas
    #         x0 = int(bbox.x1 * cW - margin_x - W)   # right align
    #         y0 = int((1.0 - bbox.y1) * cH + margin_y)  # top inside axes
    #         w.setGeometry(x0, y0, W, H)

    # ---------------------- active row / selector ----------------------
    def _set_active_row(self, row: int, reattach_cb):
        """
        Make `row` active (mutually exclusive):
        - reattach SpanSelector to that axes
        - bold its border, de-emphasize others
        - update radio (Qt group already exclusive)
        """
        self._active_row = int(row)

        # disconnect old selector
        if self._span is not None:
            try: self._span.disconnect_events()
            except Exception: pass
            self._span = None

        # define the real onselect now (uses current active row)
        def onselect(xmin, xmax):
            if xmin == xmax:
                return
            if len(self._selections[self._active_row]) >= 3:
                return
            lo, hi = sorted([xmin, xmax])
            p = self.axes[self._active_row].axvspan(lo, hi, color="orange", alpha=0.30)
            self._selections[self._active_row].append((lo, hi))
            self._patches[self._active_row].append(p)
            self.canvas.draw_idle()

        # attach to target axes
        ax = self.axes[self._active_row]
        self._span = SpanSelector(
            ax, onselect, direction="horizontal",
            useblit=True, props=dict(alpha=0.3, facecolor="orange"),
            interactive=True, button=MouseButton.LEFT
        )

        # bold active axes border
        for i, ax in enumerate(self.axes):
            lw = 2.2 if i == self._active_row else 0.8
            for sp in ax.spines.values():
                sp.set_linewidth(lw)

        # ensure radio reflects state
        if self._row_group is not None:
            btn = self._row_group.button(self._active_row)
            if btn and not btn.isChecked():
                btn.setChecked(True)

        self.canvas.draw_idle()



