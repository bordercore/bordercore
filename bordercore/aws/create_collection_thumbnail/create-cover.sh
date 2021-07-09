IMAGE_DIR=/mnt/efs/collections
COLLECTION_UUID=$1

# In case an image is an animated gif, appending "[0]"
#  to it will choose the first image in the animation
IMAGE1="$IMAGE_DIR/$2[0]"
IMAGE2="$IMAGE_DIR/$3[0]"
IMAGE3="$IMAGE_DIR/$4[0]"
IMAGE4="$IMAGE_DIR/$5[0]"

if [ $# -eq 1 ]; then
    exit 0
elif [ $# -eq 2 ]; then
    TILE=1x1
else
    TILE=2x2
fi

# https://stackoverflow.com/questions/34834208/how-to-improve-image-output-from-montage-in-imagemagick

montage "$IMAGE1" "$IMAGE2" "$IMAGE3" "$IMAGE4" \
        -tile $TILE \
        -geometry "120x120>+1+1" \
        -background black \
        miff:- \
    | convert miff:- -resize 300x300 $IMAGE_DIR/$COLLECTION_UUID.jpg
