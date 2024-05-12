Automation for [versatile_audio_super_resolution](https://github.com/haoheliu/versatile_audio_super_resolution)

Install requierments (you need Python 3.9)
```
pip install -r requirements.txt
pip install audiosr==0.0.7
```
Run script stages:
To automaticaly update list of files process (sound/)
```
list_sounds.py 
```
As long as you wish, this generates infinitely:
```
audiosr_runner.bat
```
To finalize:
```
out/sort_files.py
```
You can you can adjust audiosr arguments in audiosr_runner line 26, for example set -d cuda if you have nVidia gpu. 
Set initial seed in seed.txt (not necessery, it auto increments)


