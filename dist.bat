IF EXIST dist GOTO SKIP_MKDIR
mkdir dist
:SKIP_MKDIR

IF NOT EXIST dist GOTO SKIP_DIR_DEL
del dist\*.*
:SKIP_DIR_DEL

rem these files are now specified in setup.py
rem copy README.txt dist
rem copy LICENSE.txt dist
rem copy KW.ico dist
rem copy maps.zip dist

@echo Remember to zip maps directory as maps.zip!
py -3.5 setup.py py2exe
