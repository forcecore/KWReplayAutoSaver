!define APPNAME "Kane's Wrath Replay Auto Saver"
!define APPNAMEANDVERSION "Kane's Wrath Replay Auto Saver v1.3.1"

; Main Install settings
Name "${APPNAMEANDVERSION}"
RequestExecutionLevel user ; don't need admin privilege!
InstallDir "$INSTDIR"
OutFile "kwras_setup.exe"

; Include LogicLibrary
!include "LogicLib.nsh"

; Modern interface settings
!include "MUI2.nsh"

!define MUI_ABORTWARNING

!insertmacro MUI_PAGE_WELCOME

!define MUI_DIRECTORYPAGE_VARIABLE $INSTDIR
!insertmacro MUI_PAGE_DIRECTORY

!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Set languages (first is default language)
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_RESERVEFILE_LANGDLL



Function .onInit
	; nsis 3...
	; currently, only global maybe declared. well, not too bad, huh?
	Var /GLOBAL UserDataLeafName
	Var /GLOBAL ReplayFolderName
	ReadRegStr $UserDataLeafName HKLM "SOFTWARE\Electronic Arts\Electronic Arts\Command and Conquer 3 Kanes Wrath" "UserDataLeafName"
	ReadRegStr $ReplayFolderName HKLM "SOFTWARE\Electronic Arts\Electronic Arts\Command and Conquer 3 Kanes Wrath" "ReplayFolderName"
	StrLen $0 $UserDataLeafName
	${If} $0 = 0
		MessageBox MB_OK|MB_ICONEXCLAMATION "Kane's Wrath not found!"
		StrCpy $INSTDIR "$DOCUMENTS\KWRAS"
	${Else}
		StrCpy $INSTDIR "$DOCUMENTS\$UserDataLeafName\$ReplayFolderName\KWRAS"
	${EndIf}
FunctionEnd



Section "KWRAS" Section1

; Set Section properties
SetOverwrite on


SetOutPath "$INSTDIR"
File "..\dist\KW.ico"
File "..\dist\library.zip"
File "..\dist\maps.zip"
File "..\dist\autosaver.exe"
File "..\dist\python34.dll"
File "..\dist\wxbase30u_net_vc100.dll"
File "..\dist\wxbase30u_vc100.dll"
File "..\dist\wxmsw30u_adv_vc100.dll"
File "..\dist\wxmsw30u_core_vc100.dll"
File "..\dist\LICENSE.txt"
File "..\dist\README.txt"

;NSISdl::download /TIMEOUT=30000 "http://github.com/forcecore/KWReplayAutoSaver/releases/download/runtime_v1.0.0/runtimes.zip" $0
;Pop $R0 ;Get the return value
;  StrCmp $R0 "success" +3
;    MessageBox MB_OK "Download failed: $R0"
;    Quit
;!insertmacro MoveFile "$0" "$INSTDIR\runtimes.zip"

;NSISdl::download /TIMEOUT=30000 "http://github.com/forcecore/KWReplayAutoSaver/releases/download/map_v1.0.0/maps.zip" $0
;Pop $R0 ;Get the return value
;  StrCmp $R0 "success" +3
;    MessageBox MB_OK "Download failed: $R0"
;    Quit
;!insertmacro MoveFile "$0" "$INSTDIR\maps.zip"

SectionEnd
