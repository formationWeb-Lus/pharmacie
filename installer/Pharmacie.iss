[Setup]
AppName=Pharmacie
AppVersion=1.0.0
DefaultDirName={autopf}\Pharmacie
DefaultGroupName=Pharmacie
OutputDir=..\installer-output
OutputBaseFilename=PharmacieSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "..\dist\Pharmacie\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\Pharmacie"; Filename: "{app}\Pharmacie.exe"
Name: "{commondesktop}\Pharmacie"; Filename: "{app}\Pharmacie.exe"

[Run]
Filename: "{app}\Pharmacie.exe"; Description: "Lancer Pharmacie"; Flags: nowait postinstall skipifsilent
