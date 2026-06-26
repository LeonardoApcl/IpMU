# Compila o IpMU com o g++ do MSYS2/MinGW, com linkagem estática (executável
# portátil, sem depender das DLLs do MinGW no PATH).
#
# Uso:   .\build.ps1
# Saída: ipmu.exe na raiz do projeto.

$ErrorActionPreference = "Stop"

$mingwBin = "C:\msys64\mingw64\bin"
if (Test-Path $mingwBin) {
    $env:Path = "$mingwBin;" + $env:Path
}

$gpp = (Get-Command g++ -ErrorAction SilentlyContinue)
if (-not $gpp) {
    Write-Error "g++ não encontrado. Instale o MinGW (MSYS2) ou ajuste \$mingwBin em build.ps1."
}

Set-Location $PSScriptRoot
$srcs = Get-ChildItem -Recurse -Filter *.cpp -Path src | ForEach-Object { $_.FullName }

Write-Host "Compilando $($srcs.Count) arquivos com $($gpp.Source)..."
& g++ -std=c++17 -O2 -Wall -Wextra -static -static-libgcc -static-libstdc++ -Isrc $srcs -o ipmu.exe

if ($LASTEXITCODE -eq 0) {
    Write-Host "OK: ipmu.exe gerado." -ForegroundColor Green
    Write-Host "Exemplo: .\ipmu.exe instances\AUpdata_ta_cp_20_100_2_50_1.txt --alg bvns --out solucao.json"
} else {
    Write-Error "Falha na compilação (exit $LASTEXITCODE)."
}
