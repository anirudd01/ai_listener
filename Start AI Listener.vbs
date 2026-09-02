' Launches AI Listener silently (no console window) using the project's virtual environment.
Set fso = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = scriptDir & "\.venv\Scripts\pythonw.exe"
mainScript = scriptDir & "\main.py"

Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = scriptDir
shell.Run """" & pythonw & """ """ & mainScript & """", 0, False
