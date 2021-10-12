<template>
    <div>
        <div>
            <card title="Related Blobs">
                <template #top-right>
                    <span class="button-plus float-right" @click="chooseBlob()">
                        <font-awesome-icon icon="plus" />
                    </span>
                </template>

                <template #content>
                    <ul id="sort-container-tags" class="list-group list-group-flush">
                        <draggable v-model="blobList" ghost-class="sortable-ghost" draggable=".draggable" @change="onChange">
                            <transition-group type="transition" class="w-100">
                                <li v-for="(blob, index) in blobList" v-cloak :key="blob.uuid" v-b-hover="handleHover" class="list-group-item list-group-item-secondary text-info draggable px-0" :data-uuid="blob.uuid">
                                    <div class="d-flex">
                                        <div class="pr-2">
                                            <img :src="[[ blob.cover_url ]]" height="75" width="70">
                                        </div>

                                        <div>
                                            <a :href="blob.url">{{ blob.name }}</a>

                                            <div v-show="!blob.noteIsEditable" v-if="blob.note" class="node-note" @click="activateInEditMode(blob, index)">
                                                {{ blob.note }}
                                            </div>
                                            <span v-show="blob.noteIsEditable">
                                                <input id="add-blob-input" ref="input" type="text" class="form-control form-control-sm" :value="blob.note" placeholder="" autocomplete="off" @blur="editNote(blob.uuid, $event.target.value)" @keydown.enter="editNote(blob.uuid, $event.target.value)">
                                            </span>
                                        </div>

                                        <div class="dropdownmenu">
                                            <dropdown-menu v-model="show" transition="translate-fade-down" class="hidden">
                                                <font-awesome-icon icon="ellipsis-v" />
                                                <div slot="dropdown">
                                                    <a class="dropdown-item" href="#" @click="removeBlob(blob.uuid)">Remove</a>
                                                    <a v-if="!blob.note" class="dropdown-item" href="#" @click="addNote(blob.uuid)">Add note</a>
                                                    <a v-else class="dropdown-item" href="#" @click="activateInEditMode(blob, index)">Edit note</a>
                                                </div>
                                            </dropdown-menu>
                                        </div>
                                    </div>
                                </li>
                                <div v-cloak v-if="blobList.length == 0" :key="1" class="text-secondary">
                                    No blobs
                                </div>
                            </transition-group>
                        </draggable>
                    </ul>
                </template>
            </card>
        </div>

        <blob-search
            ref="blob"
            :search-blob-url="searchBlobUrl"
            @addBlob="addBlob"
        />
    </div>
</template>

<script>

    import BlobSearch from "../blob/BlobSearch.vue";

    export default {

        components: {
            BlobSearch,
        },
        props: {
            questionUuid: {
                default: "",
                type: String,
            },
            getBlobListUrl: {
                default: "url",
                type: String,
            },
            sortBlobListUrl: {
                default: "url",
                type: String,
            },
            addBlobUrl: {
                default: "url",
                type: String,
            },
            removeBlobUrl: {
                default: "url",
                type: String,
            },
            editBlobNoteUrl: {
                default: "url",
                type: String,
            },
            searchBlobUrl: {
                default: "url",
                type: String,
            },
        },
        data() {
            return {
                blobList: [],
                show: false,
            };
        },
        mounted() {
            this.getBlobList();
        },
        methods: {
            getBlobList() {
                doGet(
                    this,
                    this.getBlobListUrl.replace(/00000000-0000-0000-0000-000000000000/, this.questionUuid),
                    (response) => {
                        this.blobList = response.data.blob_list;

                        // Let Vue know that each blob's "noteIsEditable" property is reactive
                        for (const blob of this.blobList) {
                            this.$set(blob, "noteIsEditable", false);
                        }
                    },
                    "Error getting blob list",
                );
            },
            chooseBlob() {
                $("#modalAddBlob").modal("show");
                setTimeout( () => {
                    this.$refs.blob.$refs.simpleSuggest.$refs.suggestComponent.input.focus();
                }, 500);
            },
            onChange(evt) {
                const blobUuid = evt.moved.element.uuid;

                // The backend expects the ordering to begin
                // with 1, not 0, so add 1.
                const newPosition = evt.moved.newIndex + 1;

                doPost(
                    this,
                    this.sortBlobListUrl,
                    {
                        "question_uuid": this.questionUuid,
                        "blob_uuid": blobUuid,
                        "new_position": newPosition,
                    },
                    () => {},
                    "",
                    "",
                );
            },
            activateInEditMode(blob, index) {
                this.$set(this.blobList[index], "noteIsEditable", true);

                self = this;
                setTimeout( () => {
                    self.$refs.input[index].focus();
                }, 100);
            },
            addNote(blobUuid) {
                for (const blob of this.blobList) {
                    if (blob.uuid == blobUuid) {
                        blob.noteIsEditable = true;
                    }
                }

                this.$nextTick(() => {
                    this.$refs.input[0].focus();
                });
            },
            addBlob(blobUuid) {
                doPost(
                    this,
                    this.addBlobUrl,
                    {
                        "question_uuid": this.questionUuid,
                        "blob_uuid": blobUuid,
                    },
                    (response) => {
                        this.getBlobList();
                    },
                    "",
                    "",
                );
            },
            handleHover(hovered, evt) {
                if (hovered == true) {
                    evt.currentTarget.querySelector(".dropdown").classList.remove("hidden");
                } else {
                    evt.currentTarget.querySelector(".dropdown").classList.add("hidden");
                };
            },
            removeBlob(blobUuid) {
                doPost(
                    this,
                    this.removeBlobUrl,
                    {
                        "question_uuid": this.questionUuid,
                        "blob_uuid": blobUuid,
                    },
                    (response) => {
                        this.getBlobList();
                    },
                    "Blob removed",
                    "",
                );
            },
            editNote(blobUuid, note) {
                if (this.editingNote) {
                    return;
                }
                this.editingNote = true;

                for (const blob of this.blobList) {
                    if (blob.uuid == blobUuid) {
                        // If the note hasn't changed, abort
                        if (note == blob.note) {
                            blob.noteIsEditable = false;
                            this.editingNote = false;
                            return;
                        }

                        doPost(
                            this,
                            this.editBlobNoteUrl,
                            {
                                "question_uuid": this.questionUuid,
                                "blob_uuid": blobUuid,
                                "note": note,
                            },
                            (response) => {
                                this.getBlobList();
                            },
                            "",
                            "",
                        );

                        this.editingNote = false;
                    }
                }
            },
        },
    };

</script>
