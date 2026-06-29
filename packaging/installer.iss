; Instalador de Windows para COMPScrapper (Inno Setup).
; Instala en Archivos de programa, crea accesos directos y actualiza in-place la
; versión previa (mismo AppId). Se compila en CI con: iscc packaging/installer.iss
; Requiere el resultado de PyInstaller en dist\COMPScrapper\ (onedir).

#define MyAppName "COMPScrapper"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "CONACOM"
#define MyAppExeName "COMPScrapper.exe"

[Setup]
; AppId fijo: permite detectar y reemplazar la instalación previa al actualizar.
AppId={{8F3C2A10-7B4E-4C9A-9E21-0C0FE2A1B7D3}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=COMPScrapper-setup
SetupIconFile=icono.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "..\dist\COMPScrapper\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir COMPScrapper"; Flags: nowait postinstall skipifsilent
