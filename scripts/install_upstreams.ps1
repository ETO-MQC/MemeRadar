$ErrorActionPreference='Stop'; Set-Location (Split-Path $PSScriptRoot -Parent)
New-Item -ItemType Directory -Force upstreams | Out-Null
Set-Location upstreams
$repos=@(
  'https://github.com/alsk1992/CloddsBot.git',
  'https://github.com/0xfnzero/sol-trade-sdk.git',
  'https://github.com/freqtrade/freqtrade.git',
  'https://github.com/hummingbot/hummingbot.git'
)
foreach($r in $repos){ $n=[IO.Path]::GetFileNameWithoutExtension($r); if(!(Test-Path $n)){ git clone --depth 1 $r } else { Write-Host "$n 已存在，跳过" } }
Write-Host '完成。warp-id/solana-trading-bot 因仓库未发现明确 LICENSE，仅列为设计参考，不自动拉取/复用代码。'
