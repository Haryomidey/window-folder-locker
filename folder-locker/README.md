# Windows Folder Locker

A Windows 10 and Windows 11 folder locker with a Tkinter desktop interface.

The app protects existing folders by storing a salted PBKDF2-SHA-256 password
hash, toggling Windows hidden/system attributes, and adding a focused
current-user deny rule while locked. It keeps folder names unchanged and does
not move, rename, delete, or modify files inside the folder.

Important: this is still not encryption. The app blocks normal File Explorer
access for the current Windows user while locked, including direct path access,
but an administrator, another account with permissions, or specialized recovery
tools may still access the files.

## Installation

1. Install Python 3.9 or newer from <https://www.python.org/downloads/windows/>.
2. Keep `folder_locker.py` and the `folder_locker_app` folder together.
3. Run `folder_locker.py` from VS Code, Command Prompt, or PowerShell.

No third-party packages are required.

## GUI Usage

Start the desktop app:

```powershell
python folder_locker.py
```

The interface lets you:

- Add multiple protected folders.
- Require an app password as soon as the desktop interface opens.
- Lock, hide, and block direct File Explorer access to a selected folder.
- Unlock a folder after entering the correct password.
- Change a folder password.
- Forget a folder from the app without deleting it.
- Refresh folder status.
- Open a folder in File Explorer after entering its password.

By default, metadata and logs are stored under:

```text
%APPDATA%\FolderLocker
```

On the first GUI launch, the app asks you to create an app password. Future GUI
launches require that password before the folder list is shown.

Use a custom data directory:

```powershell
python folder_locker.py --data-dir ".\locker-data"
```

## Build a Double-Clickable App

Use `build.bat` to package the project into a Windows executable. This step uses
PyInstaller, which is only needed for building the `.exe`.

From this project folder, run:

```powershell
.\build.bat
```

When the build finishes, double-click:

```text
dist\WindowsFolderLocker.exe
```

The build also creates a Desktop shortcut named:

```text
Windows Folder Locker
```

The executable is built in windowed mode, so it opens as a normal desktop app
without a console window or a Python command prompt.

Before building, make sure Tkinter works:

```powershell
python -m tkinter
```

If that command fails with `Can't find a usable init.tcl`, repair Python:

1. Run the Python installer again.
2. Choose **Modify**.
3. Enable **tcl/tk and IDLE**.
4. Finish the install.
5. Run `.\build.bat` again.

If Windows SmartScreen warns you, choose **More info** and **Run anyway** for
your own local build. For public distribution, sign the executable with a code
signing certificate.

## Optional CLI Usage

Create password protection metadata:

```powershell
python folder_locker.py create "C:\Users\you\Documents\Private"
```

Lock and hide the folder:

```powershell
python folder_locker.py lock "C:\Users\you\Documents\Private"
```

Unlock and unhide the folder:

```powershell
python folder_locker.py unlock "C:\Users\you\Documents\Private"
```

Change the password:

```powershell
python folder_locker.py change-password "C:\Users\you\Documents\Private"
```

List protected folders:

```powershell
python folder_locker.py list
```

## Project Structure

```text
folder_locker.py              Launcher
folder_locker_app/app.py      Top-level app entry point
folder_locker_app/gui.py      Tkinter desktop interface
folder_locker_app/cli.py      Command-line interface
folder_locker_app/service.py  Core lock/unlock business logic
folder_locker_app/store.py    JSON metadata storage
folder_locker_app/security.py Password hashing and verification
folder_locker_app/windows_attributes.py Windows hidden attribute API wrapper
```

## Logs

Lock, unlock, password-change, and failed-password events are logged without
storing sensitive information. Passwords are never logged or saved.

## Future Enhancements

The app is now modular so these can be added cleanly later:

- Real folder-content encryption.
- Automatic re-locking after a timeout.
- Backup and restore of protected-folder metadata.
- A packaged `.exe` installer.
