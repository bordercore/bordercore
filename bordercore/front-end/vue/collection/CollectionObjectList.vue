<template>
    <div class="hover-reveal-target">
        <div id="modalUpdate" class="modal fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h4 id="myModalLabel" class="modal-title">
                            Update Collection
                        </h4>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" />
                    </div>
                    <div class="modal-body">
                        <div class=" row mb-3">
                            <label class="col-lg-3 col-form-label" for="inputTitle">Name</label>
                            <div class="col-lg-9">
                                <input :id="`id_name_${uuid}`" type="text" name="name" :value="name" class="form-control" autocomplete="off" maxlength="200" required>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <input id="btn-action" class="btn btn-primary" type="button" value="Update" @click="onUpdateCollection">
                    </div>
                </div>
            </div>
        </div>
        <card title="" class="position-relative">
            <template #title-slot>
                <div class="card-title d-flex">
                    <div>
                        <font-awesome-icon icon="splotch" class="text-primary me-3" />
                        {{ name }}
                    </div>
                    <drop-down-menu :show-on-hover="false">
                        <div slot="dropdown">
                            <a class="dropdown-item" href="#" @click.prevent="onAddBlob()">
                                <font-awesome-icon icon="plus" class="text-primary me-3" />
                                Add Blob
                            </a>
                            <a class="dropdown-item" href="#" @click.prevent="onAddBookmark()">
                                <font-awesome-icon icon="plus" class="text-primary me-3" />
                                Add Bookmark
                            </a>
                            <a class="dropdown-item" href="#" @click.prevent="onEditCollection()">
                                <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />
                                Edit Collection
                            </a>
                            <a class="dropdown-item" href="#" @click.prevent="onDeleteCollection()">
                                <font-awesome-icon icon="times" class="text-primary me-3" />
                                Delete Collection
                            </a>
                        </div>
                    </drop-down-menu>
                </div>
            </template>

            <template #content>
                <hr class="filter-divider mt-0">
                <ul id="sort-container-tags" class="list-group list-group-flush interior-borders">
                    <draggable v-model="objectList" ghost-class="sortable-ghost" draggable=".draggable" @change="onSort">
                        <transition-group type="transition" class="w-100">
                            <li v-for="(object, index) in objectList" v-cloak :key="object.uuid" class="hover-target list-group-item list-group-item-secondary text-info draggable pe-0" :data-uuid="object.uuid">
                                <div class="dropdown-height d-flex align-items-start">
                                    <div class="pe-2">
                                        <img :src="object.cover_url" height="75" width="70">
                                    </div>

                                    <div>
                                        <a :href="object.url">{{ object.name }}</a>
                                        <div v-if="object.note" v-show="!object.noteIsEditable" class="node-note" @click="editNote(object, index)">
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
                                            <a v-if="object.note" class="dropdown-item" href="#" @click.prevent="editNote(object, index)">
                                                <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />Edit note
                                            </a>
                                            <a v-else class="dropdown-item" href="#" @click.prevent="editNote(object, index)">
                                                <font-awesome-icon icon="plus" class="text-primary me-3" />Add note
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
            nodeUuid: {
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
                allowMounting: true,
            };
        },
        mounted() {
            console.log(`allow mounting: ${this.allowMounting}`);
            if (!this.allowMounting) {
                console.log("don't allow mounting");
                return;
            }
            console.log("mount!");
            this.allowMounting = false;
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
                this.$parent.$parent.$refs.blobSelect.openModal(this.uuid, this.getObjectList);
            },
            onAddBookmark() {
                console.log("add bookmark");
            },
            onEditCollection() {
                const modal = new Modal("#modalUpdate");
                modal.show();
            },
            onUpdateCollection() {
                const name = document.getElementById(`id_name_${this.uuid}`).value;
                doPut(
                    this,
                    this.updateCollectionUrl.replace(/00000000-0000-0000-0000-000000000000/, this.uuid),
                    {
                        "name": name,
                    },
                    (response) => {
                        this.name = name;
                        const modal = Modal.getInstance(document.getElementById("modalUpdate"));
                        modal.hide();
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
