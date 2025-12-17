# Troubleshooting Guide

## Common Issues and Solutions

### Application Won't Start
	
**Problem**: MVC Calculator doesn't launch or crashes immediately

**Solutions**:

   1. **Check System Requirements** :

      - Windows 10 or later (for Windows builds)
      - Linux with required dependencies (for Linux builds)
      - Sufficient RAM (4GB minimum recommended)

   2. **Check License**:
      - Ensure you have a valid `license.key` file installed
      - See [License Guide](license.md) for installation instructions

   3. **Check Console/Terminal**:
      - During alpha phase, a terminal window shows error messages
      - Look for error messages that indicate the problem

   4. **Reinstall**:
      - Try uninstalling and reinstalling the application
      - For portable version, try extracting to a new location

---

### Files Won't Load

**Problem**: `.mat` files don't load or show error messages

**Solutions**:

   1. **Verify File Format**:
      - Ensure files are valid MATLAB<sup>&#174;</sup> `.mat` format
      - Try opening the file in MATLAB<sup>&#174;</sup> to verify it's not corrupted

   2. **Check File Path**:
      - Avoid very long file paths (Windows limitation)
      - Avoid special characters in file names
      - Ensure you have read permissions for the file

   3. **File Size**:
      - Very large files (>1GB) may take time to load
      - Check the console for progress messages

   4. **File Structure**:
      - Ensure the `.mat` file contains sEMG data
      - Files from the QualisysAB<sup>&#174;</sup>/Noraxon<sup>&#174;</sup> IMM setup should work automatically
      - Other formats may need to match expected structure

---

### No Signal Displayed

**Problem**: File loads but no signal appears in the plot

**Solutions**:

   1. **Check Data Structure**:
      - Ensure your data structure conforms to the Qualiysy/Noraxon<sup>&#174;</sup> spceification

   2. **Check Sampling Frequency**:
      - Default is 1500 Hz
      - If your data uses a different frequency, it may affect display
      - Check `config/defaults.py` for frequency settings

   3. **Zoom/Scale Issues**:
      - Try zooming out (mouse wheel or toolbar)
      - Signal may be very small or very large
      - Check the console for data range information

   4. **Multiple Sensors**:
      - If you loaded multiple files, check different tabs
      - Each sensor appears as a separate tab

---

### Burst Detection Not Working

**Problem**: Energy Detection tool doesn't find bursts or finds too many/few

**Solutions**:

   1. **Signal Quality**:
      - Very noisy signals may need manual selection
      - Pre-process your data if it's extremely noisy
      - Check for electrical interference

   2. **Manual Selection**:
      - If automatic detection fails, use manual selection
      - Click and drag on the plot to select burst regions
      - You can select multiple bursts per sensor

---

### Can't Select Bursts

**Problem**: Clicking and dragging doesn't create selections

**Solutions**:

   1. **Remember the “best-of-3” protocol**
      - The experimental protocol requires exactly three burst selections.  
      - If you attempt to make a fourth selection, it will be ignored.
      - To free up a slot, remove an existing selection using <kbd>Shift</kbd> + Right-Click on the unwanted burst.
      - Once a selection is removed, you can make a new one as normal.

   2. **Ensure Data is Loaded**:
      - File must be fully loaded before selecting
      - Check the console for "File loaded" messages

   3. **Check Plot Area**:
      - Ensure you're clicking on the **active** signal plot area
      - Try zooming in if the signal is very small

   4. **Multiple Sensors**:
      - Make sure you're on the correct sensor tab
      - Each sensor needs separate selections

   5. **Clear Previous Selections**:
      - Use the clear button ![broom icon](user-guide/img/broom_icon.png) if needed
      - Try selecting a different region

---

### Processing Fails

**Problem**: Clicking Process/Calculate doesn't work or shows errors

**Solutions**:

   1. **Multiple Bursts**:
      - For "best of 3" protocol, select 3 bursts
      - The system will find the maximum automatically
      - You muust select **exactly** 3 bursts

   2. **Data Validity**:
      - Ensure selected regions contain valid data
      - Avoid selecting regions with artifacts or noise
      - Check that time ranges are reasonable

---

### Export/Import Issues

**Problem**: XML files won't export or import correctly

**Solutions**:

   1. **File Permissions**:
      - Ensure you have write permissions for export location
      - Try saving to a different folder (e.g., Desktop)

   2. **File Format**:
      - Ensure you're using `.xml` extension
      - Don't rename the file extension

   3. **File Corruption**:
      - If import fails, the XML file may be corrupted
      - Try exporting a new file and importing that
      - Check the console for specific error messages

   4. **Version Compatibility**:
      - XML files from older versions may not be compatible
      - Export a new file if you're upgrading versions

---

### Console/Log Issues

**Problem**: Console shows errors or doesn't display information

**Solutions**:

   1. **Log Level**:
      - Some messages are only shown at certain log levels
      - Errors should always be visible

   2. **Scroll to Bottom**:
      - New messages appear at the bottom
      - Use the scrollbar to see latest messages

   3. **Send Log**:
      - Use the "Send Log" button to email logs for support
      - This helps diagnose issues

   4. **Log File Location**:
      - Logs are saved to: `%APPDATA%\MVC_Calculator\logs\`
      - Check these files for detailed error information

---

### Performance Issues

**Problem**: Application is slow or unresponsive

**Solutions**:

   1. **Large Files**:
      - Very large `.mat` files take time to process
      - Be patient during loading and processing
      - Consider splitting very large files

   2. **Multiple Files**:
      - Processing many files simultaneously may be slow
      - Process files in smaller batches if needed

   3. **System Resources**:
      - Close other applications to free up memory
      - Ensure you have sufficient RAM
      - Check Task Manager for resource usage

   4. **Use MSI Installer**:
      - The portable version may be slower on startup
      - The MSI installer version is optimized for performance

---

### License Issues

**Problem**: License-related errors or application won't start due to license

**Solutions**:

   1. **See [License Guide](license.md)** for detailed troubleshooting
   2. **Common Issues**:
      - License file not found → Check installation location
      - Hardware mismatch → License is for different computer
      - Country mismatch → License doesn't match your location
      - Expired license → Contact support for renewal

---

### Installation Issues

**Problem**: Can't install or application won't run after installation

**Solutions**:

   1. **Windows Installer (MSI)**:
      - Run installer as Administrator
      - Check Windows Event Viewer <kbd>Win</kbd> + <kbd>R</kbd> → eventvwr) for installation errors
      - Ensure you have sufficient disk space

   2. **Portable Version**:
      - Extract to a folder you have write permissions for
      - Don't extract to Program Files (permission issues)
      - Try extracting to Desktop or Documents folder

   3. **Antivirus Software**:
      - Some antivirus software may block the application
      - Add exception for MVC Calculator
      - Contact support if false positive detected

---

## Getting Help

### Before Contacting Support

   1. **Check This Guide**: Many common issues are covered here
   2. **Check Console/Logs**: Error messages often indicate the problem
   3. **Try Basic Steps**:
      - Restart the application
      - Reinstall if needed
      - Check file formats and permissions

### Contacting Support

When contacting support@moviolabs.com, include:

   1. **Error Messages**: Copy exact error messages from console
   2. **Steps to Reproduce**: What were you doing when the error occurred?
   3. **System Information**:
      - Operating system and version
      - Application version (shown in About dialog)
      - File types and sizes you're working with

   4. **Log Files**: Use [Send Log](user-guide.md#sending-log-files-for-support) button or attach log files from:
      - `%APPDATA%\MVC_Calculator\logs\`

### Sending Logs
   If you experience a problem
   
   1. Click the Send Log button in the console area
   2. Enter a message **describing the steps you took that led to the error**
   3. Alternatively, you can manually email the log files located at: `%APPDATA%\MVC_Calculator\logs\`
   4. Be sure to include a clear description of the problem in your email

---

## Advanced Troubleshooting

### Checking Configuration

Default settings are in `config/defaults.py`:

- `BEST_OF`: Number of trials for "best of X" (default: 3)
- `DEFAULT_SEMG_FREQUENCY`: Sampling frequency in Hz (default: 1500)

If you modify these, ensure values are appropriate for your data.

### Debug Mode

During alpha phase:

- A terminal window shows detailed information
- Check this for error messages and warnings
- Log level can be adjusted in the code

### File Format Verification

To verify your `.mat` file structure:

1. Open in MATLAB<sup>&#174;</sup> and check variable names
2. Ensure data is in expected format (time series)
3. Check sampling frequency matches your settings

---

## Known Issues

### Alpha Phase Development Limitations

   - Terminal window appears in background (intentional for debugging)
   - Some features may be experimental
   - Performance may vary with very large files

### Platform-Specific

**Windows**:

- Long file paths may cause issues (Windows limitation)
- Some antivirus software may flag the application

**Linux**:

- Ensure all dependencies are installed
- Check file permissions

---

## Prevention Tips

1. **Regular Backups**: Export XML files regularly to preserve your work
2. **File Management**: Keep `.mat` files organized and named clearly
3. **System Maintenance**: Keep your operating system updated
4. **License Management**: Keep license files backed up
5. **Documentation**: Note any custom settings or workflows

---

For more help, see:
- [User Guide](user-guide.md)
- [License Guide](license.md)
- [File Formats](file-formats.md)

