#!/usr/bin/env pwsh
<#
.SYNOPSIS
    report.ps1 - Générer un rapport HTML des ressources système

.DESCRIPTION
    NIVEAU 4 : Génération de rapports (version PowerShell)
    
.PARAMETER OutputFile
    Nom du fichier de sortie (défaut: rapport.html)

.EXAMPLE
    pwsh report.ps1
    
.EXAMPLE
    pwsh report.ps1 -OutputFile mon-rapport.html
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$OutputFile = 'rapport.html'
)

function Test-ServiceActive {
    param([string]$ServiceName)
    
    try {
        $result = systemctl is-active $ServiceName 2>&1
        return $result -eq 'active'
    } catch {
        return $false
    }
}

function Format-Bytes {
    param([long]$Bytes)
    
    $units = @('B', 'KB', 'MB', 'GB', 'TB')
    $value = [double]$Bytes
    $unitIndex = 0
    
    while ($value -ge 1024 -and $unitIndex -lt ($units.Length - 1)) {
        $value /= 1024
        $unitIndex++
    }
    
    return "{0:N1} {1}" -f $value, $units[$unitIndex]
}

function Get-CpuUsage {
    try {
        $stat1 = Get-Content '/proc/stat' | Select-Object -First 1
        Start-Sleep -Milliseconds 100
        $stat2 = Get-Content '/proc/stat' | Select-Object -First 1
        
        $values1 = $stat1 -split '\s+' | Select-Object -Skip 1 | ForEach-Object { [long]$_ }
        $values2 = $stat2 -split '\s+' | Select-Object -Skip 1 | ForEach-Object { [long]$_ }
        
        $total1 = ($values1 | Measure-Object -Sum).Sum
        $total2 = ($values2 | Measure-Object -Sum).Sum
        $idle1 = $values1[3]
        $idle2 = $values2[3]
        
        $totalDiff = $total2 - $total1
        $idleDiff = $idle2 - $idle1
        
        if ($totalDiff -eq 0) { return 0 }
        
        $usage = 100 * (1 - ($idleDiff / $totalDiff))
        return [Math]::Round($usage, 1)
    } catch {
        return 0
    }
}

function Get-MemoryInfo {
    try {
        $memInfo = @{}
        Get-Content '/proc/meminfo' | ForEach-Object {
            if ($_ -match '^(\w+):\s+(\d+)') {
                $memInfo[$matches[1]] = [long]$matches[2] * 1024
            }
        }
        
        $total = $memInfo['MemTotal']
        $available = $memInfo['MemAvailable']
        $used = $total - $available
        $percent = [Math]::Round(($used / $total) * 100, 1)
        
        return @{
            Total = $total
            Used = $used
            Available = $available
            Percent = $percent
        }
    } catch {
        return @{ Total = 0; Used = 0; Available = 0; Percent = 0 }
    }
}

function Get-DiskInfo {
    try {
        $dfOutput = df -h / | Select-Object -Last 1
        $parts = $dfOutput -split '\s+' | Where-Object { $_ -ne '' }
        
        return @{
            Total = $parts[1]
            Used = $parts[2]
            Available = $parts[3]
            Percent = [int]($parts[4] -replace '%', '')
        }
    } catch {
        return @{ Total = '0'; Used = '0'; Available = '0'; Percent = 0 }
    }
}

function Get-StatusClass {
    param([double]$Percent)
    
    if ($Percent -lt 50) { return 'good' }
    elseif ($Percent -lt 80) { return 'warning' }
    else { return 'danger' }
}

function New-HtmlReport {
    param(
        [hashtable]$Data,
        [string]$OutputFile
    )
    
    # Générer les lignes de services
    $servicesRows = ""
    foreach ($service in $Data.Services.Keys) {
        $isActive = $Data.Services[$service]
        $statusClass = if ($isActive) { 'service-active' } else { 'service-inactive' }
        $statusText = if ($isActive) { '✅ Actif' } else { '❌ Inactif' }
        
        $servicesRows += @"
        <tr>
            <td>$service</td>
            <td class="$statusClass">$statusText</td>
        </tr>
"@
    }
    
    # Générer les alertes
    $alertsHtml = ""
    $alerts = @()
    
    if ($Data.Cpu -gt 80) { $alerts += "⚠️ CPU élevé: $($Data.Cpu)%" }
    if ($Data.Memory.Percent -gt 85) { $alerts += "⚠️ Mémoire élevée: $($Data.Memory.Percent)%" }
    if ($Data.Disk.Percent -gt 90) { $alerts += "⚠️ Disque presque plein: $($Data.Disk.Percent)%" }
    
    if ($alerts.Count -gt 0) {
        $alertClass = if ($Data.Cpu -gt 90 -or $Data.Memory.Percent -gt 90 -or $Data.Disk.Percent -gt 90) { 'alert danger' } else { 'alert' }
        $alertsHtml = "<div class='$alertClass'><strong>Alertes détectées:</strong><ul>"
        foreach ($alert in $alerts) {
            $alertsHtml += "<li>$alert</li>"
        }
        $alertsHtml += "</ul></div>"
    }
    
    $cpuClass = Get-StatusClass -Percent $Data.Cpu
    $memClass = Get-StatusClass -Percent $Data.Memory.Percent
    $diskClass = Get-StatusClass -Percent $Data.Disk.Percent
    
    # Template HTML (identique à la version Python)
    $html = @"
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport Système - $($Data.Hostname)</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; color: #333; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 15px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.1em; opacity: 0.9; }
        .content { padding: 40px; }
        .section { margin-bottom: 40px; background: #f8f9fa; padding: 30px; border-radius: 10px; border-left: 5px solid #667eea; }
        .section h2 { color: #667eea; margin-bottom: 20px; font-size: 1.8em; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); transition: transform 0.3s; }
        .card:hover { transform: translateY(-5px); }
        .card h3 { color: #667eea; margin-bottom: 15px; font-size: 1.2em; }
        .stat { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }
        .stat:last-child { border-bottom: none; }
        .stat-label { font-weight: 600; color: #666; }
        .stat-value { color: #333; font-weight: 500; }
        .progress { width: 100%; height: 25px; background: #e9ecef; border-radius: 12px; overflow: hidden; margin: 10px 0; }
        .progress-bar { height: 100%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; font-size: 0.9em; transition: width 0.3s; }
        .progress-bar.good { background: linear-gradient(90deg, #28a745 0%, #20c997 100%); }
        .progress-bar.warning { background: linear-gradient(90deg, #ffc107 0%, #fd7e14 100%); }
        .progress-bar.danger { background: linear-gradient(90deg, #dc3545 0%, #c82333 100%); }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; }
        th { background: #667eea; color: white; padding: 15px; text-align: left; font-weight: 600; }
        td { padding: 15px; border-bottom: 1px solid #eee; }
        tr:last-child td { border-bottom: none; }
        tr:hover { background: #f8f9fa; }
        .service-active { color: #28a745; font-weight: 600; }
        .service-inactive { color: #dc3545; font-weight: 600; }
        .footer { background: #f8f9fa; padding: 20px 40px; text-align: center; color: #666; border-top: 1px solid #dee2e6; }
        .alert { background: #fff3cd; border: 1px solid #ffc107; border-radius: 10px; padding: 15px 20px; margin: 20px 0; color: #856404; }
        .alert.danger { background: #f8d7da; border-color: #dc3545; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ Rapport Système</h1>
            <p><strong>Serveur:</strong> $($Data.Hostname)</p>
            <p><strong>Généré le:</strong> $($Data.Timestamp)</p>
        </div>
        
        <div class="content">
            $alertsHtml
            
            <div class="section">
                <h2>💻 Ressources Système</h2>
                <div class="grid">
                    <div class="card">
                        <h3>Processeur</h3>
                        <div class="stat">
                            <span class="stat-label">Utilisation</span>
                            <span class="stat-value">$($Data.Cpu)%</span>
                        </div>
                        <div class="progress">
                            <div class="progress-bar $cpuClass" style="width: $($Data.Cpu)%">
                                $($Data.Cpu)%
                            </div>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Cœurs</span>
                            <span class="stat-value">$($Data.CpuCount)</span>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>Mémoire RAM</h3>
                        <div class="stat">
                            <span class="stat-label">Utilisation</span>
                            <span class="stat-value">$($Data.Memory.Percent)%</span>
                        </div>
                        <div class="progress">
                            <div class="progress-bar $memClass" style="width: $($Data.Memory.Percent)%">
                                $($Data.Memory.Percent)%
                            </div>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Total</span>
                            <span class="stat-value">$(Format-Bytes $Data.Memory.Total)</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Utilisée</span>
                            <span class="stat-value">$(Format-Bytes $Data.Memory.Used)</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Disponible</span>
                            <span class="stat-value">$(Format-Bytes $Data.Memory.Available)</span>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>Disque</h3>
                        <div class="stat">
                            <span class="stat-label">Utilisation</span>
                            <span class="stat-value">$($Data.Disk.Percent)%</span>
                        </div>
                        <div class="progress">
                            <div class="progress-bar $diskClass" style="width: $($Data.Disk.Percent)%">
                                $($Data.Disk.Percent)%
                            </div>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Total</span>
                            <span class="stat-value">$($Data.Disk.Total)</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Utilisé</span>
                            <span class="stat-value">$($Data.Disk.Used)</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Libre</span>
                            <span class="stat-value">$($Data.Disk.Available)</span>
                        </div>
                    </div>
                    
                    <div class="card">
                        <h3>Réseau</h3>
                        <div class="stat">
                            <span class="stat-label">Données envoyées</span>
                            <span class="stat-value">$(Format-Bytes $Data.Network.BytesSent)</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Données reçues</span>
                            <span class="stat-value">$(Format-Bytes $Data.Network.BytesReceived)</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>🌐 État des Services</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Service</th>
                            <th>Statut</th>
                        </tr>
                    </thead>
                    <tbody>
                        $servicesRows
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>📊 Rapport généré automatiquement par Network Monitor</p>
            <p>© 2025 - Niveau 4 : Génération de rapports</p>
        </div>
    </div>
</body>
</html>
"@

    # Écrire le fichier
    try {
        Set-Content -Path $OutputFile -Value $html -Encoding UTF8
        
        Write-Host "`n✅ Rapport généré avec succès !" -ForegroundColor Green
        Write-Host "📁 Fichier: $OutputFile" -ForegroundColor Cyan
        Write-Host "🌐 Ouvrir avec: xdg-open $OutputFile`n" -ForegroundColor Cyan
        
        return $true
    } catch {
        Write-Host "`n❌ Erreur lors de la génération du rapport: $_`n" -ForegroundColor Red
        return $false
    }
}

# Programme principal
Write-Host "`n🔍 Collecte des informations système..." -ForegroundColor Cyan

# Collecter toutes les données
$hostname = hostname
$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$cpu = Get-CpuUsage
$cpuCount = (Get-Content '/proc/cpuinfo' | Select-String 'processor' | Measure-Object).Count
$memory = Get-MemoryInfo
$disk = Get-DiskInfo

# Réseau
try {
    $netStats = Get-Content '/proc/net/dev' | Select-Object -Skip 2
    $totalReceived = 0
    $totalSent = 0
    
    foreach ($line in $netStats) {
        if ($line -match '^\s*\w+:') {
            $parts = $line -split '\s+' | Where-Object { $_ -ne '' }
            $totalReceived += [long]$parts[1]
            $totalSent += [long]$parts[9]
        }
    }
    
    $network = @{
        BytesReceived = $totalReceived
        BytesSent = $totalSent
    }
} catch {
    $network = @{ BytesReceived = 0; BytesSent = 0 }
}

# Services
$services = @('nginx', 'apache2', 'ssh', 'mysql', 'postgresql', 'docker')
$servicesStatus = @{}
foreach ($service in $services) {
    $servicesStatus[$service] = Test-ServiceActive -ServiceName $service
}

# Créer le dictionnaire de données
$data = @{
    Hostname = $hostname
    Timestamp = $timestamp
    Cpu = $cpu
    CpuCount = $cpuCount
    Memory = $memory
    Disk = $disk
    Network = $network
    Services = $servicesStatus
}

Write-Host "📊 Génération du rapport HTML..." -ForegroundColor Cyan
New-HtmlReport -Data $data -OutputFile $OutputFile