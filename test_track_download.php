<?php
/**
 * Test script for download tracking
 * 
 * Use this to test if the tracking endpoint is working.
 * Access via: https://your-domain.com/downloads/MVC_Calculator/releases/test_track_download.php
 */

// Enable error reporting for debugging
error_reporting(E_ALL);
ini_set('display_errors', 1);

echo "<h1>Download Tracking Test</h1>";
echo "<h2>PHP Configuration</h2>";
echo "<pre>";
echo "PHP Version: " . phpversion() . "\n";
echo "Server: " . $_SERVER['SERVER_SOFTWARE'] . "\n";
echo "Document Root: " . $_SERVER['DOCUMENT_ROOT'] . "\n";
echo "Script Path: " . __FILE__ . "\n";
echo "</pre>";

echo "<h2>Email Test</h2>";

$recipient_email = 'telemetry@moviolabs.com';
$from_email = 'mail@moviolabs.com';
$subject = 'MVC Calculator - Download Tracking Test';
$message = "This is a test email from the download tracking system.\n\n";
$message .= "Time: " . date('Y-m-d H:i:s') . "\n";
$message .= "Server: " . $_SERVER['SERVER_NAME'] . "\n";

$headers = "From: " . $from_email . "\r\n";
$headers .= "Reply-To: " . $from_email . "\r\n";
$headers .= "X-Mailer: PHP/" . phpversion();

echo "<p>Attempting to send test email to: <strong>$recipient_email</strong></p>";

$mail_sent = @mail($recipient_email, $subject, $message, $headers);

if ($mail_sent) {
    echo "<p style='color: green;'><strong>✓ Email sent successfully!</strong></p>";
    echo "<p>Check your inbox (and spam folder) for the test email.</p>";
} else {
    echo "<p style='color: red;'><strong>✗ Email failed to send</strong></p>";
    echo "<p>Possible issues:</p>";
    echo "<ul>";
    echo "<li>PHP mail() function may be disabled on this server</li>";
    echo "<li>Email address may be invalid</li>";
    echo "<li>Server mail configuration may be incorrect</li>";
    echo "<li>Check cPanel email settings</li>";
    echo "</ul>";
}

echo "<h2>File Permissions</h2>";
$log_file = __DIR__ . '/downloads.log';
echo "<p>Log file path: <code>$log_file</code></p>";

if (file_exists($log_file)) {
    echo "<p>Log file exists: <strong style='color: green;'>Yes</strong></p>";
    echo "<p>Log file writable: " . (is_writable($log_file) ? "<strong style='color: green;'>Yes</strong>" : "<strong style='color: red;'>No</strong>") . "</p>";
    echo "<p>Log file size: " . filesize($log_file) . " bytes</p>";
    echo "<h3>Recent log entries (last 10 lines):</h3>";
    $lines = file($log_file);
    $recent = array_slice($lines, -10);
    echo "<pre>" . htmlspecialchars(implode('', $recent)) . "</pre>";
} else {
    echo "<p>Log file exists: <strong style='color: orange;'>No (will be created on first download)</strong></p>";
    $log_dir = dirname($log_file);
    echo "<p>Log directory writable: " . (is_writable($log_dir) ? "<strong style='color: green;'>Yes</strong>" : "<strong style='color: red;'>No</strong>") . "</p>";
}

echo "<h2>Test POST Request</h2>";
echo "<p>Click this button to simulate a download notification:</p>";
echo "<button onclick='testPostRequest()'>Send Test Download Notification</button>";
echo "<div id='post-result'></div>";

echo "<h2>JavaScript Test</h2>";
echo "<p>Open browser console and click this button to test JavaScript tracking:</p>";
echo "<button onclick='testTracking()'>Test JavaScript Tracking</button>";
echo "<div id='js-result'></div>";

echo "<script>
function testPostRequest() {
    const data = {
        type: 'file_download',
        filename: 'TEST_FILE_FROM_FORM.msi',
        url: window.location.href,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        referrer: document.referrer || 'direct',
        ip: ''
    };
    
    const resultDiv = document.getElementById('post-result');
    resultDiv.innerHTML = '<p>Sending test request...</p>';
    
    fetch('track_download.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        resultDiv.innerHTML = '<p style=\"color: green;\"><strong>✓ Request sent successfully!</strong></p><pre>' + JSON.stringify(data, null, 2) + '</pre>';
    })
    .catch(err => {
        resultDiv.innerHTML = '<p style=\"color: red;\"><strong>✗ Error:</strong> ' + err.message + '</p>';
    });
}

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
    
    const resultDiv = document.getElementById('js-result');
    resultDiv.innerHTML = '<p>Sending test request...</p>';
    
    fetch('track_download.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        resultDiv.innerHTML = '<p style=\"color: green;\"><strong>✓ Request sent successfully!</strong></p><pre>' + JSON.stringify(data, null, 2) + '</pre>';
    })
    .catch(err => {
        resultDiv.innerHTML = '<p style=\"color: red;\"><strong>✗ Error:</strong> ' + err.message + '</p>';
    });
}
</script>";

echo "<hr>";
echo "<p><small>Test completed at: " . date('Y-m-d H:i:s') . "</small></p>";
?>

