<template>
    <div class="mt-3">
        <div>
            <audio id="player" controls controlsList="nodownload" class="mw-100">
                <source src="" type="audio/mpeg">
                Your browser does not support the audio tag.
            </audio>
        </div>
        <div class="d-flex align-items-center ms-4">
            <input id="continuous_play" type="checkbox" @change="onContinuousPlay">
            <label for="continuous_play" class="ms-2">Continous Play</label>
        </div>
    </div>
</template>

<script>

    export default {
        props: {
            songUrl: {
                default: "",
                type: String,
            },
            markListenedToUrl: {
                default: "",
                type: String,
            },
            trackList: {
                default: () => [],
                type: Array,
            },
        },
        data() {
            return {
                continuousPlay: false,
                currentSongUuid: null,
            };
        },
        mounted() {
            document.getElementById("player").onended = function(evt) {
                EventBus.$emit("onEnded");
            };

            EventBus.$on("onEnded", (payload) => {
                // If continous play is enabled, find the next song in the list to play
                const newIndex = this.getIndex() + 1;

                if (this.continuousPlay && newIndex < this.trackList.length) {
                    this.currentSongUuid = this.trackList[newIndex].uuid;
                    this.playTrack(this.currentSongUuid, true);
                } else {
                    // Let the parent know that the last song has played by
                    //  passing in a row index of -1
                    this.$emit("current-song", -1);
                }
            });
        },
        methods: {
            getIndex() {
                return this.trackList.findIndex((x) => x.uuid === this.currentSongUuid);
            },
            playTrack(songUuid, selectRow=false) {
                this.currentSongUuid = songUuid;

                const el = document.getElementById("player");
                el.src = this.songUrl + songUuid;
                el.play();

                if (selectRow) {
                    this.$emit("current-song", this.getIndex());
                }

                setTimeout(this.markSongAsListenedTo, MUSIC_LISTEN_TIMEOUT);
            },
            onContinuousPlay(evt) {
                this.continuousPlay = evt.srcElement.checked;
            },
            markSongAsListenedTo() {
                const url = this.markListenedToUrl.replace(/00000000-0000-0000-0000-000000000000/, this.currentSongUuid);
                axios.get(url)
                     .then((response) => {
                     });
            },
        },
    };

</script>
