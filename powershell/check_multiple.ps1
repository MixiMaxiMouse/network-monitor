#!/usr/bin/env pwsh
<#
.SYNOPSIS
    check_multiple.ps1 - Vérifier plusieurs services d'un coup

.DESCRIPTION
    NIVEAU 2 : Gestion de plusieurs services (version PowerShell)
    
.PARAMETER Services
    Liste des services à vérifier

.PARAMETER All
    Vérifier tous les services par défaut

.EXAMPLE
    pwsh check_multiple.ps1 nginx ssh mysql
    
.EXAMPLE
    pwsh check_multiple.ps1 -All
#>

param(
    [Parameter(Mandatory=$false, ValueFromRemainingArguments=$true)]
    [string[]]$Services,
    
    [Parameter(Mandatory=$false)]
    [switch]$All
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

function Test-ServiceEnabled {
    param([string]$ServiceName)
    
    try {
        $result = systemctl is-enabled $ServiceName 2>&1
        return $result -eq 'enabled'
    } catch {
        return $false
    }
}

function Show-ServiceResults {
    param([string[]]$ServiceList)
    
    Write-Host "`n$('='*60)" -ForegroundColor Cyan
    Write-Host "           🔍 VÉRIFICATION DES SERVICES" -ForegroundColor Cyan
    Write-Host "$('='*60)`n" -ForegroundColor Cyan
    
    # En-tête
    Write-Host ("{0,-15} {1,-15} {2,-15}" -f "Service", "Statut", "Démarrage auto")
    Write-Host ('-'*60)
    
    # Statistiques
    $activeCount = 0
    $inactiveCount = 0
    
    # Vérifier chaque service
    foreach ($service in $ServiceList) {
        $isActive = Test-ServiceActive -ServiceName $service
        $isEnabled = Test-ServiceEnabled -ServiceName $service
        
        # Déterminer les symboles
        if ($isActive) {
            $status = "✅ Actif"
            $statusColor = 'Green'
            $activeCount++
        } else {
            $status = "❌ Inactif"
            $statusColor = 'Red'
            $inactiveCount++
        }
        
        $enabled = if ($isEnabled) { "🟢 Oui" } else { "🔴 Non" }
        
        # Afficher la ligne
        Write-Host ("{0,-15} " -f $service) -NoNewline
        Write-Host ("{0,-15} " -f $status) -ForegroundColor $statusColor -NoNewline
        Write-Host ("{0,-15}" -f $enabled)
    }
    
    # Résumé
    Write-Host ('-'*60)
    Write-Host "`n📊 Résumé: $activeCount actif(s) | $inactiveCount inactif(s)`n" -ForegroundColor Yellow
    Write-Host "$('='*60)`n" -ForegroundColor Cyan
}

# Services par défaut
$defaultServices = @(
    'nginx',
    'apache2',
    'ssh',
    'mysql',
    'postgresql',
    'docker',
    'cron'
)

# Programme principal
if ($All) {
    # Option --All : vérifier tous les services par défaut
    Write-Host "🔍 Vérification de tous les services par défaut..." -ForegroundColor Cyan
    Show-ServiceResults -ServiceList $defaultServices
    
} elseif ($Services.Count -gt 0) {
    # Vérifier les services spécifiés
    Write-Host "🔍 Vérification de $($Services.Count) service(s)..." -ForegroundColor Cyan
    Show-ServiceResults -ServiceList $Services
    
} else {
    # Pas d'arguments : afficher l'aide
    Write-Host "`nUsage: pwsh check_multiple.ps1 <service1> <service2> ..." -ForegroundColor Yellow
    Write-Host "       pwsh check_multiple.ps1 -All`n" -ForegroundColor Yellow
    Write-Host "Exemples:" -ForegroundColor Cyan
    Write-Host "  pwsh check_multiple.ps1 nginx ssh mysql"
    Write-Host "  pwsh check_multiple.ps1 -All`n"
    exit 1
}