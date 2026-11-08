$ErrorActionPreference = "Stop"
$docxPath = "c:\Examen si2 FASHIONSTORE\docs\DOCUMENTACION PARCIAL 2\SEGUNDO_EXAMEN_PARCIAL-FASHIONSTORE_CONSOLIDADO.docx"
$pdfPath = "c:\Examen si2 FASHIONSTORE\docs\DOCUMENTACION PARCIAL 2\SEGUNDO_EXAMEN_PARCIAL-FASHIONSTORE_CONSOLIDADO.pdf"

Write-Host "Exportando vista previa en PDF desde Word..."
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = [Microsoft.Office.Interop.Word.WdAlertLevel]::wdAlertsNone

try {
    $doc = $word.Documents.Open($docxPath)
    Write-Host "Exportando PDF..."
    # 17 = wdExportFormatPDF
    $doc.ExportAsFixedFormat($pdfPath, 17)
    Write-Host "PDF exportado exitosamente en: $pdfPath"
    $doc.Close()
} catch {
    Write-Host "Error durante exportacion a PDF: $_"
} finally {
    $word.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}

