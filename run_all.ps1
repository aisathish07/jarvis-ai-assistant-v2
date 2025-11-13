# Set environment variables for the session
$env:JARVIS_CORE_URL="http://127.0.0.1:8000"
$env:JARVIS_API_PORT="8080"

# Start the core API server
$coreJob = Start-Job -ScriptBlock { python jarvis_api.py }
Write-Output "Started core API server with PID $($coreJob.ChildJobs[0].ProcessId)"

# Wait a moment for the core server to bind to the port
Start-Sleep -Seconds 2

# Start the API bridge
$bridgeJob = Start-Job -ScriptBlock { python jarvis_api_bridge.py }
Write-Output "Started API bridge with PID $($bridgeJob.ChildJobs[0].ProcessId)"

Write-Output "Both servers are running in the background."
Write-Output "Use 'Get-Job' to see the status and 'Stop-Job' to terminate them."
