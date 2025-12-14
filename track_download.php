<?php
/**
 * Download Tracking Script for MVC Calculator
 * 
 * Receives download notifications and sends email alerts.
 * Upload this file to: /public_html/downloads/MVC_Calculator/releases/
 */

// Set content type to JSON
header('Content-Type: application/json');

// Only allow POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Get JSON data from request body
// Handle both regular JSON POST and sendBeacon blob requests
$input = file_get_contents('php://input');
$data = json_decode($input, true);

// sendBeacon sends data as blob (which PHP receives as raw string), so json_decode should work
// But if it fails, log for debugging
if ($data === null && !empty($input)) {
    // Log the raw input for debugging
    error_log("track_download.php: Failed to decode JSON. Raw input: " . substr($input, 0, 200));
    // Try one more time with trimmed input
    $data = json_decode(trim($input), true);
    
    // If still null, try to extract JSON from the blob
    if ($data === null) {
        // sendBeacon might send the blob differently, try to find JSON in the input
        $json_match = [];
        if (preg_match('/\{.*\}/s', $input, $json_match)) {
            $data = json_decode($json_match[0], true);
            if ($data) {
                error_log("track_download.php: Successfully extracted JSON from blob");
            }
        }
    }
}

// Validate required fields
if (!isset($data['type']) || !isset($data['filename'])) {
    http_response_code(400);
    $error_msg = 'Missing required fields. Received: ' . json_encode(array_keys($data ?? []));
    error_log("track_download.php: " . $error_msg);
    echo json_encode(['error' => $error_msg, 'received_data' => $data]);
    exit;
}

// Log that we received a valid request
error_log("track_download.php: Received download notification for: " . ($data['filename'] ?? 'unknown'));

// Configuration
// Send email to telemetry@moviolabs.com
$recipient_emails = [
    'telemetry@moviolabs.com'
];
$from_email = 'telemetry@moviolabs.com'; // Use telemetry account as sender (must match SMTP auth)
$app_name = 'MVC Calculator';

// SMTP Configuration (required for authenticated SMTP)
// Based on cPanel settings: mail.moviolabs.com:465 (SSL)
$smtp_host = 'mail.moviolabs.com';
$smtp_port = 465; // SSL
$smtp_username = 'telemetry@moviolabs.com';
// NOTE: You need to set the password for telemetry@moviolabs.com account
// Get this from cPanel -> Email Accounts -> telemetry@moviolabs.com -> Manage -> Change Password
// Or use an app password if available
$smtp_password = 'uGc84!qy~erQ?nlz'; // TODO: Set this password

// Get client IP address
function getClientIP() {
    $ipaddress = '';
    if (isset($_SERVER['HTTP_CLIENT_IP']))
        $ipaddress = $_SERVER['HTTP_CLIENT_IP'];
    else if(isset($_SERVER['HTTP_X_FORWARDED_FOR']))
        $ipaddress = $_SERVER['HTTP_X_FORWARDED_FOR'];
    else if(isset($_SERVER['HTTP_X_FORWARDED']))
        $ipaddress = $_SERVER['HTTP_X_FORWARDED'];
    else if(isset($_SERVER['HTTP_FORWARDED_FOR']))
        $ipaddress = $_SERVER['HTTP_FORWARDED_FOR'];
    else if(isset($_SERVER['HTTP_FORWARDED']))
        $ipaddress = $_SERVER['HTTP_FORWARDED'];
    else if(isset($_SERVER['REMOTE_ADDR']))
        $ipaddress = $_SERVER['REMOTE_ADDR'];
    else
        $ipaddress = 'UNKNOWN';
    return $ipaddress;
}

$client_ip = getClientIP();
$filename = htmlspecialchars($data['filename'] ?? 'Unknown');
$timestamp = $data['timestamp'] ?? date('Y-m-d H:i:s');
$user_agent = htmlspecialchars($data['userAgent'] ?? 'Unknown');
$referrer = htmlspecialchars($data['referrer'] ?? 'direct');
$url = htmlspecialchars($data['url'] ?? 'Unknown');

// Get location from IP address using free geolocation service
function getLocationFromIP($ip) {
    // Skip private/local IPs
    if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE) === false) {
        return 'Local/Private IP';
    }
    
    // Use ip-api.com (free, no API key required, 45 requests/minute limit)
    $url = "http://ip-api.com/json/{$ip}?fields=status,country,regionName,city,lat,lon,isp";
    $context = stream_context_create([
        'http' => [
            'timeout' => 3,
            'method' => 'GET'
        ]
    ]);
    
    $response = @file_get_contents($url, false, $context);
    if ($response === false) {
        return 'Location lookup failed';
    }
    
    $data = json_decode($response, true);
    if (isset($data['status']) && $data['status'] === 'success') {
        $location_parts = [];
        if (!empty($data['city'])) $location_parts[] = $data['city'];
        if (!empty($data['regionName'])) $location_parts[] = $data['regionName'];
        if (!empty($data['country'])) $location_parts[] = $data['country'];
        
        $location = !empty($location_parts) ? implode(', ', $location_parts) : 'Unknown';
        if (!empty($data['lat']) && !empty($data['lon'])) {
            $location .= " ({$data['lat']}, {$data['lon']})";
        }
        if (!empty($data['isp'])) {
            $location .= " [ISP: {$data['isp']}]";
        }
        return $location;
    }
    
    return 'Location not available';
}

$location = getLocationFromIP($client_ip);

// Format timestamp in Bogota, Colombia timezone
try {
    $date = new DateTime($timestamp);
    $date->setTimezone(new DateTimeZone('America/Bogota'));
    $formatted_time = $date->format('Y-m-d H:i:s T');
} catch (Exception $e) {
    $formatted_time = $timestamp;
}

// Prepare email content
$subject = $app_name . ' Download: ' . $filename;

$message = "A file download has been detected:\n\n";
$message .= "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
$message .= "FILE INFORMATION\n";
$message .= "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
$message .= "File: " . $filename . "\n";
$message .= "Timestamp: " . $formatted_time . "\n\n";

$message .= "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
$message .= "CLIENT INFORMATION\n";
$message .= "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
$message .= "IP Address: " . $client_ip . "\n";
$message .= "Location: " . $location . "\n\n";

$message .= "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
$message .= "BROWSER INFORMATION\n";
$message .= "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n";
$message .= "User Agent: " . $user_agent . "\n";
$message .= "Referrer: " . $referrer . "\n";
$message .= "Page URL: " . $url . "\n";

// Email headers
$headers = "From: " . $from_email . "\r\n";
$headers .= "Reply-To: " . $from_email . "\r\n";
$headers .= "X-Mailer: PHP/" . phpversion();

// Log to file first (for debugging) - use Bogota timezone
$log_file = __DIR__ . '/downloads.log';
try {
    $log_date = new DateTime('now', new DateTimeZone('America/Bogota'));
    $log_timestamp = $log_date->format('Y-m-d H:i:s T');
} catch (Exception $e) {
    $log_timestamp = date('Y-m-d H:i:s');
}
$log_entry = $log_timestamp . " | " . $filename . " | " . $client_ip . " | " . $location . " | " . $user_agent . "\n";
$log_success = @file_put_contents($log_file, $log_entry, FILE_APPEND | LOCK_EX);

/**
 * Send email via SMTP with authentication
 * Uses PHP sockets to connect to SMTP server (similar to Python's smtplib)
 */
function sendEmailSMTP($to, $subject, $message, $from, $smtp_host, $smtp_port, $smtp_user, $smtp_pass) {
    $error_details = [];
    try {
        error_log("track_download.php: Attempting SMTP connection to {$smtp_host}:{$smtp_port}");
        
        // Create SSL context for secure connection
        $context = stream_context_create([
            'ssl' => [
                'verify_peer' => false,
                'verify_peer_name' => false,
                'allow_self_signed' => true
            ]
        ]);
        
        // Connect to SMTP server
        $socket = @stream_socket_client(
            "ssl://{$smtp_host}:{$smtp_port}",
            $errno,
            $errstr,
            30,
            STREAM_CLIENT_CONNECT,
            $context
        );
        
        if (!$socket) {
            $error_msg = "SMTP connection failed: {$errstr} ({$errno})";
            error_log("track_download.php: {$error_msg}");
            return ['success' => false, 'error' => $error_msg];
        }
        
        error_log("track_download.php: SMTP connection established");
        
        // Read server greeting (may be multi-line)
        $response = fgets($socket, 515);
        error_log("track_download.php: SMTP greeting: " . trim($response));
        
        // Check if greeting starts with 220
        if (substr($response, 0, 3) != '220') {
            $error_msg = "SMTP greeting failed: {$response}";
            error_log("track_download.php: {$error_msg}");
            fclose($socket);
            return ['success' => false, 'error' => $error_msg];
        }
        
        // Read all greeting continuation lines (220- means more lines, 220 means done)
        while (substr($response, 0, 4) == '220-') {
            $response = fgets($socket, 515);
            error_log("track_download.php: Greeting continuation: " . trim($response));
        }
        
        // Verify final greeting response is "220 " (space, not dash)
        if (substr($response, 0, 4) != '220 ') {
            $error_msg = "SMTP greeting incomplete - unexpected response: {$response}";
            error_log("track_download.php: {$error_msg}");
            fclose($socket);
            return ['success' => false, 'error' => $error_msg];
        }
        
        error_log("track_download.php: SMTP greeting completed successfully");
        
        // Send EHLO
        fputs($socket, "EHLO {$smtp_host}\r\n");
        $response = fgets($socket, 515);
        error_log("track_download.php: EHLO response: " . trim($response));
        
        // Read all EHLO response lines (multi-line response)
        // Lines starting with "250-" are continuations, "250 " (space) is the final line
        while (substr($response, 0, 4) == '250-') {
            $response = fgets($socket, 515);
            error_log("track_download.php: EHLO continuation: " . trim($response));
        }
        
        // Verify final EHLO response is "250 " (space, not dash)
        if (substr($response, 0, 4) != '250 ') {
            $error_msg = "EHLO failed - unexpected response: {$response}";
            error_log("track_download.php: {$error_msg}");
            fclose($socket);
            return ['success' => false, 'error' => $error_msg];
        }
        
        error_log("track_download.php: EHLO completed successfully");
        
        // Authenticate
        fputs($socket, "AUTH LOGIN\r\n");
        $response = fgets($socket, 515);
        error_log("track_download.php: AUTH LOGIN response: " . trim($response));
        if (substr($response, 0, 3) != '334') {
            $error_msg = "AUTH LOGIN failed: {$response}";
            error_log("track_download.php: {$error_msg}");
            fclose($socket);
            return ['success' => false, 'error' => $error_msg];
        }
        
        // Send username (base64 encoded)
        fputs($socket, base64_encode($smtp_user) . "\r\n");
        $response = fgets($socket, 515);
        error_log("track_download.php: Username response: " . trim($response));
        if (substr($response, 0, 3) != '334') {
            $error_msg = "Username rejected: {$response}";
            error_log("track_download.php: {$error_msg}");
            fclose($socket);
            return ['success' => false, 'error' => $error_msg];
        }
        
        // Send password (base64 encoded)
        fputs($socket, base64_encode($smtp_pass) . "\r\n");
        $response = fgets($socket, 515);
        error_log("track_download.php: Password response: " . trim($response));
        if (substr($response, 0, 3) != '235') {
            $error_msg = "Authentication failed: {$response}";
            error_log("track_download.php: {$error_msg}");
            fclose($socket);
            return ['success' => false, 'error' => $error_msg];
        }
        
        error_log("track_download.php: SMTP authentication successful");
        
        // Send MAIL FROM
        fputs($socket, "MAIL FROM: <{$from}>\r\n");
        $response = fgets($socket, 515);
        error_log("track_download.php: MAIL FROM response: " . trim($response));
        if (substr($response, 0, 3) != '250') {
            $error_msg = "MAIL FROM failed: {$response}";
            error_log("track_download.php: {$error_msg}");
            fclose($socket);
            return ['success' => false, 'error' => $error_msg];
        }
        
        // Send RCPT TO
        fputs($socket, "RCPT TO: <{$to}>\r\n");
        $response = fgets($socket, 515);
        error_log("track_download.php: RCPT TO response: " . trim($response));
        if (substr($response, 0, 3) != '250') {
            $error_msg = "RCPT TO failed: {$response}";
            error_log("track_download.php: {$error_msg}");
            fclose($socket);
            return ['success' => false, 'error' => $error_msg];
        }
        
        // Send DATA
        fputs($socket, "DATA\r\n");
        $response = fgets($socket, 515);
        error_log("track_download.php: DATA response: " . trim($response));
        if (substr($response, 0, 3) != '354') {
            $error_msg = "DATA command failed: {$response}";
            error_log("track_download.php: {$error_msg}");
            fclose($socket);
            return ['success' => false, 'error' => $error_msg];
        }
        
        // Send email headers and body
        $email_data = "From: {$from}\r\n";
        $email_data .= "To: {$to}\r\n";
        $email_data .= "Subject: {$subject}\r\n";
        $email_data .= "Content-Type: text/plain; charset=UTF-8\r\n";
        $email_data .= "\r\n";
        $email_data .= $message;
        $email_data .= "\r\n.\r\n";
        
        fputs($socket, $email_data);
        $response = fgets($socket, 515);
        error_log("track_download.php: Email send response: " . trim($response));
        if (substr($response, 0, 3) != '250') {
            $error_msg = "Email send failed: {$response}";
            error_log("track_download.php: {$error_msg}");
            fclose($socket);
            return ['success' => false, 'error' => $error_msg];
        }
        
        error_log("track_download.php: Email sent successfully via SMTP");
        
        // Quit
        fputs($socket, "QUIT\r\n");
        fclose($socket);
        
        return ['success' => true];
    } catch (Exception $e) {
        $error_msg = "SMTP exception: " . $e->getMessage();
        error_log("track_download.php: {$error_msg}");
        return ['success' => false, 'error' => $error_msg];
    }
}

// Send email to all recipients using SMTP with authentication
$mail_sent = true;
$failed_recipients = [];
$smtp_error_details = []; // Store error details for each failed recipient

// Check if password is configured
if ($smtp_password === 'YOUR_TELEMETRY_PASSWORD_HERE') {
    $error_msg = "CRITICAL - SMTP password not configured! Please set \$smtp_password in track_download.php";
    error_log("track_download.php: {$error_msg}");
    $mail_sent = false;
    $failed_recipients = $recipient_emails;
    foreach ($recipient_emails as $recipient_email) {
        $smtp_error_details[$recipient_email] = $error_msg;
    }
} else {
    foreach ($recipient_emails as $recipient_email) {
        error_log("track_download.php: Attempting to send email via SMTP to {$recipient_email}");
        
        $result = sendEmailSMTP(
            $recipient_email,
            $subject,
            $message,
            $from_email,
            $smtp_host,
            $smtp_port,
            $smtp_username,
            $smtp_password
        );
        
        // Handle new return format (array with 'success' and optional 'error')
        if (is_array($result)) {
            $sent = $result['success'] ?? false;
            if (!$sent) {
                $error_detail = $result['error'] ?? 'Unknown error';
                error_log("track_download.php: SMTP error details: {$error_detail}");
                $smtp_error_details[$recipient_email] = $error_detail;
            }
        } else {
            // Backward compatibility with boolean return
            $sent = $result;
            if (!$sent) {
                $smtp_error_details[$recipient_email] = 'SMTP send failed (unknown error)';
            }
        }
        
        if (!$sent) {
            $mail_sent = false;
            $failed_recipients[] = $recipient_email;
            $error_detail = $smtp_error_details[$recipient_email] ?? 'SMTP send failed';
            error_log("track_download.php: Failed to send email to {$recipient_email}: {$error_detail}");
        } else {
            error_log("track_download.php: Email sent successfully to {$recipient_email} via SMTP");
        }
    }
}

// Enhanced error logging - use Bogota timezone
$error_log_file = __DIR__ . '/tracking_errors.log';
if (!$mail_sent) {
    try {
        $error_date = new DateTime('now', new DateTimeZone('America/Bogota'));
        $error_timestamp = $error_date->format('Y-m-d H:i:s T');
    } catch (Exception $e) {
        $error_timestamp = date('Y-m-d H:i:s');
    }
    $failed_list = implode(', ', $failed_recipients);
    $error_msg = $error_timestamp . " | Email failed | File: " . $filename . " | Failed recipients: " . $failed_list . " | From: " . $from_email . "\n";
    @file_put_contents($error_log_file, $error_msg, FILE_APPEND | LOCK_EX);
}

// Return detailed response for debugging
$response = [
    'success' => true,
    'filename' => $filename,
    'timestamp' => $formatted_time,
    'ip_address' => $client_ip,
    'location' => $location,
    'email_sent' => $mail_sent,  // This will be false if mail() failed
    'log_written' => $log_success !== false,
    'recipients' => $recipient_emails,
    'failed_recipients' => $failed_recipients,
    'from_email' => $from_email,  // Show sender email in response
    'to_email' => $recipient_emails[0] ?? 'none'  // Show recipient email
];

// Make email status VERY clear in response
if (!$mail_sent) {
    $response['error'] = 'EMAIL FAILED TO SEND';
    $response['warning'] = 'Email may have failed - check server mail configuration';
    $response['suggestion'] = 'Check PHP error logs for detailed SMTP error messages';
    $response['check_logs'] = 'Check PHP error logs and tracking_errors.log for details';
    $response['smtp_host'] = $smtp_host;
    $response['smtp_port'] = $smtp_port;
    $response['smtp_user'] = $smtp_username;
    $response['email_from'] = $from_email;
    $response['email_to'] = $recipient_emails[0] ?? 'none';
    
    // Include detailed error messages for each failed recipient
    if (!empty($smtp_error_details)) {
        $response['smtp_errors'] = $smtp_error_details;
        // Get the first error as the main error message
        $first_error = reset($smtp_error_details);
        $response['error_detail'] = $first_error;
    } else {
        $response['error_detail'] = 'SMTP send failed (no error details available)';
    }
    
    // Also set HTTP status to indicate partial success
    http_response_code(207); // Multi-Status
} else {
    $response['email_status'] = 'Email sent successfully';
    $response['email_recipient'] = $recipient_emails[0];
    $response['email_from'] = $from_email;
}

echo json_encode($response, JSON_PRETTY_PRINT);
?>

