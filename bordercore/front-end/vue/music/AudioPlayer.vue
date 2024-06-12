<template>
    <div class="audio-player-wrapper h-100 p-2">
        <div class="text5 text-center text-truncate mx-2">
            {{ currentTitle }}
        </div>
        <div>
            <media-controller v-pre audio class="w-100">
                <audio
                    id="player"
                    slot="media"
                    src=""
                    type="audio/mpeg"
                />
                <media-control-bar class="media-control-bar">
                    <media-play-button id="media-play-button" />
                    <media-time-display show-duration />
                    <media-time-range />
                    <media-playback-rate-button />
                    <media-mute-button />
                    <media-volume-range />
                </media-control-bar>
            </media-controller>
        </div>
        <div class="d-flex align-items-center ms-2 mt-2 pb-2">
            <o-switch id="continuous_play" v-model="continuousPlay">
                Continuous Play
            </o-switch>
        </div>
    </div>
</template>

<script>

    import useEvent from "/front-end/useEvent.js";

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
        emits: ["current-song", "is-playing"],
        setup(props, ctx) {
            const continuousPlay = ref(false);
            const currentSongUuid = ref();
            const isPlaying = ref(false);

            useEvent("click", handleClick, {id: "media-play-button"});

            function getIndex() {
                return props.trackList.findIndex((x) => x.uuid === currentSongUuid.value);
            };

            function handleClick(event) {
                isPlaying.value = !isPlaying.value;
                ctx.emit("is-playing", isPlaying.value);
            };

            function playTrack(songUuid, selectRow=false) {
                currentSongUuid.value = songUuid;
                isPlaying.value = true;

                const el = document.getElementById("player");
                el.src = props.songUrl + songUuid;
                el.play();

                if (selectRow) {
                    ctx.emit("current-song", getIndex());
                }
                setTimeout(markSongAsListenedTo, MUSIC_LISTEN_TIMEOUT);
                document.title = currentTitle.value;
            };

            function playNextTrack() {
                // If continous play is enabled, find the next song in the list to play
                const newIndex = getIndex() + 1;

                if (continuousPlay.value && newIndex < props.trackList.length) {
                    currentSongUuid.value = props.trackList[newIndex].uuid;
                    playTrack(currentSongUuid.value, true);
                } else {
                    // Let the parent know that the last song has played by
                    //  passing in a row index of -1
                    ctx.emit("current-song", -1);
                }
            };

            function markSongAsListenedTo() {
                doGet(
                    props.markListenedToUrl.replace(/00000000-0000-0000-0000-000000000000/, currentSongUuid.value),
                    () => {},
                );
            };

            const currentTitle = computed(() => {
                const song = props.trackList.find((x) => x.uuid === currentSongUuid.value);
                return song ? song.title : "";
            });

            onMounted(() => {
                document.getElementById("player").onended = function(evt) {
                    playNextTrack();
                };
            });

            return {
                continuousPlay,
                currentTitle,
                isPlaying,
                playTrack,
            };
        },
    };

</script>
