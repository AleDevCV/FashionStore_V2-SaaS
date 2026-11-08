$word = New-Object -ComObject Word.Application
Write-Host "Word Version: $($word.Version)"
$word.Quit()

