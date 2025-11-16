#!/usr/bin/env pwsh
<#
.SYNOPSIS
    check_service.ps1 - Vérifier si un service est actif

.DESCRIPTION
    NIVEAU 1 : Script ultra-simple pour débuter (version PowerShell)
    
.PARAMETER ServiceName
    Nom du service à vérifier (ex: nginx, ssh, apache2)

.EXAMPLE
    pwsh check_service.ps1 nginx
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ServiceName
)

function Test-ServiceActive {
    <#
    .SYNOPSIS
        Vérifie si un service systemd est actif
    #>
    param([string]$Name)
    
    try {
        # Exécuter systemctl is-active
        $result = systemctl is-active $Name 2>&1
        
        # Vérifier si la sortie est "active"
        return $result -eq 'active'
        
    } catch {
        Write-Host "❌ Erreur: $_" -ForegroundColor Red
        return $false
    }
}

# Programme principal
Write-Host "`n🔍 Vérification du service '$ServiceName'..." -ForegroundColor Cyan

if (Test-ServiceActive -Name $ServiceName) {
    Write-Host "✅ Le service $ServiceName est ACTIF`n" -ForegroundColor Green
    systemctl status "$serviceName"
} else {
    Write-Host "❌ Le service $ServiceName est INACTIF`n" -ForegroundColor Red
}
