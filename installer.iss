#define AppName "Doc Converter"
#define AppVersion "1.0.0"
#define AppPublisher "Doc Converter"
#define AppExeName "DocConverter_licensed.exe"
#define AppURL "https://github.com"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\DocConverter
DefaultGroupName={#AppName}
AllowNoIcons=yes
LicenseFile=
OutputDir=installer_output
OutputBaseFilename=DocConverter_Licensed_Setup_v{#AppVersion}
SetupIconFile=icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
VersionInfoVersion={#AppVersion}
VersionInfoProductName={#AppName}

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
; Ярлыки
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные значки:"; Flags: unchecked

; Движки конвертации (загружаются через winget)
Name: "install_libreoffice"; Description: "LibreOffice  — DOCX, PDF, XLSX, PPTX и др.  (~360 МБ)"; GroupDescription: "Загрузить и установить движки конвертации:"; Check: not LibreOfficeInstalled
Name: "install_calibre";     Description: "Calibre  — EPUB, MOBI, FB2, AZW3 и др.  (~215 МБ)"; GroupDescription: "Загрузить и установить движки конвертации:"; Check: not CalibreInstalled
Name: "install_pandoc";      Description: "Pandoc  — Markdown, RST, HTML и др.  (~50 МБ)";   GroupDescription: "Загрузить и установить движки конвертации:"; Check: not PandocInstalled

[Files]
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Удалить {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Установка движков через winget (тихо, без окон)
Filename: "winget"; Parameters: "install --id TheDocumentFoundation.LibreOffice --accept-package-agreements --accept-source-agreements --silent"; \
  Description: "Установка LibreOffice..."; Flags: waituntilterminated runhidden; Tasks: install_libreoffice
Filename: "winget"; Parameters: "install --id calibre.calibre --accept-package-agreements --accept-source-agreements --silent"; \
  Description: "Установка Calibre..."; Flags: waituntilterminated runhidden; Tasks: install_calibre
Filename: "winget"; Parameters: "install --id JohnMacFarlane.Pandoc --accept-package-agreements --accept-source-agreements --silent"; \
  Description: "Установка Pandoc..."; Flags: waituntilterminated runhidden; Tasks: install_pandoc

; Запуск приложения после установки
Filename: "{app}\{#AppExeName}"; Description: "Запустить {#AppName}"; Flags: nowait postinstall skipifsilent

[Code]

{ Проверка — установлен ли уже LibreOffice }
function LibreOfficeInstalled: Boolean;
begin
  Result := FileExists('C:\Program Files\LibreOffice\program\soffice.exe') or
            FileExists('C:\Program Files (x86)\LibreOffice\program\soffice.exe');
end;

{ Проверка — установлен ли уже Calibre }
function CalibreInstalled: Boolean;
begin
  Result := FileExists('C:\Program Files\Calibre2\ebook-convert.exe') or
            FileExists('C:\Program Files (x86)\Calibre2\ebook-convert.exe');
end;

{ Проверка — установлен ли уже Pandoc }
function PandocInstalled: Boolean;
var
  ResultCode: Integer;
begin
  Result := RegKeyExists(HKEY_LOCAL_MACHINE, 'SOFTWARE\Pandoc') or
            FileExists('C:\Program Files\Pandoc\pandoc.exe');
end;

procedure InitializeWizard;
var
  InfoPage: TOutputMsgMemoWizardPage;
  InfoText: String;
begin
  InfoText :=
    'Doc Converter — конвертер офисных документов и электронных книг.' + #13#10 + #13#10 +
    'Для конвертации используются сторонние движки с открытым исходным кодом.' + #13#10 +
    'На следующем шаге вы можете выбрать, какие из них установить.' + #13#10 + #13#10 +
    'Уже установленные программы будут автоматически исключены из списка.' + #13#10 + #13#10 +
    'Движки скачиваются через Windows Package Manager (winget).' + #13#10 +
    'Требуется подключение к интернету.';

  InfoPage := CreateOutputMsgMemoPage(
    wpWelcome,
    'О программе',
    'Doc Converter и необходимые компоненты',
    InfoText,
    ''
  );
end;
