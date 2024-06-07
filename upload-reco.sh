#!/bin/bash

# Usage example: ./test.sh test.jpg localhost 5001

file=$1
host=$2
port=$3

curl -i -v -k \
	-X POST \
	-H "Content-Type: multipart/form-data" \
	-F filename=$file \
	-F potential-frame=@$file \
	http://$host:$port/api/v1/frame-download