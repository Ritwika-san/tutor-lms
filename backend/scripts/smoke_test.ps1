$ErrorActionPreference = "Stop"

$backendDir = (Resolve-Path (Join-Path $PSScriptRoot ".." )).Path
$pythonPath = Join-Path $backendDir ".venv\Scripts\python.exe"
$baseUrl = "http://127.0.0.1:8015"
$runDir = Join-Path ([System.IO.Path]::GetTempPath()) ("tutor-lms-smoke-" + [guid]::NewGuid().ToString("N"))
$databasePath = Join-Path $runDir "smoke-test.db"
$chromaPath = Join-Path $runDir "chroma"
$stdoutPath = Join-Path $runDir "server.stdout.log"
$stderrPath = Join-Path $runDir "server.stderr.log"
$serverProcess = $null
$currentStep = "startup"

function Write-StepResult([string] $label, $result) {
    Write-Host "`n=== $label ===" -ForegroundColor Cyan
    if ($null -eq $result) {
        Write-Host "OK"
    } else {
        $result | ConvertTo-Json -Depth 20 | Write-Host
    }
}

function Invoke-Api {
    param(
        [Parameter(Mandatory = $true)][string] $Step,
        [Parameter(Mandatory = $true)][string] $Method,
        [Parameter(Mandatory = $true)][string] $Path,
        [hashtable] $Headers,
        $Body
    )

    $script:currentStep = $Step
    $client = [System.Net.Http.HttpClient]::new()
    $request = [System.Net.Http.HttpRequestMessage]::new([System.Net.Http.HttpMethod]::$Method, "$baseUrl$Path")
    try {
        if ($Headers) {
            foreach ($header in $Headers.GetEnumerator()) {
                [void]$request.Headers.TryAddWithoutValidation($header.Key, [string]$header.Value)
            }
        }
        if ($null -ne $Body) {
            $json = $Body | ConvertTo-Json -Depth 20 -Compress
            $request.Content = [System.Net.Http.StringContent]::new($json, [System.Text.Encoding]::UTF8, "application/json")
        }
        $response = $client.SendAsync($request).GetAwaiter().GetResult()
        $responseBody = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        if (-not $response.IsSuccessStatusCode) {
            throw "$Step failed with HTTP $([int]$response.StatusCode): $responseBody"
        }
        if ([string]::IsNullOrWhiteSpace($responseBody)) { return $null }
        return $responseBody | ConvertFrom-Json
    } finally {
        $request.Dispose()
        $client.Dispose()
    }
}

function Invoke-MaterialUpload([string] $Step, [int] $CourseId, [string] $Token, [byte[]] $PdfBytes) {
    $script:currentStep = $Step
    $client = [System.Net.Http.HttpClient]::new()
    $request = [System.Net.Http.HttpRequestMessage]::new([System.Net.Http.HttpMethod]::Post, "$baseUrl/courses/$CourseId/materials")
    $multipart = [System.Net.Http.MultipartFormDataContent]::new()
    try {
        $request.Headers.Authorization = [System.Net.Http.Headers.AuthenticationHeaderValue]::new("Bearer", $Token)
        $pdfContent = [System.Net.Http.ByteArrayContent]::new($PdfBytes)
        $pdfContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("application/pdf")
        $multipart.Add($pdfContent, "file", "newtons-laws.pdf")
        $request.Content = $multipart
        $response = $client.SendAsync($request).GetAwaiter().GetResult()
        $responseBody = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        if (-not $response.IsSuccessStatusCode) {
            throw "$Step failed with HTTP $([int]$response.StatusCode): $responseBody"
        }
        return $responseBody | ConvertFrom-Json
    } finally {
        $request.Dispose()
        $client.Dispose()
    }
}

function New-SamplePdf {
    $pdfScript = @'
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from io import BytesIO
import base64

buffer = BytesIO()
document = canvas.Canvas(buffer, pagesize=LETTER)
document.setTitle("Newton's Laws")
text = document.beginText(54, 740)
text.setFont("Helvetica", 11)
text.setLeading(16)
text.textLine("Newton's laws of motion describe how forces affect the movement of objects.")
text.textLine("The first law says an object remains at rest or moves at constant velocity")
text.textLine("unless acted on by a net external force. The second law is F = ma: net force")
text.textLine("equals mass multiplied by acceleration. The third law says every action force")
text.textLine("has an equal and opposite reaction force.")
document.drawText(text)
document.save()
print(base64.b64encode(buffer.getvalue()).decode("ascii"))
'@
    $encoded = & $pythonPath -c $pdfScript
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($encoded)) {
        throw "Sample PDF generation failed."
    }
    return [Convert]::FromBase64String(($encoded -join "").Trim())
}

try {
    if (-not (Test-Path $pythonPath)) {
        throw "Python venv executable not found: $pythonPath"
    }
    New-Item -ItemType Directory -Path $runDir -Force | Out-Null

    $oldDatabaseUrl = $env:DATABASE_URL
    $oldJwtSecretKey = $env:JWT_SECRET_KEY
    $oldEnvironment = $env:ENVIRONMENT
    $oldChromaPath = $env:CHROMA_PATH
    $env:DATABASE_URL = "sqlite:///$($databasePath.Replace('\', '/'))"
    $env:JWT_SECRET_KEY = "smoke-test-secret-key"
    $env:ENVIRONMENT = "testing"
    $env:CHROMA_PATH = $chromaPath

    $serverProcess = Start-Process -FilePath $pythonPath -ArgumentList @(
        "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8015"
    ) -WorkingDirectory $backendDir -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath -PassThru

    $ready = $false
    for ($attempt = 1; $attempt -le 20; $attempt++) {
        try {
            $health = Invoke-WebRequest -Uri "$baseUrl/health" -Method Get -TimeoutSec 1 -UseBasicParsing
            if ($health.StatusCode -eq 200) {
                $ready = $true
                break
            }
        } catch {
            if ($serverProcess.HasExited) { break }
        }
        if ($attempt -lt 20) { Start-Sleep -Milliseconds 500 }
    }
    if (-not $ready) {
        throw "Server did not become ready at $baseUrl/health after 20 polling attempts."
    }
    Write-StepResult "Server ready" @{ url = "$baseUrl/health"; attempts = $attempt }

    $password = "SmokeTest!2026"
    $tutorRegistration = Invoke-Api "Register tutor" "Post" "/auth/register" -Body @{ name = "Smoke Tutor"; email = "tutor1@example.com"; password = $password; role = "tutor" }
    Write-StepResult "Register tutor" $tutorRegistration
    $studentRegistration = Invoke-Api "Register student" "Post" "/auth/register" -Body @{ name = "Smoke Student"; email = "student1@example.com"; password = $password; role = "student" }
    Write-StepResult "Register student" $studentRegistration

    $tutorLogin = Invoke-Api "Login tutor" "Post" "/auth/login" -Body @{ email = "tutor1@example.com"; password = $password }
    $studentLogin = Invoke-Api "Login student" "Post" "/auth/login" -Body @{ email = "student1@example.com"; password = $password }
    $tutorToken = $tutorLogin.access_token
    $studentToken = $studentLogin.access_token
    Write-StepResult "Login tutor and student" @{ tutor_token_stored = [bool]$tutorToken; student_token_stored = [bool]$studentToken }

    $tutorHeaders = @{ Authorization = "Bearer $tutorToken" }
    $studentHeaders = @{ Authorization = "Bearer $studentToken" }
    $course = Invoke-Api "Create course" "Post" "/courses" -Headers $tutorHeaders -Body @{ title = "Physics 101"; description = "An introduction to mechanics and Newton's laws." }
    Write-StepResult "Create course" $course
    $pdfBytes = New-SamplePdf
    $material = Invoke-MaterialUpload "Upload course material" $course.id $tutorToken $pdfBytes
    Write-StepResult "Upload course material" @{ material = $material; pdf_bytes = $pdfBytes.Length }
    $enrollment = Invoke-Api "Enroll student" "Post" "/courses/$($course.id)/enroll" -Headers $studentHeaders
    Write-StepResult "Enroll student" $enrollment

    $firstDoubt = Invoke-Api "Post first doubt" "Post" "/courses/$($course.id)/doubts" -Headers $studentHeaders -Body @{ text_content = "What is Newton's second law?" }
    Write-StepResult "First doubt (expected source: generated)" $firstDoubt
    $secondDoubt = Invoke-Api "Post second doubt" "Post" "/courses/$($course.id)/doubts" -Headers $studentHeaders -Body @{ text_content = "Can you explain Newton's second law of motion?" }
    Write-StepResult "Second doubt (expected source: matched)" $secondDoubt
    $unrelatedDoubt = Invoke-Api "Post unrelated doubt" "Post" "/courses/$($course.id)/doubts" -Headers $studentHeaders -Body @{ text_content = "What is photosynthesis?" }
    Write-StepResult "Unrelated doubt (expected source: generated)" $unrelatedDoubt
    Write-Host "`nSMOKE TEST PASSED" -ForegroundColor Green
} catch {
    Write-Host "`nSMOKE TEST FAILED at step '$currentStep'" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
} finally {
    if ($serverProcess -and -not $serverProcess.HasExited) {
        $serverProcess.CloseMainWindow() | Out-Null
        $serverProcess.WaitForExit(5000)
        if (-not $serverProcess.HasExited) { $serverProcess.Kill() }
    }
    Write-Host "`n=== Backend server log output ===" -ForegroundColor Yellow
    if (Test-Path $stdoutPath) { Get-Content $stdoutPath }
    if (Test-Path $stderrPath) { Get-Content $stderrPath }
    if ($oldDatabaseUrl) { $env:DATABASE_URL = $oldDatabaseUrl } else { Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue }
    if ($oldJwtSecretKey) { $env:JWT_SECRET_KEY = $oldJwtSecretKey } else { Remove-Item Env:JWT_SECRET_KEY -ErrorAction SilentlyContinue }
    if ($oldEnvironment) { $env:ENVIRONMENT = $oldEnvironment } else { Remove-Item Env:ENVIRONMENT -ErrorAction SilentlyContinue }
    if ($oldChromaPath) { $env:CHROMA_PATH = $oldChromaPath } else { Remove-Item Env:CHROMA_PATH -ErrorAction SilentlyContinue }
    if (Test-Path $runDir) { Remove-Item $runDir -Recurse -Force -ErrorAction SilentlyContinue }
}