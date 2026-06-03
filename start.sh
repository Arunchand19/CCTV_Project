#!/bin/bash
gunicorn app:app --bind 0.0.0.0:$PORT --timeout 300 --workers 1 --threads 2 --log-level info
