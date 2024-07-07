# -*- coding: utf-8 -*-
"""
Created on Sun Jul  7 17:29:06 2024

@author: Labre
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

temp_dir = os.getenv('TEMP_DIR')
tempfile = os.path.join(temp_dir, "test.html")

print(tempfile)