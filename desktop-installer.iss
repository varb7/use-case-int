#ifndef BundleDir
  #define BundleDir "..\desktop-dist\QuestionnaireReview"
#endif
#ifndef InstallerOutput
  #define InstallerOutput "..\dist"
#endif
[Setup]
AppId={{A877F4E5-5543-4E54-A50F-475E95C51C54}
AppName=Questionnaire Review
AppVersion=1.0.0
DefaultDirName={localappdata}\Programs\QuestionnaireReview
DefaultGroupName=Questionnaire Review
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#InstallerOutput}
OutputBaseFilename=QuestionnaireReview-Setup-1.0.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\QuestionnaireReview.exe
CloseApplications=yes

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "{#BundleDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Questionnaire Review"; Filename: "{app}\QuestionnaireReview.exe"
Name: "{autodesktop}\Questionnaire Review"; Filename: "{app}\QuestionnaireReview.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\QuestionnaireReview.exe"; Description: "Open Questionnaire Review"; Flags: nowait postinstall skipifsilent

; User jobs/cache and Credential Manager entries are deliberately retained on uninstall.
