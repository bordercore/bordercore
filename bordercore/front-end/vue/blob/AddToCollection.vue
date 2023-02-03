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
                        <div id="search-collections" :class="{'d-none': !hideAddCollection}" class="mb-0">
                            <select-value
                                ref="selectValue"
                                name="search"
                                place-holder="Search collections"
                                :search-url="searchUrl"
                                @select="select"
                            >
                                <template #option="props">
                                    <div :class="{'multiselect--disabled': props.option.contains_blob}" class="search-suggestion d-flex align-items-center" @click.stop="onClick(props.option)">
                                        <div>
                                            <img class="me-2" width="50" height="50" :src="props.option.cover_url">
                                        </div>
                                        <div class="me-1">
                                            {{ props.option.name }}
                                        </div>
                                        <div class="text-primary mx-1">
                                            <small>{{ props.option.num_blobs }} blobs</small>
                                        </div>
                                        <div v-if="props.option.contains_blob" class="text-warning ms-auto">
                                            Added
                                        </div>
                                    </div>
                                </template>
                            </select-value>
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

    import SelectValue from "../common/SelectValue.vue";

    export default {

        components: {
            SelectValue,
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
            addObjectUrl: {
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
                hideAddCollection: true,
            };
        },
        methods: {
            onClick(suggestion) {
                if (!suggestion.contains_blob) {
                    this.select(suggestion);
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
                    this.addObjectUrl,
                    {
                        "collection_uuid": collectionUuid,
                        "blob_uuid": this.blobUuid,
                    },
                    (response) => {
                        this.$emit("add-to-collection", collectionUuid);

                        const modal = Modal.getInstance(document.getElementById("modalAddToCollection"));
                        modal.hide();

                        this.$nextTick(() => {
                            this.$refs.selectValue.select = "";
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
                            this.$refs.selectValue.value = "";
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
