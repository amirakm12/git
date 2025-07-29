# PowerShell Build + Scan + Launch Script
$projectPath = "C:\Users\ramin\OneDrive\Documents\MyProject\Project Human Bot IGED"
cd $projectPath
Write-Host "`n[1/5] 🔍 Scanning project files for issues..." -ForegroundColor Cyan

# Find suspicious lines: TODO, FIXME, errors, missing refs
$scanLog = "$projectPath\audit_log.txt"
Get-ChildItem -Recurse -Include *.py,*.js,*.cs,*.json,*.ts,*.html |
    Select-String -Pattern 'TODO|FIXME|ERROR|Exception|undefined|null|missing' |
    Out-File -Encoding UTF8 $scanLog

if ((Get-Content $scanLog).Length -gt 0) {
    Write-Host "[!] Issues found. Check audit_log.txt" -ForegroundColor Yellow
    notepad $scanLog
} else {
    Write-Host "[✓] No critical issues found." -ForegroundColor Green
}

# Build depending on stack detected
Write-Host "`n[2/5] 🛠 Detecting project type..." -ForegroundColor Cyan
$found = @{}

# Check for Python
if (Test-Path "$projectPath\main.py") {
    $found["Python"] = $true
    Write-Host " - Python project detected"
}

# Check for Node.js
if (Test-Path "$projectPath\package.json") {
    $found["NodeJS"] = $true
    Write-Host " - Node.js (likely Electron) project detected"
}

# Check for C#/.NET
if (Get-ChildItem -Recurse -Include *.sln,*.csproj) {
    $found["DotNet"] = $true
    Write-Host " - C#/.NET project detected"
}

Write-Host "`n[3/5]⚙️ Starting build..." -ForegroundColor Cyan

# Python EXE build (using pyinstaller)
if ($found["Python"]) {
    pip install -r requirements.txt
    pyinstaller --noconfirm --onefile main.py
    $exePath = "$projectPath\dist\main.exe"
}

# Node.js (Electron or CLI)
if ($found["NodeJS"]) {
    npm install
    if (Test-Path "$projectPath\electron.js" -or (Get-Content package.json | Select-String 'electron')) {
        npm run build
        $exePath = "$projectPath\dist\win-unpacked\ProjectHumanBot.exe"
    } else {
        $exePath = "$projectPath\index.js"
    }
}

# .NET Build
if ($found["DotNet"]) {
    dotnet restore
    dotnet build --configuration Release
    $exePath = (Get-ChildItem -Recurse -Include *.exe | Where-Object { $_.FullName -like "*\bin\Release\*" }).FullName
}

Write-Host "`n[4/5] 🚀 Launching app..." -ForegroundColor Cyan

if (Test-Path $exePath) {
    Write-Host "Launching: $exePath"
    Start-Process $exePath
} else {
    Write-Host "[X] Could not find .exe or launchable file." -ForegroundColor Red
}

Write-Host "`n[5/5] ✅ Done. Full environment scanned and build attempted." -ForegroundColor Green
