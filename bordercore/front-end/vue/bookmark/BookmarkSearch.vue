<template>
    <div id="modalAddBookmark" class="modal fade" tabindex="-1" role="dialog">
        <div class="modal-dialog modal-lg" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        Add bookmark
                    </h4>
                    <button type="button" class="close" data-dismiss="modal">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="d-flex flex-column">
                        <form @submit.prevent>
                            <div class="form-group row">
                                <label class="col-form-label col-lg-1">URL</label>
                                <div class="col-lg-10 d-flex">
                                    <input id="bookmark-search-url" v-model="url" class="form-control" type="text" autocomplete="off" placeholder="https://" @change="onChange">
                                </div>
                                <div class="col-lg-1">
                                    <div class="spinner-border ml-2" :class="{'d-none': hideSpinner}" role="status">
                                        <span class="sr-only">Loading...</span>
                                    </div>
                                </div>
                            </div>
                            <div class="form-group row" :class="{'d-none': hideNameInput}">
                                <label class="col-form-label col-lg-1">Title</label>
                                <div class="col-lg-10">
                                    <input v-model="name" class="form-control" :disabled="nameInputIsDisabled" type="text" placeholder="Name" autocomplete="off">
                                </div>
                            </div>

                            <div class="row" :class="{'d-none': hideAddButton}">
                                <div class="col-lg-10 offset-lg-1 d-flex">
                                    <div class="d-flex flex-column">
                                        <div class="mt-2 text-info">
                                            <font-awesome-icon class="mr-1 pt-1 success" icon="exclamation-triangle" />
                                            {{ message }}
                                        </div>
                                        <div class="mt-2 text-info" :class="{'d-none': hideBookmarkAdded}">
                                            <font-awesome-icon class="mr-1 pt-1 success" icon="check" /> Bookmark successfully added
                                        </div>
                                    </div>
                                    <div class="ml-auto">
                                        <button type="button" class="btn btn-primary" @click="onAdd">
                                            Add
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
            getTitleFromUrlUrl: {
                default: "",
                type: String,
            },
            createBookmarkUrl: {
                default: "",
                type: String,
            },
            questionUuid: {
                default: "",
                type: String,
            },
        },
        data() {
            return {
                url: "",
                name: "",
                gettingTitle: false,
                message: "",
                bookmarkAdded: false,
                isNewBookmark: false,
                bookmarkUuid: null,
            };
        },
        computed: {
            hideNameInput() {
                return this.url === "" || !this.isNewBookmark;
            },
            hideSpinner() {
                return !this.gettingTitle;
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
        methods: {
            onChange() {
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
                        this.isNewBookmark = !response.data.existingBookmark;
                    },
                    "Error getting title from url",
                );
            },
            onAdd() {
                if (!this.bookmarkUuid) {
                    // If this is a new bookmark (ie there is no existing bookmarkUuid),
                    // create it first and get its bookmarkUuid
                    this.createBookmark();
                } else {
                    this.addRelatedBookmark(this.bookmarkUuid);
                }
            },
            addRelatedBookmark(bookmarkUuid) {
                // The bookmark gets added in the parent component
                this.$emit("addBookmark", bookmarkUuid);
                this.bookmarkAdded = true;
                // Add a delay so the user gets some feedback before the window closes
                setTimeout( () => {
                    $("#modalAddBookmark").modal("hide");

                    // Reset everything for the next bookmark
                    this.url = "";
                    this.name = "";
                    this.bookmarkAdded = false;
                }, 2000);
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
                    this.addRelatedBookmark(response.data.uuid);
                });
            },
        },

    };

</script>
