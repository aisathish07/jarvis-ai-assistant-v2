param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$prompt
)

$apiKey = $env:DEEPSEEK_API_KEY
if (-not $apiKey) {
    Write-Host "❌ Missing DEEPSEEK_API_KEY. Set it with: setx DEEPSEEK_API_KEY your_key"
    exit
}

$url = "https://api.deepseek.com/v1/chat/completions"
$body = @{
    model = "deepseek-chat"
    messages = @(@{ role = "user"; content = $prompt })
} | ConvertTo-Json -Depth 5

$response = Invoke-RestMethod -Uri $url -Headers @{ "Authorization" = "Bearer $apiKey" } -Method Post -Body $body -ContentType "application/json"
Write-Host $response.choices[0].message.content
