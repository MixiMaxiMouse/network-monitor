#!/usr/bin/env pwsh
<#
.SYNOPSIS
    alert_system.ps1 - Système d'alertes pour le monitoring

.DESCRIPTION
    NIVEAU 5 : Système d'alertes automatiques (version PowerShell)
    
.PARAMETER ConfigFile
    Fichier de configuration JSON

.PARAMETER Test
    Mode test : une seule vérification

.EXAMPLE
    pwsh alert_system.ps1
    
.EXAMPLE
    pwsh alert_system.ps1 -ConfigFile alerts.json -Test
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$ConfigFile = 'alerts.json',
    
    [Parameter(Mandatory=$false)]
    [switch]$Test
)

class AlertSystem {
    [hashtable]$Config
    [System.Collections.ArrayList]$AlertHistory
    [hashtable]$LastAlertTime
    [string]$LogFile
    
    AlertSystem([string]$configFile) {
        $this.AlertHistory = [System.Collections.ArrayList]::new()
        $this.LastAlertTime = @{}
        $this.Config = $this.LoadConfig($configFile)
        $this.LogFile = $this.Config.log_file
    }
    
    [hashtable] LoadConfig([string]$configFile) {
        $defaultConfig = @{
            thresholds = @{
                cpu = 80.0
                memory = 85.0
                disk = 90.0
            }
            check_interval = 60
            alert_cooldown = 300
            log_file = 'alerts.log'
            console_alerts = $true
        }
        
        if (Test-Path $configFile) {
            try {
                $userConfig = Get-Content $configFile | ConvertFrom-Json -AsHashtable
                foreach ($key in $userConfig.Keys) {
                    $defaultConfig[$key] = $userConfig[$key]
                }
                Write-Host "✅ Configuration chargée depuis $configFile" -ForegroundColor Green
            } catch {
                Write-Host "⚠️  Erreur lecture config: $_, utilisation config par défaut" -ForegroundColor Yellow
            }
        } else {
            Write-Host "ℹ️  Fichier $configFile non trouvé, utilisation config par défaut" -ForegroundColor Cyan
            $this.CreateExampleConfig($configFile)
        }
        
        return $defaultConfig
    }
    
    [void] CreateExampleConfig([string]$configFile) {
        $exampleConfig = @{
            thresholds = @{
                cpu = 80.0
                memory = 85.0
                disk = 90.0
            }
            check_interval = 60
            alert_cooldown = 300
            log_file = 'alerts.log'
            console_alerts = $true
        } | ConvertTo-Json -Depth 10
        
        try {
            Set-Content -Path $configFile -Value $exampleConfig
            Write-Host "📝 Fichier de configuration exemple créé: $configFile" -ForegroundColor Cyan
        } catch {
            Write-Host "⚠️  Impossible de créer le fichier config: $_" -ForegroundColor Yellow
        }
    }
    
    [void] LogAlert([string]$alertType, [string]$message, [string]$level) {
        $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
        $logEntry = "[$timestamp] [$level] [$alertType] $message"
        
        try {
            Add-Content -Path $this.LogFile -Value $logEntry
        } catch {
            Write-Host "⚠️  Erreur écriture log: $_" -ForegroundColor Yellow
        }
        
        $this.AlertHistory.Add(@{
            timestamp = $timestamp
            type = $alertType
            message = $message
            level = $level
        }) | Out-Null
        
        if ($this.AlertHistory.Count -gt 100) {
            $this.AlertHistory.RemoveRange(0, $this.AlertHistory.Count - 100)
        }
    }
    
    [bool] CanSendAlert([string]$alertType) {
        $cooldown = $this.Config.alert_cooldown
        
        if (-not $this.LastAlertTime.ContainsKey($alertType)) {
            return $true
        }
        
        $timeSinceLast = (Get-Date) - $this.LastAlertTime[$alertType]
        return $timeSinceLast.TotalSeconds -ge $cooldown
    }
    
    [bool] CheckCpu() {
        $cpu = $this.GetCpuUsage()
        $threshold = $this.Config.thresholds.cpu
        
        if ($cpu -gt $threshold) {
            if ($this.CanSendAlert('CPU')) {
                $message = "CPU élevé: $($cpu)% (seuil: $($threshold)%)"
                
                if ($this.Config.console_alerts) {
                    Write-Host "`n⚠️  ALERTE: $message" -ForegroundColor Yellow
                }
                
                $this.LogAlert('CPU', $message, 'WARNING')
                $this.LastAlertTime['CPU'] = Get-Date
                return $true
            }
        }
        
        return $false
    }
    
    [bool] CheckMemory() {
        $memory = $this.GetMemoryInfo()
        $threshold = $this.Config.thresholds.memory
        
        if ($memory.Percent -gt $threshold) {
            if ($this.CanSendAlert('MEMORY')) {
                $message = "Mémoire élevée: $($memory.Percent)% (seuil: $($threshold)%)"
                
                if ($this.Config.console_alerts) {
                    Write-Host "`n⚠️  ALERTE: $message" -ForegroundColor Yellow
                }
                
                $this.LogAlert('MEMORY', $message, 'WARNING')
                $this.LastAlertTime['MEMORY'] = Get-Date
                return $true
            }
        }
        
        return $false
    }
    
    [bool] CheckDisk() {
        $disk = $this.GetDiskInfo()
        $threshold = $this.Config.thresholds.disk
        
        if ($disk.Percent -gt $threshold) {
            if ($this.CanSendAlert('DISK')) {
                $message = "Disque plein: $($disk.Percent)% (seuil: $($threshold)%)"
                
                if ($this.Config.console_alerts) {
                    Write-Host "`n⚠️  ALERTE: $message" -ForegroundColor Red
                }
                
                $this.LogAlert('DISK', $message, 'CRITICAL')
                $this.LastAlertTime['DISK'] = Get-Date
                return $true
            }
        }
        
        return $false
    }
    
    [double] GetCpuUsage() {
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
    
    [hashtable] GetMemoryInfo() {
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
    
    [hashtable] GetDiskInfo() {
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
    
    [void] ShowStatus() {
        Write-Host "`n$('='*70)" -ForegroundColor Cyan
        Write-Host "                   🔍 STATUT SYSTÈME" -ForegroundColor Cyan
        Write-Host "$('='*70)`n" -ForegroundColor Cyan
        
        # CPU
        $cpu = $this.GetCpuUsage()
        $cpuThreshold = $this.Config.thresholds.cpu
        $cpuStatus = if ($cpu -lt $cpuThreshold) { '✅' } else { '⚠️' }
        Write-Host "$cpuStatus CPU:     $($cpu.ToString('0.0').PadLeft(5))% (seuil: $($cpuThreshold)%)"
        
        # Mémoire
        $mem = $this.GetMemoryInfo()
        $memThreshold = $this.Config.thresholds.memory
        $memStatus = if ($mem.Percent -lt $memThreshold) { '✅' } else { '⚠️' }
        Write-Host "$memStatus Mémoire: $($mem.Percent.ToString('0.0').PadLeft(5))% (seuil: $($memThreshold)%)"
        
        # Disque
        $disk = $this.GetDiskInfo()
        $diskThreshold = $this.Config.thresholds.disk
        $diskStatus = if ($disk.Percent -lt $diskThreshold) { '✅' } else { '⚠️' }
        Write-Host "$diskStatus Disque:  $($disk.Percent.ToString('0.0').PadLeft(5))% (seuil: $($diskThreshold)%)"
        
        Write-Host "`n$('='*70)" -ForegroundColor Cyan
    }
    
    [array] RunChecks() {
        $alertsTriggered = @()
        
        if ($this.CheckCpu()) {
            $alertsTriggered += 'CPU'
        }
        
        if ($this.CheckMemory()) {
            $alertsTriggered += 'MEMORY'
        }
        
        if ($this.CheckDisk()) {
            $alertsTriggered += 'DISK'
        }
        
        return $alertsTriggered
    }
    
    [void] MonitorLoop() {
        $interval = $this.Config.check_interval
        
        Write-Host "`n🚀 Démarrage du système d'alertes" -ForegroundColor Green
        Write-Host "⏱️  Intervalle de vérification: $interval secondes" -ForegroundColor Cyan
        Write-Host "📝 Log file: $($this.LogFile)" -ForegroundColor Cyan
        Write-Host "`n💡 Appuyez sur Ctrl+C pour arrêter`n" -ForegroundColor Yellow
        
        try {
            while ($true) {
                # Afficher le statut
                $this.ShowStatus()
                
                # Exécuter les vérifications
                $alerts = $this.RunChecks()
                
                if ($alerts.Count -gt 0) {
                    Write-Host "`n🚨 $($alerts.Count) alerte(s) déclenchée(s): $($alerts -join ', ')" -ForegroundColor Red
                } else {
                    Write-Host "`n✅ Aucune alerte - Système OK" -ForegroundColor Green
                }
                
                Write-Host "`n⏳ Prochaine vérification dans ${interval}s..." -ForegroundColor Gray
                Start-Sleep -Seconds $interval
            }
        } catch {
            Write-Host "`n`n✋ Arrêt du système d'alertes..." -ForegroundColor Yellow
            Write-Host "📊 Total d'alertes dans cette session: $($this.AlertHistory.Count)" -ForegroundColor Cyan
            Write-Host "👋 Au revoir!`n" -ForegroundColor Cyan
        }
    }
}

# Programme principal
Write-Host ""

# Créer et lancer le système d'alertes
$alertSystem = [AlertSystem]::new($ConfigFile)

if ($Test) {
    # Mode test
    Write-Host "🧪 Mode test - Vérification unique`n" -ForegroundColor Cyan
    $alertSystem.ShowStatus()
    $alerts = $alertSystem.RunChecks()
    
    if ($alerts.Count -gt 0) {
        Write-Host "`n🚨 $($alerts.Count) alerte(s) détectée(s)" -ForegroundColor Red
    } else {
        Write-Host "`n✅ Aucune alerte - Système OK" -ForegroundColor Green
    }
} else {
    # Mode monitoring continu
    $alertSystem.MonitorLoop()
}