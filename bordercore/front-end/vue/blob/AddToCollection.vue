<template>
    <div id="modalAddToCollection" class="modal fade" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        Add blob to collection
                    </h4>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" @click="closeModal" />
                </div>
                <div class="modal-body">
                    <div class="d-flex flex-column">
                        <div id="search-collections" :class="{'d-none': !hideAddCollection}" class="search-with-doctypes mb-0">
                            <vue-simple-suggest
                                ref="suggestComponent"
                                display-attribute="name"
                                value-attribute="uuid"
                                :list="search"
                                name="search"
                                :filter-by-query="true"
                                :debounce="200"
                                :min-length="2"
                                :max-suggestions="20"
                                placeholder="Search collections"
                                :styles="autoCompleteStyle"
                                autocomplete="off"
                                :autofocus="false"
                                @select="select"
                            >
                                <div slot="suggestion-item" slot-scope="{ suggestion }">
                                    <div :class="{'suggestion-item-disabled': suggestion.contains_blob}" class="top-search-suggestion d-flex align-items-center" @click.stop="onClick(suggestion)">
                                        <div>
                                            <img class="me-2" width="50" height="50" :src="suggestion.cover_url">
                                        </div>
                                        <div class="me-1">
                                            {{ displayProperty(suggestion) }}
                                        </div>
                                        <div class="text-primary mx-1">
                                            <small>{{ suggestion.num_blobs }} blobs</small>
                                        </div>
                                        <div v-if="suggestion.contains_blob" class="text-warning ms-auto">
                                            Added
                                        </div>
                                    </div>
                                </div>
                            </vue-simple-suggest>
                            <div class="mt-3">
                                <button class="btn btn-primary d-flex ms-auto" @click="showCreateNewCollection">
                                    Create new collection
                                </button>
                            </div>
                        </div>
                        <div id="add-collection" :class="{'d-none': hideAddCollection}">
                            <input class="form-control mb-3" type="text" name="collection-name" placeholder="Collection name" autocomplete="off">
                            <button class="btn btn-primary d-flex ms-auto" @click="createNewCollection">
                                Create
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>

    import VueSimpleSuggest from "vue-simple-suggest";

    export default {

        components: {
            VueSimpleSuggest,
        },
        props: {
            blobUuid: {
                default: "",
                type: String,
            },
            searchUrl: {
                default: "",
                type: String,
            },
            addBlobUrl: {
                default: "",
                type: String,
            },
            addCollectionUrl: {
                default: "",
                type: String,
            },
        },
        data() {
            return {
                name: "",
                collectionList: [],
                autoCompleteStyle: {
                    vueSimpleSuggest: "position-relative",
                    inputWrapper: "",
                    defaultInput: "form-control search-box-input",
                    suggestions: "position-absolute list-group z-1000",
                    suggestItem: "list-group-item",
                },
                hideAddCollection: true,
            };
        },
        methods: {
            displayProperty: function(suggestion) {
                return this.$refs.suggestComponent.displayProperty(suggestion);
            },
            onClick(suggestion) {
                if (!suggestion.contains_blob) {
                    this.select(suggestion);
                }
            },
            search(query) {
                try {
                    const url = this.searchUrl;
                    return axios.get(url + query)
                                .then((response) => {
                                    return response.data;
                                });
                } catch (error) {
                    console.log(`Error: ${error}`);
                }
            },
            select(selection) {
                // Don't allow selecting a collection the blob is already part of
                if (selection.contains_blob) {
                    return;
                }
                this.addBlobToCollection(selection.uuid);
            },
            addBlobToCollection(collectionUuid) {
                doPost(
                    this,
                    this.addBlobUrl,
                    {
                        "collection_uuid": collectionUuid,
                        "blob_uuid": this.blobUuid,
                    },
                    (response) => {
                        this.$emit("add-to-collection", collectionUuid);

                        const modal = Modal.getInstance(document.getElementById("modalAddToCollection"));
                        modal.hide();

                        this.$nextTick(() => {
                            this.$refs.suggestComponent.$el.querySelector("input").blur();
                            this.$refs.suggestComponent.setText("");
                        });
                    },
                    "",
                    "",
                );
            },
            showCreateNewCollection() {
                this.hideAddCollection = false;
                setTimeout( () => {
                    document.querySelector("#add-collection input").focus();
                }, 100);
            },
            createNewCollection() {
                const name = document.querySelector("#add-collection input").value;

                doPost(
                    this,
                    this.addCollectionUrl,
                    {
                        "name": name,
                    },
                    (response) => {
                        const collectionUuid = response.data.uuid;

                        this.addBlobToCollection(collectionUuid);

                        this.$emit("add-to-collection", collectionUuid);

                        const modal = Modal.getInstance(document.getElementById("modalAddToCollection"));
                        modal.hide();
                        this.hideAddCollection = true;

                        this.$nextTick(() => {
                            this.$refs.suggestComponent.$el.querySelector("input").blur();
                            this.$refs.suggestComponent.setText("");
                        });
                    },
                    "",
                    "",
                );
            },
            closeModal() {
                this.hideAddCollection = true;
            },
        },

    };

</script>
