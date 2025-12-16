# User Guide

![Build](https://img.shields.io/badge/build-alpha--25.11--01-blueviolet?style=flat-square)
![Version](https://img.shields.io/badge/version-25.12--alpha.01.01-orange?style=flat-square)

## Table of Contents

- [Preamble](#preamble)
- [MVC Calculator Download Options](#mvc-calculator-download-options)
- [Getting Started](#getting-started)
- [File Operations](#file-operations)
- [Working with sEMG Data](#working-with-semg-data)
- [Burst Detection](#burst-detection)
- [Processing and Calculations](#processing-and-calculations)
- [Exporting Results](#exporting-results)
- [Sending Log Files for Support](#sending-log-files-for-support)
- [Batch Processing](#batch-processing)
- [Tips and Best Practices](#tips-and-best-practices)
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
First, sEMG signals representing the MVC are recorded using Noraxon<sup>&#174;</sup>/QualisysAB<sup>&#174;</sup> systems. These signals are then processed in MVC Calculator (see [Figure 1](#fig-mvc)). As noted earlier, the workflow can involve a combination of automatic and manual steps. Once the processing is complete, the final MVC values are saved in XML format.

![MVC recording process](img/how_it_fits_mvc_creation.png){#fig-mvc .mvc-figure}
Figure 1: The Maximum Voluntary Contraction (MVC) recording/calculation process.

#### Stage 2
The MVC XML files are [imported into Max](#importing-mvc-calculator-xml-files-into-max), where they are used on-the-fly to normalize the incoming live sEMG signals. Once normalized, these signals are then used to drive the biofeedback system—for example, to change the triggered sample. [Figure 2](#fig-max) 

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

- ❌ Not portable  
- ❌ Must reinstall to move to another machine  
- ❌ Requires admin rights  

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

1. Click **Import MAT files** button or use <kbd>Ctrl</kbd> + <kbd>L</kbd> (or File → Import MAT files)
2. Navigate to your `.mat` file location
3. Select one or more files (for batch processing)
4. Click **Open**

The application will load and display your sEMG data in the plotting area.

---

## File Operations

### Importing MAT Files

MVC Calculator supports MATLAB `.mat` files exported from the IMM **QualisysAB<sup>&#174;</sup>** QTM / **Noraxon<sup>&#174;</sup>** sEMG system.

To load mat files:

1. Click the **Import MAT files** button or use <kbd>Ctrl</kbd> + <kbd>L</kbd> (or File → Import MAT files)
2. Click the **Select files** button
3. Select one or more `.mat` files
4. With the files selected, you can choose Remove Selected to delete only those files, or Clear Files to remove all files
5. When you are happy with the siles you have selected, use the **Import Files** button
3. The application will automatically detect and load the sEMG data
4. Each file will appear as a separate tab in the plotting area

### Importing XML Files

To load previously saved MVC calculations:

1. Click the **Import XML file** button or use <kbd>Ctrl</kbd> + <kbd>X</kbd> (or File → Import XML file or use the shortcut )
2. Navigate to your saved `.xml` file
3. Click **Open**

This will restore your previous burst selections and calculated MVC values.

### Exporting Results

After processing your data:

1. Click **Export XML file** or use <kbd>Ctrl</kbd> + <kbd>E</kbd> (or File → Export XML file)
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

If you’ve loaded multiple files (e.g., 4 or 6 sensors), the interface displays four key elements (see [Figure 4](#fig-working_with_semg_ui):

1. **Tabs** – Each sensor appears as a tab at the top of the plotting area.  
2. **EMG channel selection buttons** – These highlighted buttons allow you to select the desired EMG channel.  
3. **Clear all selections button** – Clears any burst selections made in the active EMG channel.  
4. **Active EMG channel** – The currently selected sensor is highlighted with a bold rectangle around the corresponding plot.


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

- **Bandpass Filtering**: Removes noise outside the 10-500 Hz range (default)
- **RMS Calculation**: Computes root mean square for signal smoothing
- **Hampel Filtering**: Removes outliers and artifacts

These processing steps are applied automatically when you load data.

---

## Burst Detection

### Energy Detection Tool

The **Energy Detection** tool automatically scans your signal and highlights regions that are likely to contain MVC bursts.  To use the Energy Detection Tool you must: 

1. Use the **EMG channel select** button ![selection button](img/selection_button.png) to make your channel selection
2. Click the **Energy Detection** button 
3. Three orange selections will be made automagically
4. At this point, you can either **Calculate MVC** for the selected channel or refine the selections manually.

!!! Note
	Selection refinement is done by Shift-clicking to delete the current selection and creating a new one.

### Manual Burst Selection

1. **Click and Drag**: Click on the plot and drag to select a burst region
2. **Visual Feedback**: Selected regions are highlighted in orange
3. **Multiple Selections**: Multiple bursts can be selected for each sensor. The selection limit is defined by the measurement protocol and managed through the BEST_OF variable.
4. **Remove a Single Selection**:  Shift-click (right) to remove a single selection
4. **Clear All Selections**: Use the clear button ![broom icon](img/broom_icon.png) to remove all selections

!!! Note Measurement protocol and Burst selection
	MVC Calculator limits the number of bursts you can select. The default is 3 bursts, but you can change this by editing the BEST_OF variable in `./config/defaults.py.`
	
	
<!-- ### Selecting Multiple Bursts

For the "best of 3" protocol:

1. Select your **first** burst region
2. Select your **second** burst region
3. Select your **third** burst region
4. The application will automatically identify the maximum value

You can select more than 3 bursts if needed - the system will find the maximum. -->

---

## Processing and Calculations

### Understanding the MVC Calculation

The MVC (Maximum Voluntary Contraction) calculation is performed in the following stages:

1. The signal is processed, producing a value that represents muscle activity at each time point.
2. For each selected burst region, this signal is divided into 500 ms windows. The mean value of each window is calculated, and the highest of these means is taken as the Maximum Contraction or **Maximum Voluntary Contraction (MVC)**.

### Processing a single file 

With a single .mat file loaded (one tab) and your bursts selected:

1.  Review your selections in the plotting area
2.  Press the **Calculate MVC** button
3.  The software will then:
	- Compute the MVC value (usually the mean amplitude of the highest 500 ms window, as described by Konrad, 2005)
	- Output the results to the console
	
!!! note
	If you only need the MVC values for this single sensor (one .mat file), you can now press Export XML file (or use File → Export XML file) to finish the process.


### Batch Processing

Batch processing lets you run the MVC calculation across all sensors at once. Each sensor appears in a separate tab (one tab per .mat file), so you can easily navigate and verify the data before or after running the batch.

1. Repeat the '[Processing a single file](#processing-a-single-file)' for each tab (.mat file) 
2. **Red indicators** will show which sensors still need selections
3. Once all sensors have selections, click **Process**
4. Results are calculated for all sensors simultaneously


1. Select bursts for each sensor
   Move through the tabs and repeat the steps described in [Processing a single file](#processing-a-single-file) for each .mat file.  This involves reviewing the signal in the plotting area and selecting the required burst regions.

2. Use the red indicators as a guide
   Tabs with red indicators show which sensors still require burst selections.
   Tabs lose the indicator once valid selections have been made (see[Figure 5](#fig-red-in-tabs)

3. Ensure all sensors have valid selections
   Batch processing can only begin once every sensor (every tab) has at least one valid burst selection.

4. Click the **Batch calculate MVC** button
   Once all selections are complete, press Process to run the MVC calculation for all sensors simultaneously.

5. View results
   The software will:
   - Compute the MVC value for each sensor independently
   - Display the results in the console
   - Prepare the output for export (e.g., XML file generation)


<figure class="screenshot" id="fig-red-in-tabs">

<img
    src="img/red_in_tabs.png"
    data-full="img/red_in_tabs.png"
    width="700"
    alt="MVC Calculator UI"
    class="lightbox-trigger"
  />
<figcaption aria-hidden="true">
</figcaption>
Figure 5: If you forget to make a burst selection during batch processing, any tab without a valid selection is marked with a red dot.
</figure>

!!! note
    If you only need MVC values from one sensor (one .mat file), you may bypass batch processing and directly select Export XML file after computing MVC for that sensor.

---

## Exporting Results

### XML Export Format

The exported XML file contains:

```xml
<?xml version='1.0' encoding='utf-8'?>
<MVCResults>
	<ExportInfo>
		<Date>2025-12-06</Date>
		<Time>21:28:24</Time>
	</ExportInfo>
	<File name="P05_MVC_Right_FLEX_DIG_SUP.mat">
		<Row>3</Row>
		<MVC>804.7818496050679</MVC>
		<Bursts>
			<Burst id="1">
				<Start>16219</Start>
				<End>39555</End>
			</Burst>
			<Burst id="2">
				<Start>91265</Start>
				<End>115474</End>
			</Burst>
			<Burst id="3">
				<Start>196201</Start>
				<End>211145</End>
			</Burst>
		</Bursts>
	</File>
</MVCResults>
```

### Using Exported Data

The exported XML can be:

- **Imported back** into MVC Calculator for review
- **Used in other analysis software** that supports XML
- **[Imported into the MuscleMonitor Max patch](#importing-mvc-calculator-xml-files-into-max)** for real-time sEMG signal normalisation

---

## Sending Log Files for Support

If you encounter issues or need technical support, you can send your session log file directly from MVC Calculator. This helps support staff diagnose problems more quickly.

To send a log file:

  1. Click the **Send log file** button in the console area
  2. A dialog will appear where you can optionally add a message describing the issue or any relevant details
  3. Enter your message (optional) and click **OK**
  4. A progress indicator will show while the email is being sent
  5. You will receive a confirmation message: "The email was sent successfully"

The log file and your optional message will be sent to the support team for analysis.

<figure class="screenshot" id="fig-send-log">

<img
    src="img/send_log_dialog.png"
    data-full="img/send_log_dialog.png"
    width="400"
    alt="Send Log File Dialog"
    class="lightbox-trigger"
  />
<figcaption aria-hidden="true">
</figcaption>
Figure 7: The Send Log File dialog allows you to add an optional message before sending your session log to support.
</figure>

---

## Importing MVC Calculator XML Files into Max
This part of the MuscleMonitor interface allows you to load the MVC values generated by MVC Calculator. These values are used as a normalizing factor so that incoming EMG signals can be normalized in real time.

As noted earlier, each .mat file contains recordings from all muscles included in the measurement protocol. For example, if the protocol involves four muscles, each .mat file will always contain four signal channels.

In MuscleMonitor, you must therefore match each target muscle to the correct channel. This section of the UI is dedicated to making that mapping clear and easy to configure (see[Figure 6](#max_mvc_coeffs).

<figure class="screenshot" id="max_mvc_coeffs">

<img
    src="img/max_mvc_coeffs.png"
    data-full="img/max_mvc_coeffs.png"
    width="700"
    alt="MAX"
    class="lightbox-trigger"
  />
<figcaption aria-hidden="true">
</figcaption>
Figure 6: MuscleMonitor Max interface showing the mvc coefficients section
</figure>


!!! note
	Even though the dropdown menu automatically populates the MVC value, this value is not fixed. You can make fine adjustments by editing the number box in the usual way.


<!-- ## Batch Processing

### Processing Multiple Files

To process multiple sensor files at once:

1. **Load all files**: Use Import MAT files and select multiple files (or load them one by one)
2. **Switch between sensors**: Use the tabs or radio buttons
3. **Select bursts for each**: Make sure each sensor has at least one burst selected
4. **Process all**: Click Process to calculate MVC values for all sensors -->

<!-- ### Visual Indicators

- **Red Indicator**: Sensor needs burst selection before processing
- **Console Messages**: Check the console for status of each sensor -->

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

## References

Konrad, P. (2005). *The ABC of EMG: A Practical Introduction to
Kinesiological Electromyography.* Noraxon<sup>&#174;</sup> Inc.

---

## Additional Resources

- [License Information](license.md)
- [Troubleshooting Guide](troubleshooting.md)
- [File Formats](file-formats.md)
- [Keyboard Shortcuts](keyboard-shortcuts.md)

