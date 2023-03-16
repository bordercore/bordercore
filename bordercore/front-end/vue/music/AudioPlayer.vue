<template>
    <div class="mt-3">
        <div>
            <media-controller v-pre audio class="w-100">
                <audio
                    id="player"
                    slot="media"
                    src=""
                    type="audio/mpeg"
                />
                <media-control-bar class="media-control-bar">
                    <media-play-button />
                    <media-time-display show-duration />
                    <media-time-range />
                    <media-playback-rate-button />
                    <media-mute-button />
                    <media-volume-range />
                </media-control-bar>
            </media-controller>
        </div>
        <div class="d-flex align-items-center ms-4">
            <o-switch id="continuous_play" v-model="continuousPlay" />
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
        emits: ["current-song"],
        setup(props, ctx) {
            let currentSongUuid = "";

            const continuousPlay = ref(false);

            function getIndex() {
                return props.trackList.findIndex((x) => x.uuid === currentSongUuid);
            }

            function playTrack(songUuid, selectRow=false) {
                currentSongUuid = songUuid;

                const el = document.getElementById("player");
                el.src = props.songUrl + songUuid;
                el.play();

                if (selectRow) {
                    ctx.emit("current-song", getIndex());
                }
                setTimeout(markSongAsListenedTo, MUSIC_LISTEN_TIMEOUT);
            }

            function playNextTrack() {
                // If continous play is enabled, find the next song in the list to play
                const newIndex = getIndex() + 1;

                if (continuousPlay.value && newIndex < props.trackList.length) {
                    currentSongUuid = props.trackList[newIndex].uuid;
                    playTrack(currentSongUuid, true);
                } else {
                    // Let the parent know that the last song has played by
                    //  passing in a row index of -1
                    ctx.emit("current-song", -1);
                }
            };

            function markSongAsListenedTo() {
                doGet(
                    props.markListenedToUrl.replace(/00000000-0000-0000-0000-000000000000/, currentSongUuid),
                    () => {},
                );
            };

            onMounted(() => {
                document.getElementById("player").onended = function(evt) {
                    playNextTrack();
                };
            });

            return {
                continuousPlay,
                playTrack,
            };
        },
    };

</script>
