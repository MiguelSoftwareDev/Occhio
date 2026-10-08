$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Crie o ambiente virtual e instale requirements.lock.txt antes de iniciar."
}

Push-Location $ProjectRoot
try {
    docker compose up -d rabbitmq
    if ($LASTEXITCODE -ne 0) {
        throw "Não foi possível iniciar o RabbitMQ."
    }

    $BrokerReady = $false
    for ($Attempt = 0; $Attempt -lt 30; $Attempt++) {
        docker exec occhio-rabbitmq rabbitmq-diagnostics -q ping *> $null
        if ($LASTEXITCODE -eq 0) {
            $BrokerReady = $true
            break
        }
        Start-Sleep -Seconds 1
    }
    if (-not $BrokerReady) {
        throw "RabbitMQ não ficou pronto em 30 segundos."
    }

    & $Python -m backend.generate_proto
    if ($LASTEXITCODE -ne 0) {
        throw "Não foi possível gerar os módulos do contrato gRPC."
    }

    & $Python backend/run_all.py
}
finally {
    Pop-Location
}
