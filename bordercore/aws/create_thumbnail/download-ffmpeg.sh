#!/bin/bash

FILE="ffmpeg-release-amd64-static.tar.xz"
URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"

if [[ ! -e $FILE ]]; then
    echo "File $FILE not found! Downloading from $URL..."
    wget "$URL"
    tar xvf $FILE
else
    echo "File $FILE already exists."
fi
