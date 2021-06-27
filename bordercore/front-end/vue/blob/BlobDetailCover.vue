<template>
    <div>
        <img v-if="coverInfo" :src="coverInfo.url" :height="coverInfo.height_cropped" :width="coverInfo.width_cropped" data-toggle="modal" data-target="#myModal3">

        <div v-if="coverInfo" id="myModal3" class="modal fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
            <div class="modal-dialog modal-dialog-centered w-75 mw-100" role="document">
                <div class="modal-content">
                    <div class="modal-body">
                        <div>
                            <img :src="coverInfo.url" class="w-100">
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
            initialCoverInfo: {
                default: function() {
                },
                type: Object,
            },
            coverUrl: {
                default: "",
                type: String,
            },
        },
        data() {
            return {
                coverInfo: {},
                getCoverImageAttemptIntervals: [1000, 3000],
                getCoverImageAttempts: 0,
            };
        },
        mounted() {
            this.coverInfo = this.initialCoverInfo;
            if (Object.keys(this.coverInfo).length === 0) {
                // New blobs might not have cover images yet.
                // Try three times to retrieve one before giving up.
                setTimeout( () => {
                    this.getCoverImage();
                }, this.getCoverImageAttemptIntervals[this.getCoverImageAttempts]);
            }
        },
        methods: {
            getCoverImage() {
                this.getCoverImageAttempts++;
                console.log(`Retrieving cover image, attempt #${this.getCoverImageAttempts}`);
                doGet(
                    this,
                    this.coverUrl,
                    (response) => {
                        if (response.data.url) {
                            this.coverInfo = response.data;
                        } else {
                            // Keep trying to retrieve the cover image until we run out of attempts
                            if (this.getCoverImageAttempts <= this.getCoverImageAttemptIntervals.length) {
                                setTimeout( () => {
                                    this.getCoverImage();
                                }, this.getCoverImageAttemptIntervals[this.getCoverImageAttempts-1]);
                            }
                        }
                    },
                    "Error getting cover info",
                );
            },
        },
    };

</script>
