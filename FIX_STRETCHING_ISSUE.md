# Fixing WiX Dialog Bitmap Stretching Issue

## Problem
The dialog bitmap (164×314) is being stretched by WiX to fill the dialog area.

## Root Cause
WiX's `WixUI_Mondo` UI set expects the dialog bitmap to be **493×312 pixels**, NOT 164×314.

The 164×314 size is for older WiX UI sets or different dialog layouts. When WiX receives a bitmap that doesn't match the expected size, it stretches it to fill the allocated space.

## Solution

### Option 1: Resize Dialog Bitmap to 493×312 (Recommended)
1. Resize `MSI_INSTALLER_DIALOG_IMAGE.bmp` to exactly **493×312 pixels**
2. Ensure it's 24-bit BMP format
3. Rebuild the MSI

### Option 2: Use Different UI Set
If you want to keep 164×314, you may need to use a different WiX UI set that supports that size, or create a custom UI.

## Quick Preview Tool

Use `quick_preview_msi.py` to test dialog images without building the full installer:

```bash
python quick_preview_msi.py
```

This creates a minimal MSI (`preview_test.msi`) that you can run to see how the dialog images look.

## Verification

After resizing to 493×312, the dialog bitmap should display at the correct size without stretching.

