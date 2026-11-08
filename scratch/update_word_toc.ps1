$ErrorActionPreference = "Stop"
$docxPath = "c:\Examen si2 FASHIONSTORE\docs\DOCUMENTACION PARCIAL 2\SEGUNDO_EXAMEN_PARCIAL-FASHIONSTORE_CONSOLIDADO.docx"

Write-Host "Iniciando Microsoft Word para actualizar el indice y campos..."
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = [Microsoft.Office.Interop.Word.WdAlertLevel]::wdAlertsNone

try {
    $doc = $word.Documents.Open($docxPath)
    Write-Host "Documento abierto exitosamente. Paginas iniciales: $($doc.ComputeStatistics([Microsoft.Office.Interop.Word.WdStatistic]::wdStatisticPages))"
    
    Write-Host "Actualizando campos..."
    $doc.Fields.Update()
    
    if ($doc.TablesOfContents.Count -ge 1) {
        Write-Host "Actualizando Tabla de Contenido (TOC)..."
        $doc.TablesOfContents.Item(1).Update()
    } else {
        Write-Host "No se encontraron tablas de contenido automaticas explicitas."
    }
    
    $totalPages = $doc.ComputeStatistics([Microsoft.Office.Interop.Word.WdStatistic]::wdStatisticPages)
    Write-Host "Paginas finales tras actualizar: $totalPages"
    
    $doc.Save()
    Write-Host "Documento guardado con indice actualizado."
    $doc.Close()
} catch {
    Write-Host "Error durante actualizacion: $_"
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}

