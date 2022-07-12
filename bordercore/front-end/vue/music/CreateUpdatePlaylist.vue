<template>
    <div id="modalCreateUpdate" class="modal fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        <span id="action-type" v-html="action" />
                        Playlist
                    </h4>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" />
                </div>
                <div class="modal-body">
                    <div class="row mb-3">
                        <label class="col-lg-4 col-form-label" for="inputTitle">Name</label>
                        <div class="col-lg-8">
                            <input id="id_name" v-model="name" type="text" name="name" autocomplete="off" maxlength="200" required="required" class="form-control">
                        </div>
                    </div>

                    <div class="row">
                        <label class="col-lg-4 col-form-label" for="inputTitle">Note</label>
                        <div class="col-lg-8">
                            <textarea id="id_note" v-model="note" name="note" cols="40" rows="3" class="form-control" />
                        </div>
                    </div>

                    <div :class="{'d-none': hidePlaylistType}">
                        <hr class="mb-1">

                        <div class="text-primary">
                            <small>
                                Playlist Type
                            </small>
                        </div>

                        <div class="row mt-3">
                            <div class="col-lg-12">
                                <div class="form-check">
                                    <input v-model="smartType" class="form-check-input" type="radio" name="type" value="manual" checked>
                                    <label class="form-check-label d-flex" for="type">
                                        Manually Add Songs
                                    </label>
                                </div>
                            </div>
                        </div>

                        <div class="row mt-3">
                            <div class="col-lg-4">
                                <div class="form-check">
                                    <input v-model="smartType" class="form-check-input" type="radio" name="type" value="tag">
                                    <label class="form-check-label d-flex" for="type">
                                        Tag
                                    </label>
                                </div>
                            </div>
                            <div class="col-lg-8">
                                <tags-input id="smart-list-tag" ref="smartListTag" :search-url="tagSearchUrl + '&query='" name="tag" place-holder="Tag name" :disabled="!playlistTypeIsTag" :max-tags="1" />
                            </div>
                        </div>

                        <div class="row mt-3">
                            <div class="col-lg-12">
                                <div class="form-check">
                                    <input v-model="smartType" class="form-check-input" type="radio" name="type" value="recent">
                                    <label class="form-check-label d-flex" for="type">
                                        Recently Added Songs
                                    </label>
                                </div>
                            </div>
                        </div>

                        <div class="row mt-3">
                            <div class="col-lg-4">
                                <div class="form-check">
                                    <input v-model="smartType" type="radio" name="type" class="form-check-input" value="time">
                                    <div class="from-check-label text-nowrap">
                                        Time period
                                    </div>
                                </div>
                            </div>
                            <div class="col-lg-8">
                                <label class="form-check-label d-flex">
                                    <input v-model="startYear" class="form-control me-1" type="number" name="start_year" size="4" placeholder="Start year" autocomplete="off" :disabled="!playlistTypeIsTimePeriod">
                                    <input v-model="endYear" class="form-control ms-1" type="number" name="end_year" size="4" placeholder="End year" autocomplete="off" :disabled="!playlistTypeIsTimePeriod">
                                </label>
                            </div>
                        </div>
                    </div>

                    <div :class="{'d-none': hideOptions}">
                        <hr class="mb-1">

                        <div class="text-primary">
                            <small>
                                Options
                            </small>
                        </div>

                        <div class="row mt-3">
                            <label class="col-lg-4 col-form-label">Size</label>
                            <div class="col-lg-8">
                                <select v-model="size" class="form-control form-select" name="size">
                                    <option v-for="option in sizeOptions" :key="option.value" :value="option.value">
                                        {{ option.display }}
                                    </option>
                                </select>
                            </div>
                        </div>

                        <div class="row mt-3">
                            <label class="col-lg-4 col-form-label">Exclude Recent Listens</label>
                            <div class="col-lg-8">
                                <select v-model="exclude_recent" class="form-control form-select" name="exclude_recent">
                                    <option v-for="option in excludeRecentOptions" :key="option.value" :value="option.value">
                                        {{ option.display }}
                                    </option>
                                </select>
                            </div>
                        </div>

                        <div class="row mt-3">
                            <div class="col-lg-12">
                                <div class="form-check">
                                    <input v-model="exclude_albums" class="form-check-input" type="checkbox" name="exclude_albums">
                                    <label class="form-check-label">
                                        Exclude albums
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="modal-footer justify-content-end">
                    <input id="btn-action" class="btn btn-primary" type="submit" name="Go" :value="action" :disabled="disabledCreateButton">
                </div>
            </div>
        </div>
    </div>
</template>

<script>

    export default {
        props: {
            tagSearchUrl: {
                default: "",
                type: String,
            },
            action: {
                default: "Create",
                type: String,
            },
            playlist: {
                default: function() {
                },
                type: Object,
            },
        },
        data() {
            return {
                fields: [
                    {
                        key: "year",
                    },
                    {
                        key: "artist",
                    },
                    {
                        key: "title",
                    },
                    {
                        key: "length",
                        tdClass: "text-center",
                        thClass: "text-center",
                    },
                ],
                sizeOptions: [
                    {
                        value: "",
                        display: "Unlimited",
                    },
                    {
                        value: 5,
                        display: "5",
                    },
                    {
                        value: 10,
                        display: "10",
                    },
                    {
                        value: 20,
                        display: "20",
                    },
                    {
                        value: 50,
                        display: "50",
                    },
                    {
                        value: 100,
                        display: "100",
                    },
                ],
                excludeRecentOptions: [
                    {
                        value: "",
                        display: "No limit",
                    },
                    {
                        value: 1,
                        display: "Past Day",
                    },
                    {
                        value: 2,
                        display: "Past Two Days",
                    },
                    {
                        value: 3,
                        display: "Past Three Days",
                    },
                    {
                        value: 7,
                        display: "Past Week",
                    },
                    {
                        value: 30,
                        display: "Past Month",
                    },
                    {
                        value: 90,
                        display: "Past 3 Months",
                    },
                ],
                size: this.getAttribute("size", 20),
                name: this.getAttribute("name", ""),
                note: this.getAttribute("note", ""),
                exclude_recent: this.getAttribute("exclude_recent", ""),
                exclude_albums: this.getAttribute("exclude_albums", ""),
                smartType: this.getAttribute("type", undefined),
                startYear: this.getAttribute("start_year", undefined),
                endYear: this.getAttribute("end_year", undefined),
            };
        },
        computed: {
            disabledCreateButton() {
                if (this.smartType === "tag" &&
                    (this.$refs.smartListTag && this.$refs.smartListTag.tags.length === 0)) {
                    return true;
                } else if (this.smartType === "time" &&
                           (!this.startYear || !this.endYear) ||
                           parseInt(this.endYear) < parseInt(this.startYear)) {
                    return true;
                }
                return false;
            },
            hideOptions() {
                return this.smartType === "manual";
            },
            hidePlaylistType() {
                return this.action === "Update";
            },
            playlistTypeIsTag() {
                return this.smartType === "tag";
            },
            playlistTypeIsTimePeriod() {
                return this.smartType === "time";
            },
        },
        methods: {
            getAttribute(attribute, defaultValue) {
                if (this.playlist) {
                    if (attribute in this.playlist) {
                        return this.playlist[attribute];
                    } else if (attribute in this.playlist.parameters ) {
                        return this.playlist.parameters[attribute];
                    }
                }
                return defaultValue;
            },
            onClickCreate(evt) {
                const modal = new Modal("#modalAdd");
                modal.show();
                window.setTimeout(() => {
                    document.getElementById("id_name").focus();
                }, 500);
            },
        },
    };

</script>
