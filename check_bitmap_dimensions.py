#!/usr/bin/env python3
"""
Quick script to check bitmap dimensions and format
"""
from pathlib import Path
from PIL import Image
import sys

def check_bitmap(file_path):
    """Check bitmap file dimensions and format"""
    path = Path(file_path)
    if not path.exists():
        print(f"ERROR: File not found: {file_path}")
        return False
    
    try:
        img = Image.open(path)
        width, height = img.size
        mode = img.mode
        format_name = img.format
        
        print(f"\nFile: {path.name}")
        print(f"  Dimensions: {width} × {height} pixels")
        print(f"  Format: {format_name}")
        print(f"  Color Mode: {mode}")
        
        # Check if it's the expected size
        if width == 164 and height == 314:
            print(f"  ✓ Dimensions match expected 164×314")
        elif width == 493 and height == 312:
            print(f"  ⚠ Dimensions are 493×312 (alternative standard size)")
        else:
            print(f"  ✗ WARNING: Unexpected dimensions!")
            print(f"    Expected: 164×314 or 493×312")
        
        # Check format
        if format_name == "BMP":
            print(f"  ✓ Format is BMP")
        else:
            print(f"  ⚠ Format is {format_name} (BMP recommended)")
        
        # Check color depth
        if mode == "RGB":
            print(f"  ✓ Color mode is RGB (24-bit)")
        elif mode == "RGBA":
            print(f"  ⚠ Color mode is RGBA (has alpha channel - may cause issues)")
        else:
            print(f"  ⚠ Color mode is {mode}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Could not read image: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_bitmap_dimensions.py <bitmap_file>")
        sys.exit(1)
    
    check_bitmap(sys.argv[1])

