# PB2S+Twin Multi-Agent System - Windows PowerShell Launcher
# Launches all 5 agents (Orchestrator + 3 Twins + Suit) in separate PowerShell terminals

Write-Host "PB2S+Twin Multi-Agent System - Starting All Agents..." -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green

# Configuration
$AgentPorts = @{
    "Orchestrator" = 8100
    "Twin-A (Text)" = 8001
    "Twin-B (Image)" = 8002
    "Twin-C (Multimodal)" = 8003
    "Suit (Safety)" = 8200
}

$AgentScripts = @{
    "Orchestrator" = "pb2s_twin\api\agents\orchestrator.py"
    "Twin-A (Text)" = "pb2s_twin\api\agents\twin_a.py"
    "Twin-B (Image)" = "pb2s_twin\api\agents\twin_b.py"
    "Twin-C (Multimodal)" = "pb2s_twin\api\agents\twin_c.py"
    "Suit (Safety)" = "pb2s_twin\api\agents\suit.py"
}

# Store process information
$Global:AgentProcesses = @{}

# Function to start agent in new PowerShell terminal
function Start-Agent {
    param(
        [string]$AgentName,
        [string]$ScriptPath,
        [int]$Port
    )
    
    Write-Host "Starting $AgentName on port $Port..." -ForegroundColor Cyan
    
    # Create command to run in new PowerShell window
    $Command = "python $ScriptPath"
    $WindowTitle = "PB2S+Twin: $AgentName (Port: $Port)"
    
    # Start new PowerShell window with the agent
    $ProcessInfo = Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoExit",
        "-Command",
        "& { `$Host.UI.RawUI.WindowTitle = '$WindowTitle'; cd '$PWD'; Write-Host 'Starting $AgentName...' -ForegroundColor Yellow; $Command }"
    ) -PassThru
    
    # Store process information
    $Global:AgentProcesses[$AgentName] = @{
        Process = $ProcessInfo
        Port = $Port
        ScriptPath = $ScriptPath
    }
    
    Write-Host "✓ $AgentName started (PID: $($ProcessInfo.Id))" -ForegroundColor Green
    Start-Sleep -Seconds 2
}

# Function to check if port is available
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

# Function to wait for agent startup
function Wait-ForAgent {
    param(
        [string]$AgentName,
        [int]$Port,
        [int]$TimeoutSeconds = 30
    )
    
    Write-Host "Waiting for $AgentName to be ready..." -ForegroundColor Yellow
    
    $Timeout = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $Timeout) {
        if (Test-Port -Port $Port) {
            Write-Host "✓ $AgentName is ready!" -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 1
        Write-Host "." -NoNewline -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "⚠ $AgentName startup timeout!" -ForegroundColor Red
    return $false
}

# Main execution
try {
    Write-Host ""
    Write-Host "Checking prerequisites..." -ForegroundColor Yellow
    
    # Check if Python is available
    try {
        $PythonVersion = python --version 2>&1
        Write-Host "✓ Python found: $PythonVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "✗ Python not found! Please install Python and add it to PATH." -ForegroundColor Red
        exit 1
    }
    
    # Check if agent scripts exist
    foreach ($AgentName in $AgentScripts.Keys) {
        $ScriptPath = $AgentScripts[$AgentName]
        if (!(Test-Path $ScriptPath)) {
            Write-Host "✗ Agent script not found: $ScriptPath" -ForegroundColor Red
            exit 1
        }
    }
    Write-Host "✓ All agent scripts found" -ForegroundColor Green
    
    # Check if config file exists
    if (!(Test-Path "config\agents.json")) {
        Write-Host "✗ Configuration file not found: config\agents.json" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Configuration file found" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Starting agents in sequence..." -ForegroundColor Yellow
    Write-Host ""
    
    # Start agents in order: Suit -> Twins -> Orchestrator
    
    # 1. Start Safety Suit first (validation service)
    Start-Agent -AgentName "Suit (Safety)" -ScriptPath $AgentScripts["Suit (Safety)"] -Port $AgentPorts["Suit (Safety)"]
    Wait-ForAgent -AgentName "Suit (Safety)" -Port $AgentPorts["Suit (Safety)"]
    
    # 2. Start Twin agents (parallel services)
    Start-Agent -AgentName "Twin-A (Text)" -ScriptPath $AgentScripts["Twin-A (Text)"] -Port $AgentPorts["Twin-A (Text)"]
    Start-Agent -AgentName "Twin-B (Image)" -ScriptPath $AgentScripts["Twin-B (Image)"] -Port $AgentPorts["Twin-B (Image)"]
    Start-Agent -AgentName "Twin-C (Multimodal)" -ScriptPath $AgentScripts["Twin-C (Multimodal)"] -Port $AgentPorts["Twin-C (Multimodal)"]
    
    # Wait for all twins to be ready
    $TwinAgents = @("Twin-A (Text)", "Twin-B (Image)", "Twin-C (Multimodal)")
    foreach ($TwinName in $TwinAgents) {
        Wait-ForAgent -AgentName $TwinName -Port $AgentPorts[$TwinName]
    }
    
    # 3. Start Orchestrator last (coordination service)
    Start-Agent -AgentName "Orchestrator" -ScriptPath $AgentScripts["Orchestrator"] -Port $AgentPorts["Orchestrator"]
    Wait-ForAgent -AgentName "Orchestrator" -Port $AgentPorts["Orchestrator"]
    
    Write-Host ""
    Write-Host "===========================================" -ForegroundColor Green
    Write-Host "🚀 ALL AGENTS STARTED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "===========================================" -ForegroundColor Green
    Write-Host ""
    
    # Display agent status
    Write-Host "Agent Status:" -ForegroundColor Cyan
    Write-Host "-------------" -ForegroundColor Cyan
    foreach ($AgentName in $AgentPorts.Keys) {
        $Port = $AgentPorts[$AgentName]
        $Status = if (Test-Port -Port $Port) { "✓ RUNNING" } else { "✗ STOPPED" }
        $Color = if (Test-Port -Port $Port) { "Green" } else { "Red" }
        Write-Host "$AgentName : $Status (Port: $Port)" -ForegroundColor $Color
    }
    
    Write-Host ""
    Write-Host "API Endpoints:" -ForegroundColor Cyan
    Write-Host "--------------" -ForegroundColor Cyan
    Write-Host "Orchestrator  : http://localhost:8100/docs" -ForegroundColor White
    Write-Host "Twin-A (Text) : http://localhost:8001/docs" -ForegroundColor White
    Write-Host "Twin-B (Image): http://localhost:8002/docs" -ForegroundColor White
    Write-Host "Twin-C (Multi): http://localhost:8003/docs" -ForegroundColor White
    Write-Host "Suit (Safety) : http://localhost:8200/docs" -ForegroundColor White
    
    Write-Host ""
    Write-Host "Management Commands:" -ForegroundColor Cyan
    Write-Host "-------------------" -ForegroundColor Cyan
    Write-Host "View logs      : Check individual PowerShell terminals" -ForegroundColor White
    Write-Host "Stop all agents: Run stop_all.ps1 or close terminals" -ForegroundColor White
    Write-Host "Health checks  : GET /health on each agent" -ForegroundColor White
    
    Write-Host ""
    Write-Host "Sample PB2S Cycle:" -ForegroundColor Cyan
    Write-Host "------------------" -ForegroundColor Cyan
    Write-Host "1. POST http://localhost:8100/pb2s/plan" -ForegroundColor White
    Write-Host "2. POST http://localhost:8100/pb2s/twin/manufacture" -ForegroundColor White
    Write-Host "3. POST http://localhost:8100/suit/validate" -ForegroundColor White
    Write-Host "4. POST http://localhost:8100/pb2s/finalize" -ForegroundColor White
    
    Write-Host ""
    Write-Host "Press any key to continue monitoring (or close this window)..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    
}
catch {
    Write-Host ""
    Write-Host "✗ Error starting agents: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Check the logs above for details." -ForegroundColor Red
    exit 1
}

# Keep monitoring until user exits
Write-Host ""
Write-Host "Multi-Agent System is running. Monitor individual terminals for logs." -ForegroundColor Green
Write-Host "Use stop_all.ps1 to cleanly shutdown all agents." -ForegroundColor Yellow
Write-Host ""