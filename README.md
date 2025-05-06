<div align="center">
    <h3 align="center">Digital Editor</h3>
    <p align="center">
        In realtime project editor
    </p>
</div>


## Getting Started
1. How to install the project.
2. How to execute the project.

### Manual Installation
1. Clone the files from this reposetory
```sh
git clone https://github.com/N0TH1NG1337/Digital-Editor.git
```

2. Setup Python virtual enviroment in the folder. Python 3.7 or higher.
```sh
python -m venv virtual_env
```

3. Enable virtual enviroment
```sh
virtual_env\Scripts\activate
```

4. Install from the requirements file
```sh
pip install -r requirements.txt
```

### Manually Running the project
1. Enable virtual enviroment
```sh
virtual_env\Scripts\activate
```

2. Run the user or host file
```sh
python user_execute.py
```
```sh
python host_execute.py
```

### Auto Installation
1. Run the setup.ps1 script
```sh
./setup
```

### Auto Running the project
1. Run the execute.ps1 script and follow the instructions there
```sh
./execute
```

### Notes
If you have any issues with running scripts just type
```sh
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```