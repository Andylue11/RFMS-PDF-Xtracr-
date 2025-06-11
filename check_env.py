import sys
import os
 
print(f"Python executable: {sys.executable}")
os.system(f'"{sys.executable}" -m pip --version') 