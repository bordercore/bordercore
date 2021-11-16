<template>
    <div id="modalAddToCollection" class="modal fade" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        Add blob to collection
                    </h4>
                    <button type="button" class="close" data-dismiss="modal">
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="d-flex flex-column">
                        <div class="search-with-doctypes form-group">
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
                                placeholder="Name"
                                :styles="autoCompleteStyle"
                                autocomplete="off"
                                :autofocus="false"
                                @select="select"
                            >
                                <div slot="suggestion-item" slot-scope="{ suggestion }">
                                    <div :class="{'suggestion-item-disabled': suggestion.contains_blob}" class="top-search-suggestion d-flex align-items-center" @click.stop="onClick(suggestion)">
                                        <div>
                                            <img class="mr-2" width="50" height="50" :src="suggestion.cover_url">
                                        </div>
                                        <div class="mr-1">
                                            {{ displayProperty(suggestion) }}
                                        </div>
                                        <div class="text-primary mx-1">
                                            <small>{{ suggestion.num_blobs }} blobs</small>
                                        </div>
                                        <div v-if="suggestion.contains_blob" class="text-warning ml-auto">
                                            Added
                                        </div>
                                    </div>
                                </div>
                            </vue-simple-suggest>
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
            collectionMutateUrl: {
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
                doPost(
                    this,
                    this.collectionMutateUrl,
                    {
                        "blob_uuid": this.blobUuid,
                        "collection_uuid": selection.uuid,
                        "mutation": "add",
                    },
                    (response) => {
                        this.$emit("add-to-collection", selection.uuid);

                        $("#modalAddToCollection").modal("hide");

                        this.$nextTick(() => {
                            this.$refs.suggestComponent.$el.querySelector("input").blur();
                            this.$refs.suggestComponent.setText("");
                        });
                    },
                    "",
                    "",
                );
            },
        },

    };

</script>
