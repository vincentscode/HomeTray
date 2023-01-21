Set oShell = CreateObject ("Wscript.Shell") 
Dim strArgs
strArgs = "cmd /c python home_tray.py"
oShell.Run strArgs, 0, false