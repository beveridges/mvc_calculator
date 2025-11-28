# User Guide

## Table of Contents

- [Preamble](#preamble)
- [MVC Calculator Download Options](#mvc-calculator-download-options)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [File Operations](#file-operations)
- [Working with sEMG Data](#working-with-semg-data)
- [Burst Detection](#burst-detection)
- [Processing and Calculations](#processing-and-calculations)
- [Exporting Results](#exporting-results)
- [Batch Processing](#batch-processing)
- [Tips and Best Practices](#tips-and-best-practices)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Additional Resources](#additional-resources)

---

## Preamble

This section provides important context and background information before you begin using MVC Calculator.

### What is MVC Calculator?

MVC Calculator is software that provides a **visual** method of idenitfying and annotating bursts in sEMG signals.


### Why do we need to manually identify MVC bursts?

You might expect a process like burst identification to be handled automatically by software. However, during the first drum study we encountered sEMG files that were too irregular for full automation. These irregularities included recordings with extra bursts (caused by false starts or miscounts), duplicate files for the same participant, and excessive noise.
To address this, the MVC Calculator allows users to manually define MVC bursts, ensuring a method that is ***reliable, repeatable, and valid***.

!!! summary
	For all intents and purposes, using MVC Calculator is a one-and-done process: MATLAB .mat files go in, and an XML file with the MVC values comes out. In about 90% of cases, that’s the entire workflow.
	The remaining 10% can be frustrating due to irregular or problematic files—but MVC Calculator is designed to make handling that difficult 10% far more manageable.

### How MVC calculator fits into the experimental workflow

The implementation of MVC signals is a two-stage process.   

#### Stage 1
First, sEMG signals representing the MVC are recorded using Noraxon/Qualisys systems. These signals are then processed in MVC Calculator (see [Figure 1](#fig-mvc)). As noted earlier, the workflow can involve a combination of automatic and manual steps. Once the processing is complete, the final MVC values are saved in XML format.

![MVC recording process](img/how_it_fits_mvc_creation.png){#fig-mvc .mvc-figure}
Figure 1: The Maximum Voluntary Contraction (MVC) recording process.

#### Stage 2
The MVC XML files are imported into Max, where they are used on-the-fly to normalize the incoming live sEMG signals. Once normalized, these signals are then used to drive the biofeedback system—for example, to change the triggered sample. [Figure 2](#fig-max) 

![MVC in Max](img/max_in_mvc.png){#fig-max .mvc-figure}
Figure 2: MVC values being used in Max.

---

## MVC Calculator Download Options

MVC Calculator is available in four versions—two for **Windows** and two for **Linux**.  
Each version has its own advantages depending on your workflow and system requirements.

The latest builds for all platforms can be downloaded from:  
<https://downloads.moviolabs.com/MVC_Calculator/releases/>

!!! info "Download access"
    The release archive is password-protected. Your **login credentials** (username and download password) will be sent to you via email.  
	
    MVC Calculator uses a hardware-locked license system.  Refer to the [License System](license.md) section for full details.

---

### Windows Versions

#### Windows Installer (.msi) - RECOMMENDED

**Best for:**

- Users who want full system integration  
- Fast startup and automatic shortcuts  
- A clean installation on a primary machine  

**Equivalent to:**  
A standard Windows installer (similar to installing Chrome)

**Installation:**

- Double click the `.msi` file to run
- Installs into `Program Files`  
- Creates Start Menu entries  
- Performs heavy initialization once during installation  

**Pros**

- ✔ Fast startup  
- ✔ Start Menu + Desktop integration  
- ✔ Clean, stable installation  
- ✔ Easy to uninstall  

**Cons**

- ❌ Requires admin rights  
- ❌ Not portable  
- ❌ Must reinstall to move to another machine  

---


#### Windows Portable Version (ZIP)

**Best for:**

- Users who prefer a portable, no-install version  
- Running MVC Calculator from USB drives or multiple machines  
- Systems without admin rights  

**Equivalent to:**  
Portable `.exe` (standalone Windows program)

**Installation:**

- Download the `.zip` file  
- Extract it  
- Run `MVC_Calculator.exe` directly  
- No installation or registry changes  
- Settings remain inside the folder  

**Pros**

- ✔ No installation required  
- ✔ Fully portable  
- ✔ Easy to delete or move  
- ✔ No admin privileges required  

**Cons**

- ❌ Slightly slower startup  
- ❌ **Siginificantly** larger memory footprint 
- ❌ Not added to Start Menu automatically  
 

---


### Linux Versions

#### Linux .deb Package - RECOMMENDED

**Best for:**

- Ubuntu, Debian, Linux Mint users  
- Users who want a fully installed, integrated application  
- Those who prefer package-managed software  

**Equivalent to:**  
A standard `.deb` installer (used with APT)

**Installation:**

Install with:

```bash
sudo dpkg -i MVC_Calculator.deb
```

- Adds menu entries automatically  
- Application files stored under system directories  
- Managed by the OS package system  

**Pros**

- ✔ Clean OS integration  
- ✔ Desktop entry and icons included  
- ✔ Managed by package tools  
- ✔ Dependency handling  

**Cons**

- ❌ Requires sudo  
- ❌ Only works on Debian-based systems  
- ❌ Not portable  

---

#### Linux AppImage

**Best for:**

- Users on **any** Linux distribution  
- Portable workflows  
- Running without installation  

**Equivalent to:**  
A portable Linux executable

**Installation:**

- Download the `.AppImage`  
- Make it executable:

```bash
chmod +x MVC_Calculator.AppImage
./MVC_Calculator.AppImage
```

- Runs as a standalone application  
- Contains all required libraries  

**Pros**

- ✔ Runs on almost any distro  
- ✔ No installation required  
- ✔ Portable  
- ✔ No sudo required  

**Cons**

- ❌ Larger file size  
- ❌ Minimal desktop integration  
- ❌ No automatic updates  
- ❌ Slightly slower startup  

---

### Summary Table

| Version         | Platform | Best for                           |
|-----------------|----------|------------------------------------|
| Portable ZIP    | Windows  | No-install, portable use           |
| MSI Installer   | Windows  | Fast startup + full integration    |
| .deb Package    | Linux    | Ubuntu/Debian system installation  |
| AppImage        | Linux    | Any distro; portable option        |


!!! note
	During the alpha phase of development, MVC Calculator runs with a terminal window open in the background.  This is intentional and serves as a troubleshooting aid, displaying the same diagnostic output shown in the application's console window (see [Figure 3](#fig-ui)).

---

## Getting Started

### First Launch

When you first launch MVC Calculator, you'll see:

1. **Menu Bar** - File and Help menus at the top
2. **Plotting Area** - Large central area for visualizing sEMG signals
3. **Console** - Bottom panel showing log messages and status
4. **Control Buttons** - Main action buttons on the interface


<figure class="screenshot" id="fig-ui">

<img
    src="img/full_ui.png"
    data-full="img/full_ui.png"
    width="700"
    alt="MVC Calculator UI"
    class="lightbox-trigger"
  />
<figcaption aria-hidden="true">

Figure 3: The MVC Calculator UI.
</figcaption>
</figure>




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

- **Qualisys** QTM / **Noraxon** EMG systems

**Keyboard Shortcut**: `Ctrl+L`

To load mat files:

1. Click **Import MAT files** or use `Ctrl+L` (or File → Import MAT files)
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

### Understanding the User Interface

When you load a `.mat` file, MVC Calculator displays:

- **Signal Plot**: The raw or processed sEMG signal over time
- **Sensor Tabs**: If multiple sensors are loaded, each appears as a tab
- **Time Axis**: Horizontal axis showing time in seconds
- **Amplitude Axis**: Vertical axis showing signal amplitude

<!-- Each tab represents an MVC recording for a specific muscle.  However, generally all sensors are fitted to the participant during the MVC recording process.  This means that, in addition to the target EMG channel, all otaher channels will be present in the mat file.   -->

### Navigating Multiple Sensors

If you've loaded multiple files (e.g., 4 or 6 sensors):

1. **Tabs** – Each sensor appears as a tab at the top of the plotting area.  
2. **EMG channel selection buttons** – These highlighted buttons allow you to select the desired EMG channel.  
3. **Clear all selections button** – Clears any burst selections made in the active EMG channel.  
4. **Active EMG channel** – The currently selected sensor is highlighted.


<figure class="screenshot" id="fig-working_with_semg_ui">

<img
    src="img/working_with_semg_ui.png"
    data-full="img/working_with_semg_ui.png"
    width="700"
    alt="MVC Calculator UI"
    class="lightbox-trigger"
  />
<figcaption aria-hidden="true">
</figcaption>
Figure 4: MVC Calculator interface displaying sEMG signals extracted from the loaded .mat files.
</figure>


!!! extremelyimportant "EXTREMELY IMPORTANT"
    In most studies, each participant will be fitted with **all** sensors required by the measurement protocol (typically 4 or 6). As a result, every `.mat` file contains **all** sEMG channels for that recording, not just the target muscle.

    Occasionally, recording errors or mislabelling can make it unclear whether the sensor with the highest amplitude truly corresponds to the target muscle indicated by the filename. MVC Calculator provides a quick visual method to verify that the `.mat` filename matches the correct sensor channel for the intended muscle.

    When used alongside a well-defined experimental protocol, MVC Calculator greatly reduces uncertainty and ensures the correct pairing between sensor channels and muscle names.



<!-- If you've loaded multiple files (e.g., 4 or 6 sensors):

1. **Tabs**: Each sensor appears as a tab at the top of the plotting area
2. **EMG channel selection button**: The buttons highlited help the user select the required EMG channel.  
3. **Clear all selections button**:  Clears any burst selections made in the active cEMG channel.	
4. **Active EMG channel**: The currently selected sensor is highlighted

!!!extremelyimportant EXTREMELY IMPORTANT
	Usually, a participant will be fitted with **every** sensor required by the measure protocol (in our case either, 4 or 6 sensors).  This means that, as well as target muscle sensor, all others sensors will also be recorded.  Put simply, every .mat file will have 4 or 6 channels of sEMG data **for every recording**.  There are times that errors cause some confusion about whether the actual sensor that has the highest amplitude actually correspond the the target muscle, the MATLAB file name (.mat).   MVC Calculator provides a quick and dirty visual method that can be used to verify the name of the mat file matches the sensor name of the target muscle.  In conjunction with an agreed upon experimental design, MVC Calculator remove any doubt as to which sensor channel belongs to wihch muscle.
 -->
### Signal Processing

MVC Calculator automatically processes sEMG signals using:

- **Bandpass Filtering**: Removes noise outside the 50-500 Hz range (default)
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

