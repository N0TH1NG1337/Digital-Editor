<div align="center">
    <h3 align="center">Digital Editor</h3>
    <p align="center">
        In realtime project editor
    </p>
</div>


## Getting Started
How to install the project.

### Installation

1. Setup Python enviroment. Python 3.7 or higher

2. Install the next libraries
```sh
pip install imgui[full]
pip install numpy
pip install pillow
```

3. Clone the files from this reposetory
```sh
git clone https://github.com/N0TH1NG1337/Digital-Editor.git
```

4. Create 2 files. One for Server and 1 for Client, and for each set
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
