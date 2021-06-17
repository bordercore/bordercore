<template>
    <div>
        <div class="modal fade" id="modalAddToPlaylist" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h4 class="modal-title" id="myModalLabel">Add To Playlist</h4>
                        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                    </div>
                    <div class="modal-body">

                        <div class="d-flex align-items-center">
                            <div class="text-nowrap">
                            Choose Playlist:
                            </div>

                        <select class="form-control ml-3" v-model="selectedPlaylist">
                            <option v-for="playlist in playLists" v-bind:key="playlist.uuid" v-bind:value="playlist.uuid">
                                {{ playlist.name }}
                            </option>
                        </select>
                        </div>

                    </div>
                    <div class="modal-footer justify-content-end">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                        <input id="btn-action" class="btn btn-primary" type="button" value="Add" @click="onClickAdd" />
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
        methods: {
            openModal(songUuid) {
                this.songUuid = songUuid;
                $("#modalAddToPlaylist").modal("show");
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
                        $("#modalAddToPlaylist").modal("hide");
                    },
                    "Song added to playlist",
                );
            },
            isManualPlaylist(playlist) {
                return playlist.type === "manual";
            },
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
    };

</script>
