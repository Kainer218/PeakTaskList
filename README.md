# Task Manager

A clean, minimal desktop task manager for Windows. Organize tasks into projects, set deadlines, and make the app yours with dark/light themes, a custom background image, and a transparent window.

Built with Python and [PySide6](https://doc.qt.io/qtforpython-6/).

<!-- Add a screenshot here, e.g.: ![Screenshot](screenshots/main.png) -->

## Features

**Tasks**
- Add and delete tasks
- Tick the circle to move a task to the **Done** list (untick to bring it back)
- Optional deadline for every task, with date and 12-hour time picker
- Overdue tasks are highlighted in red automatically

**Projects**
- Group tasks under projects and switch between them from the sidebar
- Each project shows its number of remaining tasks
- Deleting a project moves its tasks to **No Project**
- Hide or show the sidebar with the sidebar button or `Ctrl+B`

**Appearance** (settings icon in the title bar)
- Dark mode (true black) and light mode
- Custom background image with a dim slider
- Transparent window option with a transparency slider. Only the window background becomes transparent, text and buttons stay fully visible
- Text floats directly on your background, with no panels behind it

## Getting started

### Option 1: Run from source

Requires Python 3.9+ on Windows.

```bash
python -m pip install pyside6
python task_manager.py
```

### Option 2: Build your own .exe

1. Put `task_manager.py`, `icon.ico` and `build.bat` in the same folder.
2. Double-click `build.bat`.
3. Your app will be at `dist\TaskManager.exe`.

`build.bat` installs PySide6 and PyInstaller, then runs:

```bash
python -m PyInstaller --onefile --windowed --name TaskManager --icon icon.ico --add-data "icon.ico;." task_manager.py
```

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Add the task you typed |
| `Ctrl+B` | Show / hide the projects sidebar |
| `Esc` | Close the appearance panel |

## Where your data is stored

Everything is saved locally in:

```
%APPDATA%\TaskManager
```

(usually `C:\Users\<you>\AppData\Roaming\TaskManager`)

| File | Contents |
|------|----------|
| `data.json` | Tasks, projects and settings |
| `bg_*.png/jpg/...` | A copy of your chosen background image |

The app never sends data anywhere. To back up or move your data, copy this folder. To reset the app, close it and delete the folder.

## Tech stack

- Python
- PySide6 (Qt for Python)
- PyInstaller (for the `.exe`)

## License

Add your license here (for example MIT).
