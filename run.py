import os
from pathlib import Path

os.system("chmod -R 0777 /model")

with open('/model/run.sh', 'w') as f:
    f.write("mkdir /model/result\n")

    f.write(f"python3 /model/code/main.py --test_only")
        
    f.write("chmod -R 0777 /model\n")
    
os.system('chmod 0777 /model/run.sh')
os.system('sh /model/run.sh')
