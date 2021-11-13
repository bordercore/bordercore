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
                        <form @submit.prevent>
                            <div class="form-group">
                                <simple-suggest
                                    ref="simpleSuggest"
                                    class="w-100"
                                    display-attribute="name"
                                    value-attribute="uuid"
                                    :search-url="searchUrl"
                                />
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
            };
        },
        methods: {
            boldenSuggestion(scope) {
                if (!scope) return scope;

                const {suggestion} = scope;

                const result = this.$refs.simpleSuggest.$refs.suggestComponent.displayProperty(suggestion);

                return result + " - <span class='text-primary'>" + suggestion.num_blobs + " blobs</span>";
            },
            select(selection) {
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
                            this.$refs.simpleSuggest.$refs.suggestComponent.$el.querySelector("input").blur();
                            this.$refs.simpleSuggest.$refs.suggestComponent.setText("");
                        });
                    },
                    "",
                    "",
                );
            },
        },

    };

</script>
