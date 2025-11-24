#!/bin/bash
# Run lesson plan indexing automatically (can be scheduled via cron or run manually)
cd "$(dirname "$0")"
python3 index_lesson_plans.py
