@echo off
echo Checking markets table schema...
sqlite3 marches_publics.db "PRAGMA table_info(markets);" > schema_output.txt
type schema_output.txt
echo.
echo Done
pause
