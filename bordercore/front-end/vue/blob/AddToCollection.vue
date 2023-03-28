<template>
    <div id="modalAddToCollection" class="modal fade" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        Add blob to collection
                    </h4>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" />
                </div>
                <div class="modal-body">
                    <div class="d-flex flex-column">
                        <div v-if="!showAddCollection" id="search-collections" class="mb-0">
                            <select-value
                                ref="selectValue"
                                name="search"
                                place-holder="Search collections"
                                :search-url="searchUrl"
                                @select="handleCollectionSelect"
                            >
                                <template #option="props">
                                    <div :class="{'multiselect--disabled': props.option.contains_blob}" class="search-suggestion d-flex align-items-center" @click.stop="handleCollectionSelect(props.option)">
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
                        <div v-if="showAddCollection">
                            <input id="collectionName" class="form-control mb-3" type="text" name="collection-name" placeholder="Collection name" autocomplete="off">
                            <div class="mt-3">
                                <div class="form-check">
                                    <input id="isFavorite" class="form-check-input mt-2" type="radio">
                                    <label class="form-check-label d-flex" for="isFavorite">
                                        Private
                                    </label>
                                </div>
                            </div>
                            <button class="btn btn-primary d-flex ms-auto" @click="handleCollectionCreate">
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
        emits: ["add-to-collection"],
        setup(props, ctx) {
            const showAddCollection = ref(false);

            const selectValue = ref();

            function addBlobToCollection(collectionUuid) {
                doPost(
                    props.addObjectUrl,
                    {
                        "collection_uuid": collectionUuid,
                        "blob_uuid": props.blobUuid,
                    },
                    (response) => {
                        ctx.emit("add-to-collection", collectionUuid);

                        const modal = Modal.getInstance(document.getElementById("modalAddToCollection"));
                        modal.hide();

                        nextTick(() => {
                            selectValue.value.clearOptions();
                        });
                    },
                    "",
                    "",
                );
            };

            function handleCollectionCreate() {
                const isFavorite = document.querySelector("#isFavorite").value;
                const name = document.querySelector("#collectionName").value;

                doPost(
                    props.addCollectionUrl,
                    {
                        "is_favorite": isFavorite,
                        "name": name,
                    },
                    (response) => {
                        const collectionUuid = response.data.uuid;

                        addBlobToCollection(collectionUuid);

                        ctx.emit("add-to-collection", collectionUuid);

                        const modal = Modal.getInstance(document.getElementById("modalAddToCollection"));
                        modal.hide();
                        showAddCollection.value = false;

                        nextTick(() => {
                            selectValue.value.select = "";
                        });
                    },
                    "",
                    "",
                );
            };

            function handleCollectionSelect(selection) {
                if (!selection.contains_blob) {
                    addBlobToCollection(selection.uuid);
                }
            };

            function showCreateNewCollection() {
                showAddCollection.value = true;
                setTimeout( () => {
                    document.querySelector("#collectionName").focus();
                }, 100);
            };

            return {
                handleCollectionCreate,
                handleCollectionSelect,
                showAddCollection,
                selectValue,
                showCreateNewCollection,
            };
        },
    };

</script>
