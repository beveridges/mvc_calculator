import matplotlib.pyplot as plt
import numpy as np
import scipy.io
from matplotlib.widgets import SpanSelector
from matplotlib.backend_bases import MouseButton
from functools import partial

# --- Load .mat ---
mat = scipy.io.loadmat(
    "./data/P05_MVC_Left_EXT_CAR_RAD.mat",
    struct_as_record=False, squeeze_me=True
)
tl = mat["P05_MVC_Left_EXT_CAR_RAD"]
data = tl.Analog.Data          # shape: (channels, samples)
labels = tl.Analog.Labels

# --- Figure / axes ---
nrows = min(6, data.shape[0])
npts  = data.shape[1]
x = np.arange(npts)

fig, axes = plt.subplots(nrows, 1, figsize=(12, 2*nrows), sharex=True)
# always treat axes as a flat Python list
if not isinstance(axes, (list, tuple, np.ndarray)):
    axes = [axes]
axes = list(np.atleast_1d(axes))

# Map axes→index (avoids axes.index(...) errors)
ax_to_idx = {ax: i for i, ax in enumerate(axes)}

# Global limits for consistent view
ymin = float(np.min(data[:nrows, :]))
ymax = float(np.max(data[:nrows, :]))
xlim = (0, npts - 1)

# --- State ---
active_row = 0                        # <- set this from your PyQt control
selections = {i: [] for i in range(nrows)}   # list of (xmin, xmax) per row
patches    = {i: [] for i in range(nrows)}   # corresponding axvspan patches
spans      = []                              # keep SpanSelectors alive

def onselect(xmin, xmax, ax_idx):
    """Left-drag selection."""
    # Only allow on the active row
    if ax_idx != active_row:
        return

    # Ignore clicks without drag
    if xmin == xmax:
        return

    # Enforce max 3 selections per active row
    if len(selections[ax_idx]) >= 3:
        print(f"Row {ax_idx}: already has 3 selections, ignoring.")
        return

    # Record & highlight
    lo, hi = (xmin, xmax) if xmin <= xmax else (xmax, xmin)
    selections[ax_idx].append((lo, hi))
    patch = axes[ax_idx].axvspan(lo, hi, color="orange", alpha=0.3)
    patches[ax_idx].append(patch)

    print(f"Row {ax_idx}: selections now {selections[ax_idx]}")
    # keep axes stable
    ax = axes[ax_idx]
    ax.set_xlim(xlim)
    fig.canvas.draw_idle()

def on_mouse_press(event):
    """Shift + Right-click deletes a selection on the active row."""
    # Must be inside one of our axes
    ax = event.inaxes
    if ax not in ax_to_idx:
        return

    # Only act on active row
    ax_idx = ax_to_idx[ax]
    if ax_idx != active_row:
        return

    # Require right button + Shift
    key = (getattr(event, "key", None) or "").lower()
    mods = set(getattr(event, "modifiers", []) or [])
    shift_held = ("shift" in key) or ("shift" in {m.lower() for m in mods})
    if event.button is not MouseButton.RIGHT or not shift_held:
        return

    x_click = event.xdata
    if x_click is None:
        return

    # Find the selection that covers the click
    idx = None
    for j, (lo, hi) in enumerate(selections[ax_idx]):
        if lo <= x_click <= hi:
            idx = j
            break

    if idx is not None:
        # Remove patch and record
        patches[ax_idx][idx].remove()
        patches[ax_idx].pop(idx)
        removed = selections[ax_idx].pop(idx)
        print(f"Row {ax_idx}: removed {removed}; remaining {selections[ax_idx]}")
        fig.canvas.draw_idle()

# --- Draw & attach selectors ---
for i, ax in enumerate(axes):
    ax.plot(x, data[i, :], lw=1.0)
    ax.set_title(str(labels[i]))
    ax.set_ylabel("Amplitude")
    ax.set_ylim(ymin, ymax)
    ax.set_xlim(xlim)
    ax.grid(True, which="both", axis="both", linestyle="--", alpha=0.6)

    span = SpanSelector(
        ax,
        partial(onselect, ax_idx=i),
        direction="horizontal",
        useblit=True,
        props=dict(alpha=0.3, facecolor="orange"),
        interactive=True,
        button=1  # left mouse only
    )
    spans.append(span)  # keep a reference (prevents GC)

axes[-1].set_xlabel("Sample Index")
fig.align_ylabels(axes)
plt.tight_layout()

# Connect shift+right-click deletion
fig.canvas.mpl_connect("button_press_event", on_mouse_press)

plt.show()
