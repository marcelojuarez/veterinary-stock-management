; installer.iss — Script de Inno Setup para VeterinariaApp
; Compilar con: ISCC.exe installer.iss /DMyAppVersion=1.0.0

#define MyAppName "VeterinariaApp"
#define MyAppPublisher "Tu Empresa"
#define MyAppURL "https://github.com/marcelojuarez/veterinary-stock-management/"
#define MyAppExeName "VeterinariaApp.exe"

; La versión se pasa desde release.py con /DMyAppVersion=X.Y.Z
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

#ifndef OutputBaseFilename
  #define OutputBaseFilename "VeterinariaAppSetup_v{#MyAppVersion}"
#endif

[Setup]
AppId={{F1A2B3C4-D5E6-7890-ABCD-EF1234567890}}  ; Cambiá este GUID una vez y nunca más
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=dist
OutputBaseFilename={#OutputBaseFilename}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes          ; Cierra la app si está corriendo
RestartApplications=yes        ; La reactiva luego de instalar

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Íconos adicionales"

[Files]
; El .exe compilado por PyInstaller
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Archivos de datos que necesita la app
Source: "local_version.json"; DestDir: "{app}"; Flags: ignoreversion
; La DB se crea automáticamente por la app en LOCALAPPDATA al primer arranque.
; NO incluir stock.db aquí para evitar sobreescribir datos reales en updates.

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: nowait postinstall skipifsilent
