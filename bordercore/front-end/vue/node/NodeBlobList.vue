<template>
    <div class="hover-reveal-target">
        <card title="" class="position-relative">
            <template #title-slot>
                <div class="card-title d-flex">
                    <div>
                        <font-awesome-icon icon="splotch" class="text-primary me-3" />
                        Blobs
                    </div>
                    <div class="ms-auto">
                        <add-button href="#" :click-handler="chooseBlob" class="hover-reveal-object button-add-container d-none" />
                    </div>
                </div>
            </template>

            <template #content>
                <hr class="filter-divider mt-0">
                <ul id="sort-container-tags" class="list-group list-group-flush interior-borders">
                    <draggable v-model="blobList" ghost-class="sortable-ghost" draggable=".draggable" @change="onChange">
                        <transition-group type="transition" class="w-100">
                            <li v-for="(blob, index) in blobList" v-cloak :key="blob.uuid" class="hover-target list-group-item list-group-item-secondary text-info draggable pe-0" :data-uuid="blob.uuid">
                                <div class="dropdown-height d-flex align-items-start">
                                    <div class="pe-2">
                                        <img :src="blob.cover_url" height="75" width="70">
                                    </div>

                                    <div>
                                        <a :href="blob.url">{{ blob.name }}</a>
                                        <div v-if="blob.note" v-show="!blob.noteIsEditable" class="node-note" @click="activateInEditMode(blob, index)">
                                            {{ blob.note }}
                                        </div>
                                        <span v-show="blob.noteIsEditable">
                                            <input ref="input" type="text" class="form-control form-control-sm" :value="blob.note" placeholder="" @blur="editNote(blob.uuid, $event.target.value)" @keydown.enter="editNote(blob.uuid, $event.target.value)">
                                        </span>
                                    </div>

                                    <drop-down-menu :show-on-hover="true">
                                        <div slot="dropdown">
                                            <a class="dropdown-item" href="#" @click.prevent="removeBlob(blob.uuid)">
                                                <font-awesome-icon icon="trash-alt" class="text-primary me-3" />Remove
                                            </a>
                                            <a v-if="blob.note" class="dropdown-item" href="#" @click.prevent="activateInEditMode(blob, index)">
                                                <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />Edit note
                                            </a>
                                            <a v-else class="dropdown-item" href="#" @click.prevent="addNote(blob.uuid, index)">
                                                <font-awesome-icon icon="plus" class="text-primary me-3" />Add note
                                            </a>
                                        </div>
                                    </drop-down-menu>
                                </div>
                            </li>
                            <div v-if="blobList.length == 0" v-cloak :key="1" class="text-muted">
                                No blobs
                            </div>
                        </transition-group>
                    </draggable>
                </ul>
            </template>
        </card>
    </div>
</template>

<script>

    export default {

        name: "NodeBlobList",
        props: {
            editBlobNoteUrl: {
                type: String,
                default: "",
            },
            getBlobListUrl: {
                type: String,
                default: "",
            },
            removeBlobUrl: {
                type: String,
                default: "",
            },
            sortBlobsUrl: {
                type: String,
                default: "",
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
            activateInEditMode(blob, index) {
                this.$set(this.blobList[index], "noteIsEditable", true);

                self = this;
                setTimeout( () => {
                    self.$refs.input[index].focus();
                }, 100);
            },
            addNote(blobUuid, index) {
                for (const blob of this.blobList) {
                    if (blob.uuid === blobUuid) {
                        blob.noteIsEditable = true;
                    }
                }

                this.$nextTick(() => {
                    this.$refs.input[index].focus();
                });
            },
            chooseBlob() {
                this.$parent.$parent.$refs.blobSelect.openModal();
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
                                "node_uuid": this.$store.state.nodeUuid,
                                "blob_uuid": blob.uuid,
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
            getBlobList() {
                doGet(
                    this,
                    this.getBlobListUrl,
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
            onChange(evt) {
                const blobUuid = evt.moved.element.uuid;

                // The backend expects the ordering to begin
                // with 1, not 0, so add 1.
                const newPosition = evt.moved.newIndex + 1;

                doPost(
                    this,
                    this.sortBlobsUrl,
                    {
                        "node_uuid": this.$store.state.nodeUuid,
                        "blob_uuid": blobUuid,
                        "new_position": newPosition,
                    },
                    () => {},
                    "",
                );
            },
            removeBlob(blobUuid) {
                doPost(
                    this,
                    this.removeBlobUrl,
                    {
                        "node_uuid": this.$store.state.nodeUuid,
                        "blob_uuid": blobUuid,
                    },
                    (response) => {
                        this.getBlobList();
                    },
                    "Blob removed",
                    "",
                );
            },
        },
    };

</script>
