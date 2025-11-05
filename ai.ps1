function ai {
    param(
        [string]$Question,
        [string]$File,
        [string]$Edit,
        [string]$Create,
        [switch]$Explain,
        [string]$Model = "deepseek",
        [switch]$Json,
        [string]$Session = "default",
        [switch]$Clear,
        [switch]$ListSessions
    )

    # 🧠 Session management
    $sessionDir = "$HOME\.ai_sessions"
    if (-not (Test-Path $sessionDir)) {
        New-Item -ItemType Directory -Force -Path $sessionDir | Out-Null
    }
    $sessionFile = Join-Path $sessionDir ("session_" + $Session + ".json")

    # 🗂️ List sessions
    if ($ListSessions) {
        Write-Host "`n🗂️ Saved AI Sessions:" -ForegroundColor Cyan
        Get-ChildItem $sessionDir -Filter "session_*.json" | ForEach-Object {
            $sessionName = $_.BaseName.Replace('session_', '')
            Write-Host " - $sessionName" -ForegroundColor White
        }
        Write-Host ""
        return
    }

    # 🧹 Clear session
    if ($Clear) {
        if (Test-Path $sessionFile) {
            Remove-Item $sessionFile
            Write-Host "🧽 Session '$Session' cleared." -ForegroundColor Green
        }
        else {
            Write-Host "ℹ️ Session '$Session' doesn't exist." -ForegroundColor Yellow
        }
        return
    }

    # 🆘 Show help if nothing provided
    if (-not $Question -and -not $File -and -not $Edit -and -not $Create -and -not $Explain) {
        Write-Host "`n🤖 AI CLI – Usage examples:" -ForegroundColor Cyan
        Write-Host "  ai 'your question here'" -ForegroundColor White
        Write-Host "  ai -File code.py -Explain" -ForegroundColor White
        Write-Host "  ai -ListSessions" -ForegroundColor White
        return
    }

    # 🔑 Model routing
    $apiKey = $null
    $apiUrl = $null
    $modelName = ""
    switch ($Model.ToLower()) {
        "deepseek" {
            $apiKey = $env:DEEPSEEK_API_KEY
            $apiUrl = "https://api.deepseek.com/chat/completions"
            $modelName = "deepseek-chat"
        }
        "gpt5" {
            $apiKey = $env:OPENAI_API_KEY
            $apiUrl = "https://api.openai.com/v1/chat/completions"
            $modelName = "gpt-5"
        }
        "claude" {
            $apiKey = $env:ANTHROPIC_API_KEY
            $apiUrl = "https://api.anthropic.com/v1/messages"
            $modelName = "claude-3-sonnet-20240229"
        }
        default {
            Write-Host "❌ Unsupported model: $Model" -ForegroundColor Red
            return
        }
    }

    if (-not $apiKey) {
        Write-Host "❌ Missing API key for $Model" -ForegroundColor Red
        Write-Host "   Set it with: `$env:${Model.ToUpper()}_API_KEY = 'sk-your-key-here'" -ForegroundColor Yellow
        return
    }

    # 💾 Load session history
    $messages = @()
    if (Test-Path $sessionFile) {
        try {
            $messages = Get-Content $sessionFile -Raw | ConvertFrom-Json
        }
        catch { $messages = @() }
    }

    # 🧩 Special modes
    if ($Explain -and $File) {
        $fileContent = Get-Content $File -Raw
        $Question = "Explain this code in detail:`n`n$fileContent"
    }

    if ($Edit -and $File) {
        $content = Get-Content $File -Raw
        Write-Host "📝 Editing: $File" -ForegroundColor Cyan
        $body = @{
            model = $modelName
            messages = @(
                @{ role = "system"; content = "Return ONLY the modified code, no explanations." },
                @{ role = "user"; content = "Edit this code per instruction:`n$Edit`n`n$content" }
            )
        }
        $response = Invoke-RestMethod -Uri $apiUrl -Method Post -Headers @{
            "Authorization" = "Bearer $apiKey"
            "Content-Type" = "application/json"
        } -Body ($body | ConvertTo-Json)
        $newContent = $response.choices[0].message.content
        $newContent.Trim() | Out-File -FilePath $File -Encoding utf8
        Write-Host "✅ File updated: $File" -ForegroundColor Green
        return
    }

    if ($Create) {
        Write-Host "🛠️ Creating: $Create" -ForegroundColor Cyan
        $body = @{
            model = $modelName
            messages = @(
                @{ role = "system"; content = "Generate code only, no explanations." },
                @{ role = "user"; content = "Create: $Question" }
            )
        }
        $response = Invoke-RestMethod -Uri $apiUrl -Method Post -Headers @{
            "Authorization" = "Bearer $apiKey"
            "Content-Type" = "application/json"
        } -Body ($body | ConvertTo-Json)
        $code = $response.choices[0].message.content
        $code.Trim() | Out-File -FilePath $Create -Encoding utf8
        Write-Host "✅ Created: $Create" -ForegroundColor Green
        return
    }

    # 🧱 File context
    $context = ""
    if ($File -and (Test-Path $File)) {
        $fileContent = Get-Content $File -Raw
        $context = "File: " + $File + "`n" + "```" + ($File.Split('.')[-1]) + "`n" + $fileContent + "`n" + "```"
    }

    # ➕ Append to messages
    if ($Question) {
        $messages += @{ role = "user"; content = "$context`n$Question" }
    }

    # 🚀 API call
    $body = @{
        model = $modelName
        messages = $messages
    }
    if ($Json) {
        $body.response_format = @{ type = "json_object" }
    }

    $response = Invoke-RestMethod -Uri $apiUrl -Method Post -Headers @{
        "Authorization" = "Bearer $apiKey"
        "Content-Type" = "application/json"
    } -Body ($body | ConvertTo-Json)

    $answer = $response.choices[0].message.content
    Write-Host "`n🤖 AI:`n$answer" -ForegroundColor Green

    # 💾 Save to session
    $messages += @{ role = "assistant"; content = $answer }
    $messages | ConvertTo-Json -Depth 5 | Out-File -FilePath $sessionFile -Encoding utf8
}