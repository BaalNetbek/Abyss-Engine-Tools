Rem This scripts works assuming that you have AudioSR installed 

set "script_dir=%~dp0"

set "seed_file=%script_dir%seed.txt"

if not exist "%seed_file%" (
  set "seed=0"
  echo %seed% > "%seed_file%"
) else (
  set /p seed=<"%seed_file%"
)

set "audiosr_output=%script_dir%out"
set "file_list=%script_dir%file_list.txt"

:loop
cmd /c audiosr -il "%file_list%" -s "%audiosr_output%" -d cpu --seed %seed% -gs 1 --ddim 10 --suffix %seed%


set /a (seed+=1)
echo %seed% > "%seed_file%" 


goto loop