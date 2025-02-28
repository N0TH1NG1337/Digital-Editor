

try {
    # Activate the virtual environment
    .\virutal_env\Scripts\Activate.ps1
}
catch {
    try {
        # Sometimes the virtual environment is in different folder.
        # Try the defualt one
        .\.venv\Scripts\Activate.ps1
    }
    catch {
        <#Do this if a terminating exception happens#>
        Write-Error "Failed to load virtual env \n Exception: $_"
        exit 1
    }
}

Clear-Host

Write-Host "Welcome user to Digital Editor [preview]"
Write-Host ""
Write-Host "Choose which version to run:"
Write-Host "1. user" 
Write-Host "2. host" 
Write-Host ""
Write-Host "0. exit" 
Write-Host ""

while ($true) { # Loop for valaid input
    
    $selection = Read-Host "Enter the number (0, 1 or 2)"

    if ($selection -eq 1) {

        $selectedScript = "user_execute.py"
        break

    } elseif ($selection -eq 2) {

        $selectedScript = "host_execute.py"
        break

    } elseif ($selection -eq 0) {

        $selectedScript = "exit"
        break

    } else {
        
        Write-Host "Invalid input. Please enter 1 or 2."
    }
}

if ($selectedScript -eq "exit") {
    Write-Host "Exiting..."
    deactivate
    exit
}

# Check if the selected script exists before trying to run it
if (Test-Path $selectedScript) {
    python $selectedScript
} else {
    Write-Error "Selected script '$selectedScript' not found."
}

deactivate

Write-Host "Script execution complete."