<template>
    <div :class="imageClass">
        <img class="h-100 w-100" :src="coverUrl" data-bs-toggle="modal" data-bs-target="#myModal3" @error="loadCoverImage()">
        <div id="myModal3" class="modal fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
            <div class="modal-dialog modal-dialog-centered w-75 mw-100" role="document">
                <div class="modal-content">
                    <div class="modal-body">
                        <div>
                            <img class="cover_image w-100" :src="coverUrl">
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>

    export default {
        props: {
            coverUrl: {
                default: "",
                type: String,
            },
            fullSize: {
                default: true,
                type: Boolean,
            },
        },
        setup(props) {
            const imageAttemptIntervals = [1000, 3000, 6000];
            let imageAttempts = 0;

            function loadCoverImage() {
                // New blobs might not have cover images yet.
                // Try three times to retrieve one before giving up.

                // While we do this, hide the broken images (inline and modal)
                for (const element of document.getElementsByClassName("cover_image")) {
                    element.style.display = "none";
                }

                setTimeout( () => {
                    getCoverImage();
                }, imageAttemptIntervals[imageAttempts]);
            };

            function getCoverImage() {
                imageAttempts++;

                if (imageAttempts > imageAttemptIntervals.length) {
                    return;
                }
                console.log(`Retrieving cover image, attempt #${imageAttempts}`);

                // Add a datetime to bust the cache
                for (const element of document.getElementsByClassName("cover_image")) {
                    element.src = props.coverUrl + "&nocache=" + new Date().getTime();
                }

                // Reveal the image
                for (const element of document.getElementsByClassName("cover_image")) {
                    element.style.display = "inline";
                }
            };

            const imageClass = computed(() => {
                return props.fullSize ?
                    "blob-detail-cover-image" :
                    "blob-detail-cover-image-with-content";
            });

            return {
                loadCoverImage,
                imageClass,
            };
        },
    };

</script>
