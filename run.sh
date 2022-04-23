#!/bin/sh

while :
do
	rm -rf jppbot
	git clone https://github.com/zylozs/jppbot.git
	cd jppbot
	pip3 install -r requirements.txt

	python3 jppbot.py --ip=$1 --port=$2 --token=$3
	cd ..
done