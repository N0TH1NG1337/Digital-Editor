# This setup script configures the Digital-Editor project by 
# 1. installing all necessary Python dependencies, 
# 2. creating a virtual environment, 
# 3. and preparing the project for execution.
$requirementsFile = "requirements.txt"
$runScriptPath = "execute.ps1"

# TO EXECUTE : Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
# Note ! Because on some mechines python is not a keyword, we will use py...
# This is python for windows defined keywork path that works fine

Clear-Host

try {
    # 1. Create the virtual environment
    py -m venv virtual_env 
}
catch {

    Write-Error "Failed to create venv folder\n Exception: $_"
    exit 1 
}

try {
    # 2. Activate the virtual environment
    .\virtual_env\Scripts\Activate.ps1
}
catch {

    Write-Error "Failed to load virtual env \n Exception: $_"
    exit 1 
}

try {
    # Check
    py -m pip install --upgrade pip

    # 3. Install requirements
    pip install -r $requirementsFile
}
catch {

    Write-Error "An error occurred: $_"
    exit 1 
}

Clear-Host

Write-Host "Project setup complete!"

icacls $runScriptPath /grant "Authenticated Users:(RX)"

# Execute the run script in a new PowerShell process
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$runScriptPath`""

deactivate

Write-Host "Done"