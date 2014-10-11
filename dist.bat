IF NOT EXIST dist GOTO SKIP_DIR_DEL
del dist\*.*
:SKIP_DIR_DEL

copy README.txt dist
copy LICENSE.txt dist
copy KW.ico dist

py -3.4 setup.py py2exe
