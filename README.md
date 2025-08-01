# GUI of the Raspberry Pi
![image](https://github.com/user-attachments/assets/ac0ae203-a6ff-4c12-b10b-f4a35f3ea825)

## Notes to Remember
- Version 1: run.py
- Version 2: controller.py

### Version 2.1
- uses python classes
- fake_picamera2 and fake_gpio libaries for designing the app without an raspberrypi

### Version 2
- user controlled conveyor belt
- improved user interface
- same features such as picture of side 1 and 2 view and live video feed

### Version 1
- fully automated where the conveyor moves based on static time assigned
- side 1 and side 2 mango view
- live video feed



## Kenan's TODO List
- what to put on the list of results
- check for magic numbers and inconsistent var naming
- start the help page
- ~~make the controller buttons and gpio~~
- ~~add the rpi camera with live video feed~~
- ~~add the top part picturing~~
- ~~add the bottom part picturing~~
- ~~add the user priority input~~
- ~~make it work~~
- ~~display the results on the controller similar to the run.py~~

## If first time to PUSH and COMMIT
clone this first
```bash
  git clone https://github.com/francis-bautista/gui_conveyor.git
```
setting up your venv
```bash
  cd path/to/project
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
```
### How to PUSH and COMMIT changes 
Add File
```bash
  git add .
```
Commit with a MESSAGE
```bash
  git commit -m "message"
```
Push to the branch
```bash
  git push
```

### Merge Conflict notes
```bash
git merge --abort
git fetch origin
git reset --hard origin/master
```

## Python Libraries Required
- tkinter, customtkinter
- torch, torchvision, efficientnet_pytorch
- opencv, scipy, numpy, imutils

