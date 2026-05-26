# Build script for code-analysis-service
# Downloads Maven 3.9.6 automatically if not present

$ErrorActionPreference = "Stop"
$MavenVersion  = "3.9.6"
$WrapperDir    = "$PSScriptRoot\.mvn\wrapper"
$MavenZip      = "$WrapperDir\apache-maven-$MavenVersion-bin.zip"
$MavenHome     = "$WrapperDir\apache-maven-$MavenVersion"
$MavenExe      = "$MavenHome\bin\mvn.cmd"
$DownloadUrl   = "https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/$MavenVersion/apache-maven-$MavenVersion-bin.zip"

if (-not (Test-Path $MavenExe)) {
    Write-Host "Downloading Apache Maven $MavenVersion..."
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $MavenZip
    Write-Host "Extracting..."
    Expand-Archive -Path $MavenZip -DestinationPath $WrapperDir -Force
    Remove-Item $MavenZip
    Write-Host "Maven $MavenVersion ready at $MavenHome"
}

$args_to_pass = if ($args.Count -gt 0) { $args } else { @("package", "-DskipTests") }
Write-Host "Running: mvn $args_to_pass"
& $MavenExe @args_to_pass
