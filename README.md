# LogDetAction

## Sanal ortam (`.venv`)

Projede Python sanal ortamı kök dizinde `.venv` klasöründedir. **PowerShell** içinde etkinleştirmek için:

```powershell
cd c:\developer\LogDetAction
.\.venv\Scripts\Activate.ps1
```

Etkin olduğunda komut satırında `(.venv)` öneki görünür ve `python` yolu `.venv\Scripts\python.exe` olur.

`Activate.ps1` çalışmıyorsa (execution policy), bir kez:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

ardından `Activate.ps1` komutunu tekrar çalıştırın.

**cmd** için: `.\.venv\Scripts\activate.bat`
