# -----------------------------------------
# reset_wsl.ps1 — Full WSL Ubuntu reset
# -----------------------------------------

Write-Host "🔻 Shutting down WSL..."
wsl --shutdown

Write-Host "🗑 Unregistering Ubuntu-22.04 (deletes Linux filesystem)..."
wsl --unregister Ubuntu-22.04

Write-Host "⬇️ Reinstalling Ubuntu-22.04..."
wsl --install -d Ubuntu-22.04

Write-Host "✅ WSL reset complete!"
Write-Host "➡️ Now open Ubuntu in Windows Terminal and run: ./rebuild_mvc_wsl.sh"

