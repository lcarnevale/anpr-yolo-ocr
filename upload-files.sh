#!/bin/bash
# Usage: ./upload-files.sh dataset localhost 5001

host=$2
port=$3

image_folder=$1

for file in "$image_folder"/*; do

    if [ -f "$file" ]; then
        echo "Invio del file: $file"

        ./upload-reco.sh $file $host $port
        sleep 0.5
    fi
done