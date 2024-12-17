<div align="center">
    <h3 align="center">Digital Editor</h3>
    <p align="center">
        In realtime project editor
    </p>
</div>


## Getting Started
How to install the project.

### Installation

1. Setup Python virtual enviroment. Python 3.7 or higher.
```sh
python -m venv virtual_env
```

2. Enable virtual enviroment
```sh
virtual_env\Scripts\activate
```

3. Install from the requirements file
```sh
pip install -r requirements.txt
```

4. Clone the files from this reposetory
```sh
git clone https://github.com/N0TH1NG1337/Digital-Editor.git
```

5. Navigate to the Digital-Editor folder
```sh
cd Digital-Editor
```

6. Create 2 files. One for Server and 1 for Client, and for each set:
```python
# server_execute.py
from server.graphical_interface import c_server_gui

def main( ):
    c_server_gui( ).execute( )

if __name__ == "__main__":
    main( )
```
```python
# client_execute.py
from client.graphical_interface import c_client_gui

def main( ):
    c_client_gui( ).execute( )

if __name__ == "__main__":
    main( )
```

7. Execute the server or client. Note ! the file execution must be from the Digital-Editor folder.
```sh
python client_execute.py
```
```sh
python server_execute.py
```
