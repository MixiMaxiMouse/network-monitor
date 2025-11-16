#!/usr/bin/env pwsh
<#
.SYNOPSIS
    monitor.ps1 - Surveiller les ressources système en temps réel

.DESCRIPTION
    NIVEAU 3 : Monitoring basique (CPU, RAM, Disque)
    
.PARAMETER Interval
    Intervalle de rafraîchissement en secondes (défaut: 3)

.EXAMPLE
    pwsh monitor.ps1
    
.EXAMPLE
    pwsh monitor.ps1 -Interval 5
#>

param(
    [Parameter(Mandatory=$false)]
    [int]$Interval = 3
)

function Get-CpuUsage {
    <#
    .SYNOPSIS
        Calcule l'utilisation CPU en pourcentage
    #>
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
    <#
    .SYNOPSIS
        Récupère les informations mémoire
    #>
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
        return @{
            Total = 0
            Used = 0
            Available = 0
            Percent = 0
        }
    }
}

function Get-DiskInfo {
    <#
    .SYNOPSIS
        Récupère les informations disque
    #>
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
        return @{
            Total = '0'
            Used = '0'
            Available = '0'
            Percent = 0
        }
    }
}

function Get-NetworkInfo {
    <#
    .SYNOPSIS
        Récupère les informations réseau
    #>
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
        
        return @{
            BytesReceived = $totalReceived
            BytesSent = $totalSent
        }
    } catch {
        return @{
            BytesReceived = 0
            BytesSent = 0
        }
    }
}

function Format-Bytes {
    <#
    .SYNOPSIS
        Formate les octets en format lisible
    #>
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

function Draw-ProgressBar {
    <#
    .SYNOPSIS
        Dessine une barre de progression colorée
    #>
    param(
        [double]$Percentage,
        [int]$Width = 40
    )
    
    $filled = [Math]::Floor(($Percentage / 100) * $Width)
    $empty = $Width - $filled
    
    # Choisir la couleur
    if ($Percentage -lt 50) {
        $color = 'Green'
    } elseif ($Percentage -lt 80) {
        $color = 'Yellow'
    } else {
        $color = 'Red'
    }
    
    $bar = ('█' * $filled) + ('░' * $empty)
    
    Write-Host "[" -NoNewline
    Write-Host $bar -ForegroundColor $color -NoNewline
    Write-Host "] $($Percentage.ToString('0.0'))%"
}

function Show-Dashboard {
    <#
    .SYNOPSIS
        Affiche le tableau de bord complet
    #>
    param(
        $Cpu,
        $Memory,
        $Disk,
        $Network
    )
    
    Clear-Host
    
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:MM:ss'
    
    # En-tête
    Write-Host "`n$('='*70)" -ForegroundColor Cyan
    Write-Host "                🖥️  MONITORING SYSTÈME" -ForegroundColor Cyan
    Write-Host "                Mise à jour: $timestamp" -ForegroundColor Cyan
    Write-Host "$('='*70)`n" -ForegroundColor Cyan
    
    # Section CPU
    Write-Host "💻 CPU" -ForegroundColor Yellow
    Write-Host ('-'*70)
    Write-Host "  Utilisation:  " -NoNewline
    Draw-ProgressBar -Percentage $Cpu
    
    # Section Mémoire
    Write-Host "`n💾 MÉMOIRE" -ForegroundColor Yellow
    Write-Host ('-'*70)
    Write-Host "  RAM:          " -NoNewline
    Draw-ProgressBar -Percentage $Memory.Percent
    Write-Host "  Utilisée:     $(Format-Bytes $Memory.Used) / $(Format-Bytes $Memory.Total)"
    Write-Host "  Disponible:   $(Format-Bytes $Memory.Available)"
    
    # Section Disque
    Write-Host "`n💿 DISQUE" -ForegroundColor Yellow
    Write-Host ('-'*70)
    Write-Host "  Utilisation:  " -NoNewline
    Draw-ProgressBar -Percentage $Disk.Percent
    Write-Host "  Utilisé:      $($Disk.Used) / $($Disk.Total)"
    Write-Host "  Libre:        $($Disk.Available)"
    
    # Section Réseau
    Write-Host "`n🌐 RÉSEAU" -ForegroundColor Yellow
    Write-Host ('-'*70)
    Write-Host "  Envoyé:       $(Format-Bytes $Network.BytesSent)"
    Write-Host "  Reçu:         $(Format-Bytes $Network.BytesReceived)"
    
    # Alertes
    $alerts = @()
    if ($Cpu -gt 80) { $alerts += "⚠️  CPU élevé" }
    if ($Memory.Percent -gt 85) { $alerts += "⚠️  Mémoire élevée" }
    if ($Disk.Percent -gt 90) { $alerts += "⚠️  Disque presque plein" }
    
    if ($alerts.Count -gt 0) {
        Write-Host "`n🚨 ALERTES" -ForegroundColor Red
        Write-Host ('-'*70)
        foreach ($alert in $alerts) {
            Write-Host "  $alert" -ForegroundColor Yellow
        }
    }
    
    # Pied de page
    Write-Host "`n$('='*70)" -ForegroundColor Cyan
    Write-Host "  Ctrl+C pour quitter" -ForegroundColor Gray
    Write-Host "$('='*70)" -ForegroundColor Cyan
}

# Programme principal
Write-Host "`n🚀 Démarrage du monitoring (intervalle: ${Interval}s)" -ForegroundColor Green
Write-Host "💡 Appuyez sur Ctrl+C pour arrêter`n" -ForegroundColor Cyan

Start-Sleep -Seconds 2

try {
    while ($true) {
        # Collecter les données
        $cpu = Get-CpuUsage
        $memory = Get-MemoryInfo
        $disk = Get-DiskInfo
        $network = Get-NetworkInfo
        
        # Afficher le tableau de bord
        Show-Dashboard -Cpu $cpu -Memory $memory -Disk $disk -Network $network
        
        # Attendre
        Start-Sleep -Seconds $Interval
    }
} catch {
    Write-Host "`n`n✋ Arrêt du monitoring..." -ForegroundColor Yellow
    Write-Host "👋 Au revoir!`n" -ForegroundColor Cyan
}