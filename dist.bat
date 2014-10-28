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

py -3.4 setup.py py2exe

@echo ""
@echo ""
@echo ""
@echo Don't forget to copy maps folder into dist folder!
