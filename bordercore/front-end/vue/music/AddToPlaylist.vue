<template>
    <div>
        <div id="modalAddToPlaylist" class="modal fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h4 id="myModalLabel" class="modal-title">
                            Add To Playlist
                        </h4>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" />
                    </div>
                    <div class="modal-body">
                        <div class="d-flex align-items-center">
                            <div class="text-nowrap">
                                Choose Playlist:
                            </div>

                            <select v-model="selectedPlaylist" class="form-control ms-3">
                                <option v-for="playlist in playLists" :key="playlist.uuid" :value="playlist.uuid">
                                    {{ playlist.name }}
                                </option>
                            </select>
                        </div>
                    </div>
                    <div class="modal-footer justify-content-end">
                        <input id="btn-action" class="btn btn-primary" type="button" value="Add" @click="onClickAdd">
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>

    export default {
        props: {
            getPlaylistsUrl: {
                default: "",
                type: String,
            },
            addToPlaylistUrl: {
                default: "",
                type: String,
            },
            defaultPlaylist: {
                default: "",
                type: String,
            },
        },
        data() {
            return {
                songUuid: "",
                selectedPlaylist: "",
                playLists: [],
            };
        },
        mounted() {
            doGet(
                this,
                this.getPlaylistsUrl,
                (response) => {
                    this.playLists = response.data.results.filter(this.isManualPlaylist);
                    if (this.defaultPlaylist) {
                        this.selectedPlaylist = this.defaultPlaylist;
                    }
                },
                "Error getting playlists",
            );
        },
        methods: {
            openModal(songUuid) {
                this.songUuid = songUuid;
                const modal = new Modal("#modalAddToPlaylist");
                modal.show();
            },
            onClickAdd(datum) {
                doPost(
                    this,
                    this.addToPlaylistUrl,
                    {
                        "playlist_uuid": this.selectedPlaylist,
                        "song_uuid": this.songUuid,
                    },
                    () => {
                        const modal = Modal.getInstance(document.getElementById("modalAddToPlaylist"));
                        modal.hide();
                    },
                    "Song added to playlist",
                );
            },
            isManualPlaylist(playlist) {
                return playlist.type === "manual";
            },
        },
    };

</script>
