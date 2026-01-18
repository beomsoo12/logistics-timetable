; Inno Setup Script for 견우물류 타임테이블
; Inno Setup 6.0 이상 필요

#define MyAppName "견우물류 타임테이블"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "견우물류"
#define MyAppExeName "견우물류타임테이블.exe"

[Setup]
; 기본 설정
AppId={{E8F9A3B2-7C1D-4E5F-9A2B-8D3C4E5F6A7B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; 라이선스 파일 (있으면 주석 해제)
; LicenseFile=LICENSE.txt
OutputDir=dist
OutputBaseFilename=견우물류타임테이블_v{#MyAppVersion}_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; 아이콘 (있으면 주석 해제)
; SetupIconFile=icon.ico
; 관리자 권한 요청
PrivilegesRequired=admin
; 아키텍처
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 실행 파일
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; 설정 파일 템플릿
Source: "db_config.py"; DestDir: "{app}"; DestName: "db_config_template.py"; Flags: ignoreversion
; README 파일
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
; 버전 파일
Source: "version.py"; DestDir: "{app}"; Flags: ignoreversion
; data 폴더 생성
Source: "data\.gitkeep"; DestDir: "{app}\data"; Flags: ignoreversion

[Dirs]
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\logs"; Permissions: users-modify

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\설정 파일 편집"; Filename: "notepad.exe"; Parameters: """{app}\db_config.py"""
Name: "{group}\설치 폴더 열기"; Filename: "{app}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Name: "{group}\README 읽기"; Filename: "notepad.exe"; Parameters: """{app}\README.md"""; Flags: postinstall skipifsilent nowait
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
var
  ConfigPage: TInputQueryWizardPage;
  ServerEdit, DatabaseEdit, UsernameEdit, PasswordEdit: TEdit;
  UseWindowsAuthCheckBox: TNewCheckBox;

procedure InitializeWizard;
begin
  { 데이터베이스 설정 페이지 생성 }
  ConfigPage := CreateInputQueryPage(wpSelectDir,
    '데이터베이스 설정',
    'SQL Server 연결 정보를 입력하세요',
    '프로그램이 사용할 데이터베이스 연결 정보를 입력합니다. ' +
    'Windows 인증을 사용하는 경우 체크박스를 선택하세요.');

  { Server 입력 }
  ConfigPage.Add('SQL Server 주소:', False);
  ServerEdit := ConfigPage.Edits[0];
  ServerEdit.Text := 'localhost';

  { Database 입력 }
  ConfigPage.Add('데이터베이스 이름:', False);
  DatabaseEdit := ConfigPage.Edits[1];
  DatabaseEdit.Text := 'LogisticsDB';

  { Windows 인증 체크박스 }
  UseWindowsAuthCheckBox := TNewCheckBox.Create(ConfigPage);
  UseWindowsAuthCheckBox.Parent := ConfigPage.Surface;
  UseWindowsAuthCheckBox.Top := ConfigPage.Edits[1].Top + ConfigPage.Edits[1].Height + ScaleY(16);
  UseWindowsAuthCheckBox.Width := ConfigPage.SurfaceWidth;
  UseWindowsAuthCheckBox.Caption := 'Windows 인증 사용';
  UseWindowsAuthCheckBox.Checked := True;

  { Username 입력 }
  ConfigPage.Add('사용자명 (Windows 인증 미사용시):', False);
  UsernameEdit := ConfigPage.Edits[2];
  UsernameEdit.Text := 'sa';
  UsernameEdit.Enabled := False;

  { Password 입력 }
  ConfigPage.Add('비밀번호 (Windows 인증 미사용시):', True);
  PasswordEdit := ConfigPage.Edits[3];
  PasswordEdit.Enabled := False;

  { Windows 인증 체크박스 이벤트 }
  UseWindowsAuthCheckBox.OnClick := @WindowsAuthCheckBoxClick;
end;

procedure WindowsAuthCheckBoxClick(Sender: TObject);
begin
  UsernameEdit.Enabled := not UseWindowsAuthCheckBox.Checked;
  PasswordEdit.Enabled := not UseWindowsAuthCheckBox.Checked;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;

  if CurPageID = ConfigPage.ID then
  begin
    { 입력 검증 }
    if Trim(ServerEdit.Text) = '' then
    begin
      MsgBox('SQL Server 주소를 입력하세요.', mbError, MB_OK);
      Result := False;
      Exit;
    end;

    if Trim(DatabaseEdit.Text) = '' then
    begin
      MsgBox('데이터베이스 이름을 입력하세요.', mbError, MB_OK);
      Result := False;
      Exit;
    end;

    if not UseWindowsAuthCheckBox.Checked then
    begin
      if Trim(UsernameEdit.Text) = '' then
      begin
        MsgBox('사용자명을 입력하세요.', mbError, MB_OK);
        Result := False;
        Exit;
      end;

      if Trim(PasswordEdit.Text) = '' then
      begin
        MsgBox('비밀번호를 입력하세요.', mbError, MB_OK);
        Result := False;
        Exit;
      end;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigContent: AnsiString;
  ConfigFilePath: String;
begin
  if CurStep = ssPostInstall then
  begin
    { db_config.py 파일 생성 }
    ConfigFilePath := ExpandConstant('{app}\db_config.py');

    if UseWindowsAuthCheckBox.Checked then
    begin
      { Windows 인증 }
      ConfigContent :=
        '# 데이터베이스 연결 설정' + #13#10 +
        '# 이 파일은 자동으로 생성되었습니다.' + #13#10 +
        '#' + #13#10 +
        'DB_CONFIG = {' + #13#10 +
        '    ''server'': ''' + ServerEdit.Text + ''',' + #13#10 +
        '    ''database'': ''' + DatabaseEdit.Text + ''',' + #13#10 +
        '    ''trusted_connection'': ''yes'',' + #13#10 +
        '    ''driver'': ''{ODBC Driver 17 for SQL Server}''' + #13#10 +
        '}' + #13#10;
    end
    else
    begin
      { SQL Server 인증 }
      ConfigContent :=
        '# 데이터베이스 연결 설정' + #13#10 +
        '# 이 파일은 자동으로 생성되었습니다.' + #13#10 +
        '#' + #13#10 +
        'DB_CONFIG = {' + #13#10 +
        '    ''server'': ''' + ServerEdit.Text + ''',' + #13#10 +
        '    ''database'': ''' + DatabaseEdit.Text + ''',' + #13#10 +
        '    ''username'': ''' + UsernameEdit.Text + ''',' + #13#10 +
        '    ''password'': ''' + PasswordEdit.Text + ''',' + #13#10 +
        '    ''driver'': ''{ODBC Driver 17 for SQL Server}''' + #13#10 +
        '}' + #13#10;
    end;

    { 파일 저장 }
    SaveStringToFile(ConfigFilePath, ConfigContent, False);
  end;
end;

[UninstallDelete]
Type: files; Name: "{app}\db_config.py"
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\*.backup"
