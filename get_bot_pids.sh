#!/bin/bash
ps -ef | grep "python3.6 ./bot.py" | awk '{print $2}'
