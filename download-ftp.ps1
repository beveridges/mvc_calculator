param(
    [Parameter(Mandatory=$true)]
    [string]$FtpServer,

    [Parameter(Mandatory=$true)]
    [string]$RemoteFile,

    [Parameter(Mandatory=$true)]
    [string]$LocalFile,

    [Parameter(Mandatory=$true)]
    [string]$Username
)

# Prompt for password securely
$Password = Read-Host "Enter FTP Password" -AsSecureString
$Credential = New-Object System.Management.Automation.PSCredential ($Username, $Password)

# Build full FTP URI
$Uri = "ftp://$FtpServer/$RemoteFile"

try {
    Write-Host "Downloading $Uri ..."
    
    Invoke-WebRequest `
        -Uri $Uri `
        -OutFile $LocalFile `
        -Credential $Credential `
        -ErrorAction Stop

    Write-Host "Download completed successfully."
}
catch {
    Write-Error "Download failed: $($_.Exception.Message)"
}