<template>
    <div>
        <div class="hover-reveal-target">
            <card class="position-relative backdrop-filter">
                <template #title-slot>
                    <div class="d-flex">
                        <div class="card-title d-flex">
                            <font-awesome-icon icon="splotch" class="text-primary me-3 mt-1" />
                            Blobs
                        </div>
                        <div class="hover-reveal-object button-add-container d-none">
                            <add-button href="#" :click-handler="chooseBlob" />
                        </div>
                    </div>
                </template>

                <template #content>
                    <hr class="filter-divider mt-0">
                    <ul id="sort-container-tags" class="list-group list-group-flush">
                        <draggable v-model="blobList" ghost-class="sortable-ghost" draggable=".draggable" @change="onSort">
                            <transition-group type="transition" class="w-100">
                                <li v-for="(blob, index) in blobList" v-cloak :key="blob.uuid" class="hover-target text-info draggable d-flex align-items-center p-2" :data-uuid="blob.uuid">
                                    <div class="d-flex align-items-center w-100">
                                        <div class="align-self-start pe-2">
                                            <img :src="[[ blob.cover_url ]]" height="75" width="70">
                                        </div>

                                        <div class="d-flex flex-column justify-content-center w-100">
                                            <a :href="blob.url">{{ blob.name }}</a>

                                            <div v-show="!blob.noteIsEditable" v-if="blob.note" class="node-object-note" @click="activateInEditMode(blob, index)">
                                                {{ blob.note }}
                                            </div>
                                            <span v-show="blob.noteIsEditable">
                                                <input id="add-blob-input" ref="input" type="text" class="form-control form-control-sm" :value="blob.note" placeholder="" autocomplete="off" @blur="editNote(blob.uuid, $event.target.value)" @keydown.enter="editNote(blob.uuid, $event.target.value)">
                                            </span>
                                        </div>

                                        <drop-down-menu ref="editNoteMenu" :show-on-hover="true">
                                            <div slot="dropdown">
                                                <li>
                                                    <a class="dropdown-item" href="#" @click.prevent="removeBlob(blob.uuid)"><font-awesome-icon icon="trash-alt" class="text-primary me-3" />Remove</a>
                                                    <a v-if="!blob.note" class="dropdown-item" href="#" @click.prevent="addNote(blob.uuid)">
                                                        <font-awesome-icon icon="plus" class="text-primary me-3" />Add note
                                                    </a>
                                                    <a v-else class="dropdown-item" href="#" @click.prevent="activateInEditMode(blob, index)">
                                                        <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />Edit note
                                                    </a>
                                                </li>
                                            </div>
                                        </drop-down-menu>
                                    </div>
                                </li>
                                <div v-cloak v-if="blobList.length == 0" :key="1" class="text-muted">
                                    No blobs
                                </div>
                            </transition-group>
                        </draggable>
                    </ul>
                </template>
            </card>
        </div>

        <blob-select
            ref="blobSelect"
            :search-blob-url="searchBlobUrl"
            :recent-blobs-url="recentBlobsUrl"
            @select-blob="selectBlob"
        />
    </div>
</template>

<script>

    import BlobSelect from "../blob/BlobSelect.vue";

    export default {

        components: {
            BlobSelect,
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
            recentBlobsUrl: {
                default: "url",
                type: String,
            },
            newQuestion: {
                default: false,
                type: Boolean,
            },
        },
        data() {
            return {
                blobList: [],
                show: false,
            };
        },
        mounted() {
            if (!this.newQuestion) {
                this.getBlobList();
            }
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
                this.$refs.blobSelect.openModal();
            },
            onSort(evt) {
                const blobUuid = evt.moved.element.uuid;

                // The backend expects the ordering to begin
                // with 1, not 0, so add 1.
                const newPosition = evt.moved.newIndex + 1;

                if (this.newQuestion) {
                    return;
                }

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
            selectBlob(blob) {
                if (this.newQuestion) {
                    this.blobList.push(blob);
                    // Let Vue know that the blob's "noteIsEditable" property is reactive
                    this.$set(blob, "noteIsEditable", false);
                    return;
                }

                doPost(
                    this,
                    this.addBlobUrl,
                    {
                        "question_uuid": this.questionUuid,
                        "blob_uuid": blob.uuid,
                    },
                    (response) => {
                        this.getBlobList();
                        this.$refs.blobSelect.$refs.simpleSuggest.$refs.suggestComponent.selected = null;
                    },
                    "",
                    "",
                );
            },
            removeBlob(blobUuid) {
                if (this.newQuestion) {
                    const newBlobList = this.blobList.filter((x) => x.uuid !== blobUuid);
                    this.blobList = newBlobList;
                    return;
                }

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

                        if (this.newQuestion) {
                            blob.note = note;
                            blob.noteIsEditable = false;
                        } else {
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
                        }
                        this.editingNote = false;
                    }
                }
            },
        },
    };

</script>
