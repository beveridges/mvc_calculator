# Debugging Download Tracking

If you're not receiving email notifications when downloads occur, follow these steps:

## Step 1: Upload the Test Script

First, upload the test script to your server:

```bash
python deploy_release_ftp.py -u --upload-auxiliary --include-test
```

This will upload both `track_download.php` and `test_track_download.php` to your server.

## Step 2: Run the Test Script

Open your browser and navigate to:
```
https://your-domain.com/downloads/MVC_Calculator/releases/test_track_download.php
```

This test script will:
- ✅ Check PHP configuration
- ✅ Test email sending capability
- ✅ Check file permissions
- ✅ Show recent log entries
- ✅ Provide a form to test POST requests
- ✅ Provide a JavaScript test button

## Step 3: Check the Results

### If Email Test Fails:
1. **Check cPanel Email Settings**
   - Go to cPanel → Email Accounts
   - Verify that `mail@moviolabs.com` exists and is configured
   - Test sending an email from cPanel

2. **Check PHP mail() Function**
   - Some hosting providers disable `mail()` function
   - You may need to use SMTP instead (requires additional configuration)

3. **Check Email Address**
   - Verify `telemetry@moviolabs.com` is correct in `track_download.php`
   - Check spam/junk folder

### If Log File Issues:
1. **Check File Permissions**
   - The `downloads.log` file needs write permissions
   - In cPanel File Manager, set permissions to 644 or 666
   - The directory needs write permissions (755 or 775)

2. **Check Error Log**
   - Look for `tracking_errors.log` in the same directory
   - Check cPanel error logs for PHP errors

## Step 4: Test JavaScript Tracking

1. Open your releases page in a browser
2. Open Developer Tools (F12)
3. Go to Console tab
4. Click a download link
5. Check console for messages:
   - ✅ "Download tracked: {...}" = Success
   - ⚠️ "Download tracking warning: ..." = Email may have failed
   - ❌ "Failed to send download notification: ..." = Request failed

## Step 5: Check Server Logs

### Check downloads.log:
```bash
# Via cPanel File Manager or SSH
cat downloads.log
tail -20 downloads.log  # Last 20 entries
```

### Check tracking_errors.log:
```bash
cat tracking_errors.log
```

## Step 6: Verify PHP Script is Accessible

Test the endpoint directly:
```bash
curl -X POST https://your-domain.com/downloads/MVC_Calculator/releases/track_download.php \
  -H "Content-Type: application/json" \
  -d '{"type":"file_download","filename":"test.msi","timestamp":"2024-01-01T00:00:00Z"}'
```

Expected response:
```json
{
  "success": true,
  "filename": "test.msi",
  "timestamp": "2024-01-01 00:00:00",
  "email_sent": true,
  "log_written": true,
  "recipient": "telemetry@moviolabs.com"
}
```

## Common Issues and Solutions

### Issue: Email not sending
**Solution**: 
- Verify email addresses in `track_download.php` (lines 31-32)
- Check cPanel email configuration
- Consider using SMTP instead of `mail()` function

### Issue: JavaScript not firing
**Solution**:
- Check browser console for errors
- Verify `TEMPLATE_RELEASE.html` has the tracking JavaScript
- Ensure download links have the correct class or attributes

### Issue: 405 Method Not Allowed
**Solution**:
- Verify the script only accepts POST requests
- Check that the request is actually POST, not GET

### Issue: 400 Bad Request
**Solution**:
- Verify JSON payload includes `type` and `filename` fields
- Check browser console for the actual request payload

### Issue: CORS Errors
**Solution**:
- Add CORS headers to `track_download.php` if needed:
```php
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
```

## Manual Testing

You can manually test the tracking by creating a simple HTML file:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Download Tracking Test</title>
</head>
<body>
    <h1>Test Download Tracking</h1>
    <button onclick="testTracking()">Test Download Notification</button>
    <div id="result"></div>
    
    <script>
    function testTracking() {
        const data = {
            type: 'file_download',
            filename: 'TEST_FILE.msi',
            url: window.location.href,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            referrer: document.referrer || 'direct',
            ip: ''
        };
        
        fetch('track_download.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('result').innerHTML = 
                '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
        })
        .catch(err => {
            document.getElementById('result').innerHTML = 
                '<p style="color: red;">Error: ' + err.message + '</p>';
        });
    }
    </script>
</body>
</html>
```

## Next Steps

If email still doesn't work after these checks:
1. Contact your hosting provider about PHP `mail()` function
2. Consider implementing SMTP email (requires PHPMailer or similar)
3. Use the log file as a backup tracking method
4. Set up automated log file monitoring/emailing

