<template>
    <div id="modalAddBookmark" class="modal fade" tabindex="-1" role="dialog">
        <div class="modal-dialog modal-lg" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        {{ title }}
                    </h4>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" />
                </div>
                <div class="modal-body">
                    <div class="d-flex flex-column">
                        <form v-if="mode==='select'" @submit.prevent>
                            <div class="row mb-3">
                                <label class="col-form-label col-lg-1">Name</label>
                                <div class="col-lg-11 d-flex">
                                    <simple-suggest
                                        ref="simpleSuggest"
                                        class="w-100"
                                        display-attribute="name"
                                        value-attribute="uuid"
                                        place-holder=""
                                        :search-url="searchUrl + '?term='"
                                    />
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-lg-11 offset-lg-1 d-flex">
                                    <div class="ps-1 text-info">
                                        {{ message }}
                                    </div>
                                    <div class="ms-auto">
                                        <button class="btn btn-primary text-nowrap" @click="selectMode('add')">
                                            Add New Bookmark
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </form>
                        <form v-else @submit.prevent>
                            <div class="row">
                                <label class="col-form-label col-lg-1">URL</label>
                                <div class="col-lg-11 d-flex">
                                    <input id="bookmark-search-url" v-model="url" class="form-control" type="text" autocomplete="off" placeholder="https://" @change="onUrlSearch">
                                </div>
                            </div>
                            <div class="row">
                                <label class="col-form-label col-lg-1">Name</label>
                                <div class="col-lg-11">
                                    <input v-model="name" class="form-control" :disabled="nameInputIsDisabled" type="text" placeholder="Name" autocomplete="off">
                                </div>
                            </div>

                            <div class="row">
                                <div class="col-lg-11 offset-lg-1 d-flex">
                                    <div class="d-flex flex-column">
                                        <div v-if="gettingTitle" class="spinner-border ms-2" role="status">
                                            <span class="sr-only">Loading...</span>
                                        </div>
                                        <div class="mt-2 ps-1 text-info">
                                            {{ message }}
                                        </div>
                                        <div class="mt-2 text-info" :class="{'d-none': hideBookmarkAdded}">
                                            <font-awesome-icon class="me-1 pt-1 success" icon="check" /> Bookmark successfully added
                                        </div>
                                    </div>
                                    <div class="ms-auto">
                                        <button v-if="!hideAddButton" type="button" class="btn btn-primary me-2" @click="onAdd">
                                            Add
                                        </button>
                                        <button type="button" class="btn btn-primary" @click="selectMode('select')">
                                            Cancel
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>

    export default {

        props: {
            searchUrl: {
                default: "",
                type: String,
            },
            getTitleFromUrlUrl: {
                default: "",
                type: String,
            },
            createBookmarkUrl: {
                default: "",
                type: String,
            },
        },
        data() {
            return {
                mode: "select",
                gettingTitle: false,
                bookmarkUuid: null,
                url: "",
                name: "",
                message: "",
            };
        },
        computed: {
            title() {
                return this.mode === "select" ? "Select Bookmark" : "Add Bookmark";
            },
            hideAddButton() {
                return !this.url || !this.name;
            },
            hideBookmarkAdded() {
                return !this.bookmarkAdded;
            },
            nameInputIsDisabled() {
                return this.bookmarkUuid !== null;
            },
        },
        mounted() {
            this.selectMode(this.mode);
        },
        methods: {
            select(selection) {
                // The parent component receives the bookmark uuid and takes action
                this.$emit("select-bookmark", selection);

                const modal = Modal.getInstance(document.getElementById("modalAddBookmark"));
                modal.hide();

                // Reset parameters
                this.mode = "select";
                this.bookmarkUuid = null;
                this.url = "";
                this.name = "";

                // First check if the simpleSuggest component exists. It won't if we're
                //  in "add" mode and the UI is hidden.
                if (this.$refs.simpleSuggest) {
                    this.$nextTick(() => {
                        this.$refs.simpleSuggest.$refs.suggestComponent.$el.querySelector("input").blur();
                        this.$refs.simpleSuggest.$refs.suggestComponent.setText("");
                    });
                }
            },
            onUrlSearch(evt) {
                this.message = "";
                this.bookmarkUuid = null;
                const url = document.getElementById("bookmark-search-url").value;

                if (!url) {
                    return;
                }

                this.gettingTitle = true;

                doGet(
                    this,
                    this.getTitleFromUrlUrl + "?url=" + encodeURIComponent(url),
                    (response) => {
                        const title = response.data.title;
                        if (title) {
                            this.name = title;
                            this.bookmarkUuid = response.data.bookmarkUuid;
                        }
                        this.message = response.data.message;
                        this.gettingTitle = false;
                    },
                    "Error getting title from url",
                );
            },
            selectMode(mode) {
                this.mode = mode;
                if (this.mode === "select") {
                    this.message = "Search for an existing bookmark by name";
                } else {
                    this.message = "Add a new bookmark";
                    this.url = "";
                    this.name = "";
                }
            },
            onAdd() {
                if (!this.bookmarkUuid) {
                    // If this is a new bookmark (ie there is no existing bookmarkUuid),
                    // create it first and get its bookmarkUuid
                    this.createBookmark();
                } else {
                    this.select({"uuid": this.bookmarkUuid});
                }
            },
            createBookmark() {
                const bodyFormData = new URLSearchParams();
                bodyFormData.append("url", this.url);
                bodyFormData.append("name", this.name);

                // We can't use doPost because the DRF doesn't
                // return a "status": "OK" in the response.
                axios(this.createBookmarkUrl, {
                    method: "POST",
                    data: bodyFormData,
                }).then((response) => {
                    this.select({"uuid": response.data.uuid});
                });
            },
        },

    };

</script>
