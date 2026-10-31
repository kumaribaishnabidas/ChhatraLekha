# ---------------------------------------------------------------------------
# Build launcher for Acadentrix (a product of ChhatraLekha).
#
# This wrapper is a convenience, not a requirement: a bare `gradlew test` now
# works on this machine. It pins the project toolchain (JDK 17) and sanitises
# the environment so the Gradle daemon starts from a clean PATH.
#
# Why the PATH still needs sanitising:
#   This machine's machine-level PATH contains a malformed entry that embeds
#   double quotes ("C:\Program Files\Java\jdk-23\bin;"). The JVM derives
#   java.library.path from PATH, and AGP's AndroidUnitTest#executeTests()
#   copies that value verbatim into the forked JUnit worker's
#   "-Djava.library.path=..." argument. Gradle quotes arguments for the Windows
#   command line but does not escape embedded quotes, so the worker JVM
#   mis-parses argv and dies with:
#       Error: Could not find or load main class Files\Java\jdk-23\bin;;...
#   app/build.gradle.kts now strips the stray quotes from the daemon's
#   java.library.path in a doFirst action, which makes the bare `gradlew` path
#   work as well. Sanitising PATH here additionally keeps the daemon's own
#   java.library.path clean.
#
# Usage:  .\build.cmd [gradle-task ...]
#         .\build.cmd testDebugUnitTest
#         .\build.cmd assembleDebug testDebugUnitTest
# ---------------------------------------------------------------------------
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Tasks = @('assembleDebug')
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$javaHome = 'C:\dev\toolchain\jdk-17'
if (-not (Test-Path (Join-Path $javaHome 'bin\java.exe'))) {
    Write-Host "[build] FATAL: JAVA_HOME not found at $javaHome" -ForegroundColor Red
    exit 1
}

$env:JAVA_HOME = $javaHome

# Strip stray double quotes from PATH (the machine-level PATH is the offender).
if ($env:PATH -match '"') {
    Write-Host "[build] Sanitising PATH (stray quote characters found)..." -ForegroundColor Yellow
    $env:PATH = $env:PATH -replace '"', ''
}

# Put the project toolchain JDK first.
$env:PATH = (Join-Path $javaHome 'bin') + ';' + $env:PATH

Set-Location $projectRoot

$gradlew = Join-Path $projectRoot 'gradlew.bat'

# Restart the daemon so it inherits the sanitised environment.
Write-Host '[build] Stopping any existing Gradle daemon...' -ForegroundColor DarkGray
& $gradlew --stop 2>&1 | Out-Null

Write-Host "[build] Running: gradlew $($Tasks -join ' ')" -ForegroundColor Cyan
& $gradlew @Tasks --console=plain
$code = $LASTEXITCODE

if ($code -eq 0) {
    Write-Host '[build] BUILD SUCCESSFUL' -ForegroundColor Green
} else {
    Write-Host "[build] BUILD FAILED (exit $code)" -ForegroundColor Red
}
exit $code
