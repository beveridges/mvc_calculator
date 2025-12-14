# File Formats

## Supported File Types

MVC Calculator supports the following file formats:

1. **MATLAB<sup>&#174;</sup> `.mat` files** - For importing sEMG data
2. **XML files** - For importing/exporting MVC calculation results

---

## MATLAB<sup>&#174;</sup> .mat Files

### Overview

MVC Calculator imports sEMG data from MATLAB<sup>&#174;</sup> `.mat` files, exported from the IMM **QualisysAB<sup>&#174;</sup>**/**Noraxon<sup>&#174;</sup>** motion capture configuration.



```

### Data Format

The sEMG data should be:
- **Time series data**: Array or matrix of signal values
- **Sampling frequency**: Default assumed 1500 Hz (configurable)
- **Units**: Typically in millivolts (mV) or microvolts (µV)

### Loading Multiple Files

You can load:
- **Single file**: One sensor's data
- **Multiple files**: 4 or 6 sensors (typical configuration)
- **Batch processing**: All files processed together

### File Size Considerations

- **Small files** (< 10 MB): Load quickly
- **Medium files** (10-100 MB): May take a few seconds
- **Large files** (> 100 MB): May take longer, be patient

### Common Issues

**Problem**: File loads but shows error
- **Solution**: Verify file is valid MATLAB<sup>&#174;</sup> format, try opening in MATLAB<sup>&#174;</sup> first

**Problem**: No signal displayed
- **Solution**: Check that data variable is properly named and contains time series data

**Problem**: Wrong sampling frequency
- **Solution**: Adjust `DEFAULT_SEMG_FREQUENCY` in `config/defaults.py`

---

## XML Export Format

### Overview

MVC Calculator exports results in XML format, containing:
- Selected burst regions for each sensor
- Calculated MVC values
- Metadata (timestamps, file paths, etc.)

### XML Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mvc_results>
  <metadata>
    <version>1.0</version>
    <timestamp>2024-01-15T10:30:00</timestamp>
    <application>MVC Calculator</application>
  </metadata>
  
  <sensor name="EMG_1" source_file="path/to/file1.mat">
    <burst>
      <start_time>1.23</start_time>
      <end_time>2.45</end_time>
      <mvc_value>0.456</mvc_value>
      <rms_value>0.445</rms_value>
    </burst>
    <burst>
      <start_time>5.67</start_time>
      <end_time>6.89</end_time>
      <mvc_value>0.512</mvc_value>
      <rms_value>0.501</rms_value>
    </burst>
    <burst>
      <start_time>10.11</start_time>
      <end_time>11.33</end_time>
      <mvc_value>0.489</mvc_value>
      <rms_value>0.478</rms_value>
    </burst>
    <max_mvc>0.512</max_mvc>
    <selected_burst_index>1</selected_burst_index>
  </sensor>
  
  <sensor name="EMG_2" source_file="path/to/file2.mat">
    <!-- Additional sensors... -->
  </sensor>
</mvc_results>
```

### XML Elements

#### Root Element: `<mvc_results>`
- Contains all MVC calculation results

#### Metadata Section: `<metadata>`
- **`<version>`**: XML format version
- **`<timestamp>`**: When the calculation was performed
- **`<application>`**: Application name and version

#### Sensor Section: `<sensor>`
- **`name`**: Sensor identifier (e.g., "EMG_1", "EMG_2")
- **`source_file`**: Path to original `.mat` file

#### Burst Section: `<burst>`
- **`<start_time>`**: Start time of burst (seconds)
- **`<end_time>`**: End time of burst (seconds)
- **`<mvc_value>`**: Calculated MVC value for this burst
- **`<rms_value>`**: RMS value for this burst

#### Summary: `<max_mvc>`
- Maximum MVC value from all bursts (the "best of 3" result)
- **`<selected_burst_index>`**: Which burst had the maximum value (0-indexed)

### Importing XML Files

When you import an XML file:
- Burst selections are restored
- MVC values are restored
- You can review and modify selections
- You can re-export if needed

### XML Compatibility

- **Version Compatibility**: XML files from older versions may not be fully compatible
- **Backward Compatibility**: Newer versions should read older XML files
- **Forward Compatibility**: Older versions may not read newer XML formats

---

## File Naming Conventions

### Recommended Naming

For `.mat` files:
- Use descriptive names: `Participant01_Sensor1.mat`
- Include sensor information: `EMG_Leg_Left.mat`
- Avoid special characters: Use underscores instead of spaces

For XML exports:
- Include participant ID: `Participant01_MVC_Results.xml`
- Include date: `MVC_Results_2024-01-15.xml`
- Be descriptive: `Session1_Baseline_MVC.xml`

### File Organization

Recommended folder structure:
```
Data/
├── Participant01/
│   ├── Sensor1.mat
│   ├── Sensor2.mat
│   ├── Sensor3.mat
│   ├── Sensor4.mat
│   └── Results/
│       └── Participant01_MVC_Results.xml
├── Participant02/
│   └── ...
```

---

## Data Processing

### Signal Processing Pipeline

When you load a `.mat` file, MVC Calculator automatically:

1. **Loads raw data** from the file
2. **Applies bandpass filter** (20-450 Hz default)
3. **Calculates RMS** (root mean square)
4. **Applies Hampel filter** (removes outliers)
5. **Displays processed signal** in the plot

### Processing Parameters

Default parameters (configurable in `config/defaults.py`):
- **Sampling Frequency**: 1500 Hz
- **Bandpass Filter**: 20-450 Hz
- **RMS Window**: 50 ms
- **Hampel Filter**: 50 ms window, k=3.0

---

## Export Options

### What Gets Exported

When you export to XML:
- ✅ All selected burst regions
- ✅ Calculated MVC values
- ✅ Maximum MVC value (best of 3)
- ✅ Source file paths
- ✅ Timestamps and metadata

### What Doesn't Get Exported

- ❌ Raw signal data (too large)
- ❌ Plot images (export separately if needed)
- ❌ Processing parameters (use defaults or document separately)

---

## Best Practices

### File Management

1. **Keep Originals**: Always keep original `.mat` files
2. **Regular Exports**: Export XML files frequently during analysis
3. **Version Control**: Use descriptive names with dates/versions
4. **Backup**: Keep backups of both `.mat` and `.xml` files

### Data Quality

1. **Verify Files**: Check files open correctly before processing
2. **Check Sampling Rate**: Ensure consistent sampling rates
3. **Document Settings**: Note any custom processing parameters
4. **Validate Results**: Review exported XML for correctness

### Workflow

1. **Load** → Import `.mat` files
2. **Process** → Select bursts and calculate MVC
3. **Export** → Save XML results
4. **Archive** → Store both original and processed data

---

## Troubleshooting File Issues

### .mat File Issues

See [Troubleshooting Guide](troubleshooting.md) for:
- Files that won't load
- Incorrect data display
- Format compatibility issues

### XML File Issues

- **Can't import**: Check file isn't corrupted, try re-exporting
- **Missing data**: Ensure you processed and saved before exporting
- **Wrong format**: Ensure you're using XML files exported from MVC Calculator

---

## Technical Details

### MATLAB<sup>&#174;</sup> File Reading

MVC Calculator uses `scipy.io.loadmat()` to read MATLAB<sup>&#174;</sup> files:
- Supports MATLAB<sup>&#174;</sup> v5, v6, v7, and v7.3 formats
- Automatically handles compressed files
- Extracts first non-metadata variable

### XML Generation

XML files are generated using Python's `xml.etree.ElementTree`:
- UTF-8 encoding
- Human-readable format
- Valid XML structure

---

For more information, see:
- [User Guide](user-guide.md)
- [Troubleshooting](troubleshooting.md)

