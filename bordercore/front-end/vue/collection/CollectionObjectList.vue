<template>
    <div class="hover-reveal-target">
        <card title="" class="backdrop-filter position-relative">
            <template #title-slot>
                <div class="card-title d-flex">
                    <div>
                        <font-awesome-icon icon="splotch" class="text-primary me-3" />
                        {{ name }}
                    </div>
                    <div class="dropdown-menu-container ms-auto">
                        <drop-down-menu class="d-none hover-reveal-object" :show-on-hover="false">
                            <div slot="dropdown">
                                <a class="dropdown-item" href="#" @click.prevent="onAddBlob()">
                                    <span>
                                        <font-awesome-icon icon="plus" class="text-primary me-3" />
                                    </span>
                                    Add Blob
                                </a>
                                <a class="dropdown-item" href="#" @click.prevent="onAddBookmark()">
                                    <span>
                                        <font-awesome-icon icon="plus" class="text-primary me-3" />
                                    </span>
                                    Add Bookmark
                                </a>
                                <a class="dropdown-item" href="#" @click.prevent="onEditCollection()">
                                    <span>
                                        <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />
                                    </span>
                                    Edit Collection
                                </a>
                                <a class="dropdown-item" href="#" @click.prevent="onDeleteCollection()">
                                    <span>
                                        <font-awesome-icon icon="times" class="text-primary me-3" />
                                    </span>
                                    Delete Collection
                                </a>
                            </div>
                        </drop-down-menu>
                    </div>
                </div>
            </template>

            <template #content>
                <hr class="filter-divider mt-0">
                <ul id="sort-container-tags" class="list-group list-group-flush interior-borders">
                    <draggable v-model="objectList" ghost-class="sortable-ghost" draggable=".draggable" @change="onSort">
                        <transition-group type="transition" class="w-100">
                            <li v-for="(object, index) in objectList" v-cloak :key="object.uuid" class="hover-target list-group-item list-group-item-secondary text-info draggable pe-0" :data-uuid="object.uuid">
                                <div class="dropdown-height d-flex align-items-start">
                                    <div v-if="object.type === 'blob'" class="pe-2">
                                        <img :src="object.cover_url" height="75" width="70">
                                    </div>
                                    <div v-else class="pe-2" v-html="object.favicon_url" />

                                    <div>
                                        <a :href="object.url">{{ object.name }}</a>
                                        <div v-if="object.note" v-show="!object.noteIsEditable" class="node-object-note" @click="editNote(object, index)">
                                            {{ object.note }}
                                        </div>
                                        <span v-show="object.noteIsEditable">
                                            <input ref="input" type="text" class="form-control form-control-sm" :value="object.note" placeholder="" @blur="updateNote(object, $event.target.value)" @keydown.enter="updateNote(object, $event.target.value)">
                                        </span>
                                    </div>

                                    <drop-down-menu :show-on-hover="true">
                                        <div slot="dropdown">
                                            <a class="dropdown-item" href="#" @click.prevent="removeObject(object.uuid)">
                                                <font-awesome-icon icon="trash-alt" class="text-primary me-3" />Remove
                                            </a>
                                            <a class="dropdown-item" href="#" @click.prevent="editNote(object, index)">
                                                <font-awesome-icon icon="pencil-alt" class="text-primary me-3" /><span v-if="object.note">Edit</span><span v-else>Add</span> Note
                                            </a>
                                        </div>
                                    </drop-down-menu>
                                </div>
                            </li>
                            <div v-if="objectList.length == 0" v-cloak :key="1" class="text-muted">
                                No objects
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

        name: "CollectionObjectList",
        props: {
            initialName: {
                type: String,
                default: "",
            },
            uuid: {
                type: String,
                default: "",
            },
            updateCollectionUrl: {
                type: String,
                default: "",
            },
            getObjectListUrl: {
                type: String,
                default: "",
            },
            updateObjectNoteUrl: {
                type: String,
                default: "",
            },
            removeObjectUrl: {
                type: String,
                default: "",
            },
            sortObjectsUrl: {
                type: String,
                default: "",
            },
        },
        data() {
            return {
                objectList: [],
                show: false,
                name: null,
            };
        },
        mounted() {
            this.name = this.initialName;
            this.getObjectList();
        },
        methods: {
            editNote(object, index) {
                object.noteIsEditable = true;
                this.$nextTick(() => {
                    this.$refs.input[index].focus();
                });
            },
            updateNote(object, note) {
                // If the note hasn't changed, abort
                if (object.note === note) {
                    object.noteIsEditable = false;
                    return;
                }

                doPost(
                    this,
                    this.updateObjectNoteUrl,
                    {
                        "collection_uuid": this.uuid,
                        "object_uuid": object.uuid,
                        "note": note,
                    },
                    (response) => {
                        this.getObjectList();
                    },
                    "",
                    "",
                );
            },
            getObjectList() {
                doGet(
                    this,
                    this.getObjectListUrl,
                    (response) => {
                        this.objectList = response.data.object_list;
                        // Let Vue know that each object's "noteIsEditable" property is reactive
                        for (const blob of this.objectList) {
                            this.$set(blob, "noteIsEditable", false);
                        }
                    },
                    "Error getting object list",
                );
            },
            onAddBlob() {
                this.$parent.$parent.$refs.objectSelectCollection.openModal(["blob", "book", "document", "note"], this.getObjectList, {"collectionUuid": this.uuid});
            },
            onAddBookmark() {
                this.$parent.$parent.$refs.objectSelectCollection.openModal(["bookmark"], this.getObjectList, {"collectionUuid": this.uuid});
            },
            onEditCollection() {
                this.$emit("open-modal-collection-update", this.onUpdateCollection, {name: this.name});
            },
            onUpdateCollection() {
                const name = document.getElementById("id_name_collection").value;
                doPut(
                    this,
                    this.updateCollectionUrl.replace(/00000000-0000-0000-0000-000000000000/, this.uuid),
                    {
                        "name": name,
                        "is_private": true,
                    },
                    (response) => {
                        this.name = name;
                    },
                    "Collection updated",
                );
            },
            onDeleteCollection() {
                this.$emit("delete-collection", this.uuid);
            },
            onSort(evt) {
                const uuid = evt.moved.element.uuid;

                // The backend expects the ordering to begin
                // with 1, not 0, so add 1.
                const newPosition = evt.moved.newIndex + 1;

                doPost(
                    this,
                    this.sortObjectsUrl,
                    {
                        "collection_uuid": this.uuid,
                        "object_uuid": uuid,
                        "new_position": newPosition,
                    },
                    () => {},
                    "",
                );
            },
            removeObject(objectUuid) {
                doPost(
                    this,
                    this.removeObjectUrl,
                    {
                        "collection_uuid": this.uuid,
                        "object_uuid": objectUuid,
                    },
                    (response) => {
                        this.getObjectList();
                    },
                    "Object removed",
                    "",
                );
            },
        },
    };

</script>
