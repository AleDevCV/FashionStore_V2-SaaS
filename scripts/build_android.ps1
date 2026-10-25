param([string]$JdkPath='C:\Program Files\Android\Android Studio\jbr',[string]$ApiUrl='https://fashionstore.aledevcv.me')
$ErrorActionPreference='Stop'
$p2Root=Split-Path -Parent $PSScriptRoot
$p2Temp=Join-Path $p2Root 'tmp\java'
New-Item -ItemType Directory -Force -Path $p2Temp | Out-Null
if(-not(Test-Path -LiteralPath (Join-Path $JdkPath 'bin\java.exe'))){throw 'Configure -JdkPath con un JDK 21 instalado.'}
$p2PreviousJava=$env:JAVA_HOME
$p2PreviousOptions=$env:JAVA_TOOL_OPTIONS
try {
 $env:JAVA_HOME=$JdkPath
 $env:JAVA_TOOL_OPTIONS="$p2PreviousOptions -Djava.io.tmpdir=$p2Temp -Djdk.net.unixdomain.tmpdir=$p2Temp"
 Push-Location (Join-Path $p2Root 'Parcial2_mobile')
 try {flutter build apk --release "--dart-define=API_BASE_URL=$ApiUrl";if($LASTEXITCODE -ne 0){throw 'La compilación Android falló.'}} finally {Pop-Location}
} finally {$env:JAVA_HOME=$p2PreviousJava;$env:JAVA_TOOL_OPTIONS=$p2PreviousOptions}
