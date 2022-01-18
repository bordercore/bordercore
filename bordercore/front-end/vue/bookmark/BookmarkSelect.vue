<template>
    <div id="modalAddBookmark" class="modal fade" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        Select bookmark
                    </h4>
                    <button type="button" class="close" data-dismiss="modal">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="d-flex flex-column">
                        <form v-if="mode==='search'" @submit.prevent>
                            <div class="form-group">
                                <simple-suggest
                                    ref="simpleSuggest"
                                    class="w-100"
                                    display-attribute="name"
                                    value-attribute="uuid"
                                    place-holder="Url Name"
                                    :search-url="searchUrl + '?term='"
                                />
                            </div>
                        </form>
                        <form v-else @submit.prevent>
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
            searchUrl: {
                default: "",
                type: String,
            },
        },
        data() {
            return {
                mode: "search",
                gettingTitle: false,
            };
        },
        computed: {
            hideSpinner() {
                return !this.gettingTitle;
            },
        },
        methods: {
            select(selection) {
                // The parent component receives the bookmark uuid and takes action
                this.$emit("select-bookmark", selection.uuid);

                $("#modalAddBookmark").modal("hide");

                this.$nextTick(() => {
                    this.$refs.simpleSuggest.$refs.suggestComponent.$el.querySelector("input").blur();
                    this.$refs.simpleSuggest.$refs.suggestComponent.setText("");
                });
            },
            onChange(evt) {
                console.log("onChange: " + evt);
            },
        },

    };

</script>
