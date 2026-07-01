# Campanha multi-seed do benchmark IpMU: roda as seeds 43..51 (a 42 já existe) em
# paralelo (6 workers) e depois agrega as 10 seeds nas tabelas do artigo.
#
# Pausável/retomável: Ctrl+C preserva os checkpoints em results/raw/; reexecutar
# continua de onde parou (pula os (config, seed, instância) já feitos).
#
# Uso:   .\run_all_seeds.ps1            # seeds 43..51, 6 workers, todas as instâncias
#        .\run_all_seeds.ps1 -Jobs 8    # ajusta o nº de runs paralelos
#        .\run_all_seeds.ps1 -Seeds 43,44,45

param(
    [int[]] $Seeds = (43..51),
    [int]   $Jobs  = 6
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$py = ".\.venv\Scripts\python.exe"

Write-Host "=== Benchmark multi-seed: seeds $($Seeds -join ',') | jobs $Jobs ===" -ForegroundColor Cyan
& $py python\run_full_benchmark.py --seeds $Seeds --jobs $Jobs

# Agrega TODAS as seeds presentes em results/raw/ (inclui a 42) nas tabelas do artigo.
Write-Host "`n=== Agregando seeds (detalhe + tabelas small/big) ===" -ForegroundColor Cyan
& $py python\aggregate_seeds.py

Write-Host "`nOK. Tabelas em results\report\seeds_summary_small.csv e seeds_summary_big.csv" -ForegroundColor Green
