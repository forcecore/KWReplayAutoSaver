IF NOT EXIST dist GOTO SKIP_DIR_DEL
del dist\*.*
:SKIP_DIR_DEL

py -3.4 setup.py py2exe
copy README.txt dist
copy LICENSE.txt dist
