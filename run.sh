#!/bin/sh

pip3 install mongoengine discord.py
git clone https://github.com/zylozs/jppbot.git

cd jppbot

python3 jppbot.py --ip=$1 --port=$2 --token=$3