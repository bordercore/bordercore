<template>
    <div class="hover-reveal-target" @mouseover="hover = true" @mouseleave="hover = false">
        <card title="" class="backdrop-filter node-color-1 position-relative">
            <template #title-slot>
                <div class="card-title d-flex">
                    <div class="text-truncate">
                        <font-awesome-icon icon="splotch" class="text-primary me-3" />
                        {{ collectionObjectList.name }}
                    </div>
                    <div class="text-secondary text-small text-nowrap ms-3">
                        {{ collectionObjectList.count }} <span>{{ getPluralized(collectionObjectList.count) }}</span>
                    </div>
                    <div class="dropdown-menu-container dropdown-menu-container-width ms-auto">
                        <drop-down-menu class="d-none hover-reveal-object" :show-on-hover="false">
                            <template #dropdown>
                                <li>
                                    <a v-if="collectionObjectList.collection_type === 'ad-hoc'" class="dropdown-item" href="#" @click.prevent="onAddObject()">
                                        <span>
                                            <font-awesome-icon icon="plus" class="text-primary me-3" />
                                        </span>
                                        Add Object
                                    </a>
                                </li>
                                <li>
                                    <a class="dropdown-item" href="#" @click.prevent="onEditCollection()">
                                        <span>
                                            <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />
                                        </span>
                                        Edit Collection
                                    </a>
                                </li>
                                <li>
                                    <a class="dropdown-item" href="#" @click.prevent="onDeleteCollection()">
                                        <span>
                                            <font-awesome-icon icon="times" class="text-primary me-3" />
                                        </span>
                                        <span v-if="collectionObjectList.collection_type === 'ad-hoc'">Delete</span>
                                        <span v-else>
                                            Remove
                                        </span>
                                        Collection
                                    </a>
                                </li>
                            </template>
                        </drop-down-menu>
                    </div>
                </div>
            </template>

            <template #content>
                <hr class="divider">
                <div v-if="collectionObjectList.display === 'individual'">
                    <img v-if="currentObjectIndex !== null && objectList.length > 0" :src="objectList[currentObjectIndex].cover_url_large" class="mw-100" @click="onClick()">
                    <span v-else class="text-muted">No objects</span>
                </div>
                <ul v-else id="sort-container-tags" class="list-group list-group-flush interior-borders">
                    <draggable v-model="limitedObjectList" draggable=".draggable" :component-data="{type:'transition-group'}" item-key="uuid" @change="onSort">
                        <template #item="{element}">
                            <li v-cloak :key="element.uuid" class="hover-target list-group-item list-group-item-secondary draggable pe-0" :data-uuid="element.uuid">
                                <div class="dropdown-height d-flex align-items-start">
                                    <div v-if="element.type === 'blob'" class="pe-2">
                                        <img :src="element.cover_url" height="75" width="70">
                                    </div>
                                    <div v-else class="pe-2" v-html="element.favicon_url" />

                                    <div>
                                        <a :href="element.url">{{ element.name }}</a>
                                        <Transition name="fade" mode="out-in" @after-enter="onAfterEnter">
                                            <div v-if="!element.noteIsEditable" class="node-object-note" @click="editNote(element)" v-html="getNote(element.note)" />
                                            <span v-else>
                                                <input ref="input" type="text" class="form-control form-control-sm" :value="element.note" placeholder="" @blur="updateNote(element, $event.target.value)" @keydown.enter="updateNote(element, $event.target.value)">
                                            </span>
                                        </Transition>
                                    </div>

                                    <drop-down-menu :show-on-hover="true">
                                        <template #dropdown>
                                            <li>
                                                <a class="dropdown-item" href="#" @click.prevent="removeObject(element.uuid)">
                                                    <font-awesome-icon icon="trash-alt" class="text-primary me-3" />Remove
                                                </a>
                                            </li>
                                            <li>
                                                <a class="dropdown-item" href="#" @click.prevent="editNote(element)">
                                                    <font-awesome-icon icon="pencil-alt" class="text-primary me-3" /><span v-if="element.note">Edit</span><span v-else>Add</span> Note
                                                </a>
                                            </li>
                                        </template>
                                    </drop-down-menu>
                                </div>
                            </li>
                        </template>
                    </draggable>
                    <div v-if="objectList.length == 0" v-cloak :key="1" class="text-muted">
                        No objects
                    </div>
                </ul>
            </template>
        </card>
    </div>
</template>

<script>

    import Card from "/front-end/vue/common/Card.vue";
    import draggable from "vuedraggable";
    import DropDownMenu from "/front-end/vue/common/DropDownMenu.vue";
    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

    export default {
        name: "CollectionObjectList",
        components: {
            Card,
            draggable,
            DropDownMenu,
            FontAwesomeIcon,
        },
        props: {
            nodeUuid: {
                type: String,
                default: "",
            },
            collectionObjectListInitial: {
                type: Object,
                default: function() {},
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
            deleteCollectionUrl: {
                type: String,
                default: "",
            },
        },
        data() {
            return {
                collectionObjectList: {},
                currentObjectIndex: null,
                hover: false,
                objectList: [],
                rotateInterval: null,
                show: false,
            };
        },
        computed: {
            limitedObjectList: {
                // We need to define a getter and setter since it needs to be
                // writable by the draggable component.
                get() {
                    return this.collectionObjectList.limit ? this.objectList.slice(0, this.collectionObjectList.limit) : this.objectList;
                },
                set(newValue) {
                    this.objectList = newValue;
                },
            },
        },
        mounted() {
            this.collectionObjectList = this.collectionObjectListInitial;
            this.getObjectList();

            const self = this;

            hotkeys("left,right", function(event, handler) {
                if (!self.hover) {
                    return;
                }
                switch (handler.key) {
                    case "left":
                        self.showPreviousObject();
                        break;
                    case "right":
                        self.showNextObject();
                        break;
                }
            });
        },
        methods: {
            editNote(object) {
                object.noteIsEditable = true;
            },
            getNote(note) {
                if (note) {
                    return markdown.render(note);
                }
            },
            onAfterEnter(evt) {
                const input = evt.querySelector("input");
                if (input) {
                    input.focus();
                }
            },
            onClick() {
                this.$emit("open-modal-note-image", this.objectList[this.currentObjectIndex].cover_url_large);
            },
            updateNote(object, note) {
                // If the note hasn't changed, abort
                if (object.note === note) {
                    object.noteIsEditable = false;
                    return;
                }

                doPost(
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
                    `${this.getObjectListUrl}?random_order=${this.collectionObjectList.random_order}`,
                    (response) => {
                        this.objectList = response.data.object_list;
                        // Let Vue know that each object's "noteIsEditable" property is reactive
                        for (const blob of this.objectList) {
                            blob.noteIsEditable = false;
                            // this.$set(blob, "noteIsEditable", false);
                        }
                        this.currentObjectIndex = 0;
                        if (this.collectionObjectList.rotate !== null && this.collectionObjectList.rotate !== -1) {
                            this.setTimer();
                        }
                    },
                    "Error getting object list",
                );
            },
            getPluralized: function(count) {
                return pluralize("object", count);
            },
            onAddObject() {
                this.$parent.$parent.$refs.objectSelectCollection.openModal(this.getObjectList, {"collectionUuid": this.uuid});
            },
            onEditCollection() {
                this.$emit("open-modal-collection-update", this.onUpdateCollection, this.collectionObjectList);
            },
            onUpdateCollection(collectionObjectList) {
                doPost(
                    this.updateCollectionUrl,
                    {
                        "collection_uuid": this.uuid,
                        "node_uuid": this.nodeUuid,
                        "name": collectionObjectList.name,
                        "display": collectionObjectList.display,
                        "random_order": collectionObjectList.random_order,
                        "rotate": collectionObjectList.rotate,
                        "limit": collectionObjectList.limit,
                    },
                    (response) => {
                        this.collectionObjectList.name = collectionObjectList.name;
                        this.collectionObjectList.display = collectionObjectList.display;
                        this.setTimer();
                    },
                    "Collection updated",
                );
            },
            onDeleteCollection() {
                doPost(
                    this.deleteCollectionUrl,
                    {
                        "node_uuid": this.nodeUuid,
                        "collection_uuid": this.uuid,
                        "collection_type": this.collectionObjectList.collection_type,
                    },
                    (response) => {
                        this.$emit("updateLayout", response.data.layout);
                    },
                    "Collection deleted",
                );
            },
            onSort(evt) {
                const uuid = evt.moved.element.uuid;

                // The backend expects the ordering to begin
                // with 1, not 0, so add 1.
                const newPosition = evt.moved.newIndex + 1;

                doPost(
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
            setTimer() {
                if (!this.collectionObjectList.rotate || this.collectionObjectList.rotate === -1) {
                    return;
                }
                clearInterval(this.rotateInterval);
                this.rotateInterval = setInterval( () => {
                    this.showNextObject();
                }, this.collectionObjectList.rotate * 1000 * 60);
            },
            showNextObject() {
                if (this.currentObjectIndex === this.objectList.length - 1) {
                    this.currentObjectIndex = 0;
                } else {
                    this.currentObjectIndex++;
                }
            },
            showPreviousObject() {
                if (this.currentObjectIndex === 0) {
                    this.currentObjectIndex = this.objectList.length - 1;
                } else {
                    this.currentObjectIndex--;
                }
            },
        },
    };

</script>
