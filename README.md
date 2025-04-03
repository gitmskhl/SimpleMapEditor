# Simple Map Editor
Simple Map Editor is a graphical editor that allows you to create maps for games. This editor works with the JSON format and a special map storage format used in games, which may not be compatible with formats from other applications.
![example](static/gif/editor.gif)
## Installation and Usage:
### Windows
```
git clone https://github.com/gitmskhl/level-editor.git
cd level-editor
.venv\Scripts\activate
python.exe editor.py
```

### Linux
```
git clone https://github.com/gitmskhl/level-editor.git
cd level-editor
source .venv/bin/activate
python.exe editor.py
```

## Hot Keys
| Клавиша       | Действие            |
|---------------|---------------------|
| `Up`          | move the camera up    |
| `Down`        | move the camera down  |
| `Left`        | move the camera left  |
| `Right`       | move the camera right |
| `Escape`      | Quit                  |
| `S`           | Save to the file      |
| `G`           | Change grid mode      |
| `+/-`           | Zoom      |
| `F`           | Fill      |
| `E`      | Change tile type (next)                  |
| `Q`      | Change tile type (previous)                  |
| `Space`      | Change tile variant (next)                  |
| `Ctrl + Space`      | Change tile varian (previous)                  |
| `t`      | auto-transform (only for special resources)                  |
| `Ctrl + C`      | Copy selected area |
| `Ctrl + Z`      | Undo |
| `Ctrl + alt + Z`      | Undo (fast) |
| `Ctrl + SHIFT + Z + alt `      | Redo (fast) |

Hold the Ctrl key, click on the map, then move the mouse to select tiles. After selecting, you can drag the selected tiles, delete them (`backspace`), copy them (`Ctrl + C`), or click on another empty area to cancel the selection.

## Config file
In the configuration file named `config.pr`, you can set file paths and editor properties.  

Here is an example of a configuration file:  

```
[PATH]
RESOURCES_DIR=./resources
MAP_DIR=.
MAP_FILE=./map.json


[SIZE]
base_tile_size=48
tile_size=24
change_tiles_size=16
```

- The **PATH** section contains information about the path to the resource folder and the folder where the game map file is stored or will be saved.  

- The **SIZE** section includes:  
  - `base_tile_size` – the base tile size (usually the size of resource images on your computer).  
  - `tile_size` – the current tile size, which you will see when launching the editor and can adjust by zooming in or out on the map.  
  - `change_tiles_size` – the amount by which `tile_size` changes when pressing the `+` or `-` key on the keyboard.
