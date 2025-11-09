# build_project.py
# Run this script inside an empty folder named car_rental_system.
# It will create:
#  - car_rental_system_ultimate.py  (full Streamlit app)
#  - car_rental.db                  (pre-seeded with 120 cars)
#  - car_images/                    (sample placeholders)
#  - requirements.txt
#  - README.md

import os
import sqlite3
import random
import textwrap
from pathlib import Path

root = Path(".").resolve()

# create images folder
(img_dir := root / "car_images").mkdir(exist_ok=True)

# create 8 placeholder image files (these are tiny text placeholders; you can replace them with real .jpg later)
for i in range(1, 9):
    p = img_dir / f"car{i}.jpg"
    if not p.exists():
        p.write_bytes(b"placeholder image file - replace with real jpg if you want\n")

# requirements.txt
(root / "requirements.txt").write_text(textwrap.dedent("""\
streamlit
pandas
altair
"""))

# README.md
(root / "README.md").write_text(textwrap.dedent("""\
# 🚗 Car Rental Management System (Streamlit + SQLite)

This project is a full DBMS mini-project built with Streamlit and SQLite.

## Features
- Admin and User accounts
- Add / View / Book / Return / Rate Cars
- 120 cars pre-loaded (mix of real & fictional)
- Analytics Dashboard (Altair)
- Simple UI theme

## How to run locally

1. Install dependencies:
```bash
pip install -r requirements.txt