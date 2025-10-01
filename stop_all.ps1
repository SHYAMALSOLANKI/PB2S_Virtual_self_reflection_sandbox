# PB2S+Twin Multi-Agent System - Windows PowerShell Shutdown Script
# Gracefully stops all running agents

Write-Host "PB2S+Twin Multi-Agent System - Stopping All Agents..." -ForegroundColor Red
Write-Host "======================================================" -ForegroundColor Red

# Configuration - Agent ports to check and stop
$AgentPorts = @{
    "Orchestrator" = 8100
    "Twin-A (Text)" = 8001
    "Twin-B (Image)" = 8002
    "Twin-C (Multimodal)" = 8003
    "Suit (Safety)" = 8200
}

# Function to check if port is in use
function Test-Port {
    param([int]$Port)
    
    try {
        $Connection = New-Object System.Net.Sockets.TcpClient
        $Connection.Connect("localhost", $Port)
        $Connection.Close()
        return $true
    }
    catch {
        return $false
    }
}

# Function to find and stop processes using specific ports
function Stop-ProcessOnPort {
    param(
        [int]$Port,
        [string]$AgentName
    )
    
    Write-Host "Checking $AgentName on port $Port..." -ForegroundColor Yellow
    
    try {
        # Use netstat to find process using the port
        $NetstatOutput = netstat -ano | Where-Object { $_ -match ":$Port\s" }
        
        if ($NetstatOutput) {
            foreach ($Line in $NetstatOutput) {
                # Extract PID from netstat output
                $Parts = $Line -split '\s+'
                $PID = $Parts[-1]
                
                if ($PID -and $PID -match '^\d+$') {
                    try {
                        $Process = Get-Process -Id $PID -ErrorAction Stop
                        Write-Host "Found process: $($Process.ProcessName) (PID: $PID)" -ForegroundColor Cyan
                        
                        # Try graceful shutdown first
                        Write-Host "Attempting graceful shutdown..." -ForegroundColor Yellow
                        $Process.CloseMainWindow()
                        
                        # Wait a bit for graceful shutdown
                        Start-Sleep -Seconds 3
                        
                        # Check if still running
                        if (!$Process.HasExited) {
                            Write-Host "Forcing termination..." -ForegroundColor Orange
                            Stop-Process -Id $PID -Force
                        }
                        
                        Write-Host "✓ $AgentName stopped successfully" -ForegroundColor Green
                        return $true
                    }
                    catch {
                        Write-Host "⚠ Could not stop process $PID`: $($_.Exception.Message)" -ForegroundColor Orange
                    }
                }
            }
        }
        else {
            Write-Host "✓ No process found on port $Port" -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "✗ Error checking port $Port`: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    return $false
}

# Function to stop Python processes by name
function Stop-PythonAgents {
    Write-Host "Looking for Python agent processes..." -ForegroundColor Yellow
    
    try {
        # Find Python processes that might be our agents
        $PythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue
        
        if ($PythonProcesses) {
            foreach ($Process in $PythonProcesses) {
                try {
                    # Check if this is likely one of our agents
                    $CommandLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($Process.Id)").CommandLine
                    
                    if ($CommandLine -and ($CommandLine -match "orchestrator\.py|twin_[abc]\.py|suit\.py")) {
                        Write-Host "Found agent process: $CommandLine" -ForegroundColor Cyan
                        Write-Host "Stopping Python agent (PID: $($Process.Id))..." -ForegroundColor Yellow
                        
                        # Try graceful shutdown
                        $Process.CloseMainWindow()
                        Start-Sleep -Seconds 2
                        
                        if (!$Process.HasExited) {
                            Stop-Process -Id $Process.Id -Force
                        }
                        
                        Write-Host "✓ Python agent stopped" -ForegroundColor Green
                    }
                }
                catch {
                    Write-Host "⚠ Could not check/stop Python process $($Process.Id): $($_.Exception.Message)" -ForegroundColor Orange
                }
            }
        }
        else {
            Write-Host "✓ No Python processes found" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "⚠ Error searching for Python processes: $($_.Exception.Message)" -ForegroundColor Orange
    }
}

# Main execution
try {
    Write-Host ""
    Write-Host "Checking agent status..." -ForegroundColor Yellow
    
    # Check which agents are currently running
    $RunningAgents = @()
    foreach ($AgentName in $AgentPorts.Keys) {
        $Port = $AgentPorts[$AgentName]
        if (Test-Port -Port $Port) {
            $RunningAgents += $AgentName
            Write-Host "🔴 $AgentName is running on port $Port" -ForegroundColor Red
        }
        else {
            Write-Host "⚫ $AgentName is not running on port $Port" -ForegroundColor Gray
        }
    }
    
    if ($RunningAgents.Count -eq 0) {
        Write-Host ""
        Write-Host "✓ No agents appear to be running." -ForegroundColor Green
        Write-Host "All ports are clear." -ForegroundColor Green
    }
    else {
        Write-Host ""
        Write-Host "Stopping $($RunningAgents.Count) running agent(s)..." -ForegroundColor Yellow
        Write-Host ""
        
        # Stop agents in reverse order: Orchestrator -> Twins -> Suit
        $StopOrder = @("Orchestrator", "Twin-C (Multimodal)", "Twin-B (Image)", "Twin-A (Text)", "Suit (Safety)")
        
        foreach ($AgentName in $StopOrder) {
            if ($RunningAgents -contains $AgentName) {
                $Port = $AgentPorts[$AgentName]
                Stop-ProcessOnPort -Port $Port -AgentName $AgentName
                Start-Sleep -Seconds 1
            }
        }
        
        # Additional cleanup - stop any remaining Python agent processes
        Write-Host ""
        Write-Host "Performing additional cleanup..." -ForegroundColor Yellow
        Stop-PythonAgents
        
        # Final verification
        Write-Host ""
        Write-Host "Verifying shutdown..." -ForegroundColor Yellow
        $StillRunning = @()
        foreach ($AgentName in $AgentPorts.Keys) {
            $Port = $AgentPorts[$AgentName]
            if (Test-Port -Port $Port) {
                $StillRunning += $AgentName
            }
        }
        
        if ($StillRunning.Count -eq 0) {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "✅ ALL AGENTS STOPPED SUCCESSFULLY!" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
        }
        else {
            Write-Host ""
            Write-Host "⚠ Some agents may still be running:" -ForegroundColor Orange
            foreach ($AgentName in $StillRunning) {
                Write-Host "   - $AgentName (Port: $($AgentPorts[$AgentName]))" -ForegroundColor Orange
            }
            Write-Host ""
            Write-Host "You may need to manually close their PowerShell windows." -ForegroundColor Yellow
        }
    }
    
    # Clean up any leftover files
    Write-Host ""
    Write-Host "Cleaning up temporary files..." -ForegroundColor Yellow
    try {
        # Clean up PID files if they exist
        if (Test-Path ".pb2s/*.pid") {
            Remove-Item ".pb2s/*.pid" -Force
            Write-Host "✓ Cleaned up PID files" -ForegroundColor Green
        }
        
        # Show ledger files (don't delete - they contain audit trail)
        if (Test-Path ".pb2s/*.jsonl") {
            $LedgerFiles = Get-ChildItem ".pb2s/*.jsonl"
            Write-Host "ℹ Ledger files preserved: $($LedgerFiles.Count) files" -ForegroundColor Cyan
        }
    }
    catch {
        Write-Host "⚠ Could not clean up temporary files: $($_.Exception.Message)" -ForegroundColor Orange
    }
    
    Write-Host ""
    Write-Host "Shutdown complete." -ForegroundColor Green
    Write-Host ""
    Write-Host "To restart the system, run: .\run_all.ps1" -ForegroundColor Cyan
    Write-Host ""
}
catch {
    Write-Host ""
    Write-Host "✗ Error during shutdown: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Some processes may need to be stopped manually." -ForegroundColor Red
    exit 1
}

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")