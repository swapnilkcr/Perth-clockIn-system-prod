@echo off
echo Starting backend server...
start cmd /k python "S:\DATAPERTH\Perth Log Job system\Clock_In_prod\prod_app\backend.py" %*

echo Starting frontend server...
start cmd /k python -m http.server 3001 --bind 10.0.0.80

pause