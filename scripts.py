import subprocess

if __name__ == '__main__':
    subprocess.Popen(["python", "main.py", "--mode", "train", "--game", "hexus", "--board_level", "\"#EB00A2\""], shell=False)
    subprocess.Popen(["python", "main.py", "--mode", "train", "--game", "hexus", "--board_level", "\"#0D2EFF\""], shell=False)
    subprocess.Popen(["python", "main.py", "--mode", "train", "--game", "hexus", "--board_level", "\"#00FF94\""], shell=False)
    subprocess.Popen(["python", "main.py", "--mode", "train", "--game", "hexus", "--board_level", "\"#8700EB\""], shell=False)
    subprocess.Popen(["python", "main.py", "--mode", "train", "--game", "hexus", "--board_level", "\"#FFFFFF\""], shell=False)
    subprocess.Popen(["python", "main.py", "--mode", "train", "--game", "hexus", "--board_level", "\"#000000\""], shell=False)


"""
python main.py --mode train --game hexus --board_level "#EB00A2" &
python main.py --mode train --game hexus --board_level "#0D2EFF" &
python main.py --mode train --game hexus --board_level "#00FF94" &
python main.py --mode train --game hexus --board_level "#8700EB" &
python main.py --mode train --game hexus --board_level "#FFFFFF" &
python main.py --mode train --game hexus --board_level "#000000" &
"""
