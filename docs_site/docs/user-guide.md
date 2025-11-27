# User Guide

## Table of Contents

- [Getting Started](#getting-started)
- [File Operations](#file-operations)
- [Working with sEMG Data](#working-with-semg-data)
- [Burst Detection](#burst-detection)
- [Processing and Calculations](#processing-and-calculations)
- [Exporting Results](#exporting-results)
- [Batch Processing](#batch-processing)
- [Tips and Best Practices](#tips-and-best-practices)

---

## Getting Started

### First Launch

When you first launch MVC Calculator, you'll see:

1. **Menu Bar** - File and Help menus at the top
2. **Plotting Area** - Large central area for visualizing sEMG signals
3. **Console** - Bottom panel showing log messages and status
4. **Control Buttons** - Main action buttons on the interface

### Loading Your First File

1. Click **Import MAT files** button or use `Ctrl+L` (or File → Import MAT files)
2. Navigate to your `.mat` file location
3. Select one or more files (for batch processing)
4. Click **Open**

The application will load and display your sEMG data in the plotting area.

---

## File Operations

### Importing MAT Files

MVC Calculator supports MATLAB `.mat` files from:
- **Qualisys** motion capture systems
- **Noraxon** EMG systems
- Other systems that export standard MATLAB format

**Keyboard Shortcut**: `Ctrl+L`

**Process**:
1. Click **Import MAT files** or use the menu: File → Import MAT files
2. Select one or more `.mat` files
3. The application will automatically detect and load the sEMG data
4. Each file will appear as a separate tab in the plotting area

### Importing XML Files

To load previously saved MVC calculations:

1. Click **Import XML file** or use `Ctrl+X` (or File → Import XML file)
2. Navigate to your saved `.xml` file
3. Click **Open**

This will restore your previous burst selections and calculated MVC values.

### Exporting Results

After processing your data:

1. Click **Export XML file** or use `Ctrl+E` (or File → Export XML file)
2. Choose a location and filename
3. Click **Save**

The exported XML contains:
- Selected burst regions for each sensor
- Calculated MVC values
- Metadata (timestamps, file paths, etc.)

---

## Working with sEMG Data

### Understanding the Display

When you load a `.mat` file, MVC Calculator displays:

- **Signal Plot**: The raw or processed sEMG signal over time
- **Sensor Tabs**: If multiple sensors are loaded, each appears as a tab
- **Time Axis**: Horizontal axis showing time in seconds
- **Amplitude Axis**: Vertical axis showing signal amplitude

### Navigating Multiple Sensors

If you've loaded multiple files (e.g., 4 or 6 sensors):

- **Tabs**: Each sensor appears as a tab at the top of the plotting area
- **Radio Buttons**: Use the radio buttons to switch between sensors
- **Active Tab**: The currently selected sensor is highlighted

### Signal Processing

MVC Calculator automatically processes sEMG signals using:

- **Bandpass Filtering**: Removes noise outside the 20-450 Hz range (default)
- **RMS Calculation**: Computes root mean square for signal smoothing
- **Hampel Filtering**: Removes outliers and artifacts

These processing steps are applied automatically when you load data.

---

## Burst Detection

### Energy Detection Tool

The **Energy Detection** tool helps you locate candidate MVC bursts automatically:

1. Click the **Energy Detection** button (or use the menu)
2. Adjust the detection parameters:
   - **Minimum Silence Duration**: Time between bursts (default: 80ms)
   - **Minimum Sound Duration**: Minimum burst length (default: 200ms)
3. Click **Detect** or **Apply**

The tool will highlight potential burst regions on the plot.

### Manual Burst Selection

After using Energy Detection (or instead of it):

1. **Click and Drag**: Click on the plot and drag to select a burst region
2. **Visual Feedback**: Selected regions are highlighted
3. **Multiple Selections**: You can select multiple bursts per sensor
4. **Clear Selection**: Use the clear button (broom icon) to remove a selection

### Selecting Multiple Bursts

For the "best of 3" protocol:

1. Select your **first** burst region
2. Select your **second** burst region
3. Select your **third** burst region
4. The application will automatically identify the maximum value

You can select more than 3 bursts if needed - the system will find the maximum.

---

## Processing and Calculations

### Running the MVC Calculation

Once you've selected bursts for all sensors:

1. Review your selections in the console/log area
2. Click the **Process** or **Calculate** button
3. The application will:
   - Extract the maximum value from each sensor's selected bursts
   - Calculate the MVC value (typically the peak RMS value)
   - Display results in the console

### Understanding MVC Values

The MVC (Maximum Voluntary Contraction) value represents:
- The **peak amplitude** from your selected burst regions
- Used for **normalization** in subsequent analyses
- Typically the **highest value** from your "best of 3" trials

### Batch Processing

When processing multiple sensors:

1. **Select bursts for each sensor** using the tabs
2. **Red indicators** will show which sensors still need selections
3. Once all sensors have selections, click **Process**
4. Results are calculated for all sensors simultaneously

---

## Exporting Results

### XML Export Format

The exported XML file contains:

```xml
<mvc_results>
  <sensor name="EMG_1">
    <burst start="1.23" end="2.45" mvc_value="0.456"/>
    <burst start="5.67" end="6.89" mvc_value="0.512"/>
    <burst start="10.11" end="11.33" mvc_value="0.489"/>
    <max_mvc>0.512</max_mvc>
  </sensor>
  <!-- Additional sensors... -->
</mvc_results>
```

### Using Exported Data

The exported XML can be:
- **Imported back** into MVC Calculator for review
- **Used in other analysis software** that supports XML
- **Archived** for record-keeping and reproducibility

---

## Batch Processing

### Processing Multiple Files

To process multiple sensor files at once:

1. **Load all files**: Use Import MAT files and select multiple files (or load them one by one)
2. **Switch between sensors**: Use the tabs or radio buttons
3. **Select bursts for each**: Make sure each sensor has at least one burst selected
4. **Process all**: Click Process to calculate MVC values for all sensors

### Visual Indicators

- **Green/Active Tab**: Sensor has burst selections
- **Red Indicator**: Sensor needs burst selection before processing
- **Console Messages**: Check the console for status of each sensor

---

## Tips and Best Practices

### Data Quality

- **Check Signal Quality**: Look for clean, artifact-free regions
- **Avoid Movement Artifacts**: Select bursts during stable contractions
- **Consistent Electrode Placement**: Ensure electrodes are placed consistently across sessions

### Selection Strategy

- **Select Clear Peaks**: Choose regions with obvious maximum contractions
- **Avoid Noise**: Don't select regions with electrical noise or artifacts
- **Consistent Window Size**: Try to select bursts of similar duration

### Workflow Efficiency

1. **Use Energy Detection First**: Let the tool find candidate regions
2. **Fine-tune Manually**: Adjust selections as needed
3. **Review Before Processing**: Check all sensors have selections
4. **Save Frequently**: Export XML files to preserve your work

### Troubleshooting

- **No Signal Displayed**: Check that your `.mat` file contains valid sEMG data
- **Can't Select Bursts**: Ensure data is loaded and displayed correctly
- **Processing Fails**: Verify all sensors have at least one burst selected
- **See the [Troubleshooting Guide](troubleshooting.md)** for more help

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Import MAT files | `Ctrl+L` |
| Import XML file | `Ctrl+X` |
| Export XML file | `Ctrl+E` |
| Exit Application | `Ctrl+Q` |

For a complete list, see [Keyboard Shortcuts](keyboard-shortcuts.md).

---

## Additional Resources

- [Troubleshooting Guide](troubleshooting.md)
- [File Formats](file-formats.md)
- [License Information](license.md)
- [Measurement Protocol](index.md#measurement-protocol-suggestions)

