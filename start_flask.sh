#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python flask_app.py
