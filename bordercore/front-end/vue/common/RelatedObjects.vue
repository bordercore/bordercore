<template>
    <div v-if="objectList.length > 0 || showEmptyList" class="hover-reveal-target mb-3">
        <transition :name="transitionName">
            <card class="position-relative h-100 backdrop-filter z-index-positive">
                <template #title-slot>
                    <div class="d-flex">
                        <div class="card-title d-flex">
                            <font-awesome-icon icon="bookmark" class="text-primary me-3 mt-1" />
                            {{ title }}
                        </div>
                        <div class="dropdown-menu-container ms-auto">
                            <drop-down-menu class="d-none hover-reveal-object" :show-on-hover="false">
                                <div slot="dropdown">
                                    <li>
                                        <a class="dropdown-item" href="#" @click.prevent="openModal">
                                            <span>
                                                <font-awesome-icon icon="plus" class="text-primary me-3" />
                                            </span>
                                            Add Object
                                        </a>
                                    </li>
                                </div>
                            </drop-down-menu>
                        </div>
                    </div>
                </template>

                <template #content>
                    <hr class="divider">
                    <ul class="list-group list-group-flush interior-borders">
                        <li v-for="object in objectList" v-cloak :key="object.uuid" class="hover-target list-group-item list-group-item-secondary px-0" :data-uuid="object.uuid">
                            <div class="dropdown-height d-flex align-items-start">
                                <div v-if="object.type === 'bookmark'" class="pe-2" v-html="object.favicon_url" />
                                <div v-else-if="object.type === 'blob'" class="pe-2">
                                    <img :src="[[ object.cover_url ]]" height="75" width="70">
                                </div>
                                <div>
                                    <a :href="object.url">{{ object.name }}</a>

                                    <div v-show="!object.noteIsEditable" v-if="object.note" class="node-object-note" @click="onSetNoteIsEditable(object)">
                                        {{ object.note }}
                                    </div>
                                    <span v-show="object.noteIsEditable">
                                        <input id="add-object-input" ref="input" type="text" class="form-control form-control-sm" :value="object.note" placeholder="" autocomplete="off" @blur="onEditNote(object, $event.target.value)" @keydown.enter="onEditNote(object, $event.target.value)">
                                    </span>
                                </div>
                                <drop-down-menu ref="editNoteMenu" :show-on-hover="true">
                                    <div slot="dropdown">
                                        <li>
                                            <a class="dropdown-item" href="#" @click.prevent="onRemoveObject(object.bc_object_uuid, object.uuid)">
                                                <font-awesome-icon icon="trash-alt" class="text-primary me-3" />Remove
                                            </a>
                                            <a class="dropdown-item" :href="object.edit_url">
                                                <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />Edit <span>{{ object.type }}</span>
                                            </a>
                                            <a class="dropdown-item" href="#" @click.prevent="onSetNoteIsEditable(object)">
                                                <font-awesome-icon :icon="object.note ? 'pencil-alt' : 'plus'" class="text-primary me-3" />{{ object.note ? 'Edit' : 'Add' }} note
                                            </a>
                                        </li>
                                    </div>
                                </drop-down-menu>
                            </div>
                        </li>
                        <div v-cloak v-if="objectList.length == 0" :key="1" class="text-muted">
                            No objects
                        </div>
                    </ul>
                </template>
            </card>
        </transition>
    </div>
</template>

<script>

    export default {

        props: {
            objectUuid: {
                default: "",
                type: String,
            },
            baseModelName: {
                default: "",
                type: String,
            },
            title: {
                default: "Related Objects",
                type: String,
            },
            relatedObjectsUrl: {
                default: "",
                type: String,
            },
            addObjectUrl: {
                default: "",
                type: String,
            },
            removeObjectUrl: {
                default: "",
                type: String,
            },
            editObjectNoteUrl: {
                default: "url",
                type: String,
            },
            transitionName: {
                default: "fade",
                type: String,
            },
            showEmptyList: {
                default: true,
                type: Boolean,
            },
            newQuestion: {
                default: false,
                type: Boolean,
            },
        },
        data() {
            return {
                mode: "search",
                name: "",
                bookmarkList: [],
                objectList: [],
            };
        },
        mounted() {
            if (!this.newQuestion) {
                this.getRelatedObjects();
            }
        },
        methods: {
            getRelatedObjects() {
                doGet(
                    this,
                    this.relatedObjectsUrl.replace(/00000000-0000-0000-0000-000000000000/, this.objectUuid),
                    (response) => {
                        this.objectList = response.data.related_objects;

                        // Let Vue know that each objects's "noteIsEditable" property is reactive
                        for (const object of this.objectList) {
                            this.$set(object, "noteIsEditable", false);
                        }
                    },
                    "Error getting object list",
                );
            },
            onRemoveObject(bcObjectUuid, uuid) {
                if (this.newQuestion) {
                    const newObjectList = this.objectList.filter((x) => x.uuid !== uuid);
                    this.objectList = newObjectList;
                    return;
                }

                doPost(
                    this,
                    this.removeObjectUrl,
                    {
                        "question_uuid": this.objectUuid,
                        "bc_object_uuid": bcObjectUuid,
                    },
                    (response) => {
                        this.getRelatedObjects();
                    },
                    "Object removed",
                    "",
                );
            },
            openModal() {
                this.$parent.$refs.objectSelect.openModal();
            },
            addObject(bcObject) {
                if (this.newQuestion) {
                    this.objectList.push(bcObject);
                    // Let Vue know that the object's "noteIsEditable" property is reactive
                    this.$set(bcObject, "noteIsEditable", false);
                    return;
                }

                doPost(
                    this,
                    this.addObjectUrl,
                    {
                        "question_uuid": this.objectUuid,
                        "object_uuid": bcObject.uuid,
                    },
                    (response) => {
                        this.getRelatedObjects();
                    },
                    "Object added",
                    "",
                );
            },
            onSetNoteIsEditable(bcObject) {
                bcObject.noteIsEditable = true;

                this.$nextTick(() => {
                    this.$refs.input[0].focus();
                });
            },
            onEditNote(bcObject, note) {
                if (this.editingNote) {
                    return;
                }
                this.editingNote = true;

                // If the note hasn't changed, abort
                if (note == bcObject.note) {
                    bcObject.noteIsEditable = false;
                    this.editingNote = false;
                    return;
                }

                if (this.newQuestion) {
                    bcObject.note = note;
                    bcObject.noteIsEditable = false;
                } else {
                    doPost(
                        this,
                        this.editObjectNoteUrl,
                        {
                            "bc_object_uuid": bcObject.bc_object_uuid,
                            "note": note,
                        },
                        (response) => {
                            this.getRelatedObjects();
                        },
                        "",
                        "",
                    );
                }
                this.editingNote = false;
            },
        },
    };

</script>
