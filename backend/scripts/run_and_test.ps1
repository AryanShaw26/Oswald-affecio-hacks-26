# PowerShell script to set up the Python virtual environment, run the FastAPI backend, and test the dev endpoints.

# Ensure script runs from the script's directory
Set-Location $PSScriptRoot

# 1. Create virtual environment if it does not exist
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

# 2. Activate the virtual environment
Write-Host "Activating virtual environment..."
# Import the activation script in the current session
& "$PSScriptRoot\.venv\Scripts\Activate.ps1"

# 2b. Change to backend root (parent of scripts) so Python can find the app package
Set-Location "$PSScriptRoot\.."

# 3. Install backend dependencies
Write-Host "Installing Python dependencies..."
pip install -r "requirements.txt"

# 4. Launch the FastAPI backend (uvicorn) as a background process
Write-Host "Starting FastAPI backend..."
$uvicornProc = Start-Process -FilePath "uvicorn" -ArgumentList "app.main:app", "--reload", "--port", "8000" -PassThru -NoNewWindow
# Wait a short period for the server to start
Start-Sleep -Seconds 5

# 5. Test the POST /dev/test‑user endpoint
Write-Host "Testing POST /dev/test-user"
$payload = '{"name":"TestUser","email":"testuser@example.com"}'
try {
    $postResponse = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/dev/test-user" -ContentType "application/json" -Body $payload
    Write-Host "POST succeeded. Response:`n" $postResponse
} catch {
    Write-Error "POST request failed: $_"
    $uvicornProc | Stop-Process
    exit 1
}

# 6. Test the GET /dev/test-user/{id} endpoint using the ID returned from POST
if ($postResponse.id) {
    Write-Host "Testing GET /dev/test-user/${$postResponse.id}"
    try {
        $getResponse = Invoke-RestMethod -Method Get -Uri "http://localhost:8000/dev/test-user/$($postResponse.id)"
        Write-Host "GET succeeded. Response:`n" $getResponse
    } catch {
        Write-Error "GET request failed: $_"
        $uvicornProc | Stop-Process
        exit 1
    }
} else {
    Write-Warning "POST response did not contain an 'id' field; skipping GET test."
}

# 7. Clean up – stop the FastAPI process
Write-Host "Stopping FastAPI backend..."
$uvicornProc | Stop-Process
Write-Host "All tests completed successfully."
