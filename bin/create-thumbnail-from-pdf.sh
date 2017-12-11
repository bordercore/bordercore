#!/bin/bash

if [ $# -ne 2 ]
then
    echo "Usage: $0 <pdf> <page number>"
    exit 1
fi

INPUT_PDF=$1
PAGE_NUMBER=$2
SIZE=128

# Get the basename
BASENAME=${INPUT_PDF%.*}

OUTPUT_PDF="${BASENAME}_p${PAGE_NUMBER}.pdf"

# Extract the first
pdftk "$INPUT_PDF" cat ${PAGE_NUMBER}-${PAGE_NUMBER} output "$OUTPUT_PDF"

# OUTPUT_JPG="$BASENAME.jpg"
OUTPUT_JPG="cover-large.jpg"

pdftoppm -jpeg "$OUTPUT_PDF" > $OUTPUT_JPG

convert -thumbnail $SIZE $OUTPUT_JPG "cover-small.jpg"

rm "$OUTPUT_PDF"
# rm $OUTPUT_JPG
