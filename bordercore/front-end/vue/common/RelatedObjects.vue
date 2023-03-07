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
                                <template #dropdown>
                                    <li>
                                        <a class="dropdown-item" href="#" @click.prevent="openObjectSelectModal">
                                            <span>
                                                <font-awesome-icon icon="plus" class="text-primary me-3" />
                                            </span>
                                            Add Object
                                        </a>
                                    </li>
                                </template>
                            </drop-down-menu>
                        </div>
                    </div>
                </template>

                <template #content>
                    <hr class="divider">
                    <ul class="list-group list-group-flush interior-borders">
                        <li v-for="(object, index) in objectList" v-cloak :key="object.uuid" class="hover-target list-group-item list-group-item-secondary px-0" :data-uuid="object.uuid">
                            <div class="dropdown-height d-flex align-items-start">
                                <div v-if="object.type === 'bookmark'" class="pe-2" v-html="object.favicon_url" />
                                <div v-else-if="object.type === 'blob'" class="pe-2">
                                    <img :src="[[ object.cover_url ]]" height="75" width="70">
                                </div>
                                <div>
                                    <a :href="object.url">{{ object.name }}</a>

                                    <div v-show="!object.noteIsEditable" v-if="object.note" class="node-object-note" @click="handleSetNoteIsEditable(object, index)">
                                        {{ object.note }}
                                    </div>
                                    <span v-show="object.noteIsEditable">
                                        <input ref="input" type="text" class="form-control form-control-sm" :value="object.note" placeholder="" autocomplete="off" @blur="handleEditNote(object, $event.target.value)" @keydown.enter="handleEditNote(object, $event.target.value)">
                                    </span>
                                </div>
                                <drop-down-menu ref="editNoteMenu" :show-on-hover="true">
                                    <template #dropdown>
                                        <li>
                                            <a class="dropdown-item" href="#" @click.prevent="handleRemoveObject(object.bc_object_uuid, object.uuid)">
                                                <font-awesome-icon icon="trash-alt" class="text-primary me-3" />Remove
                                            </a>
                                            <a class="dropdown-item" :href="object.edit_url">
                                                <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />Edit <span>{{ object.type }}</span>
                                            </a>
                                            <a class="dropdown-item" href="#" @click.prevent="handleSetNoteIsEditable(object, index)">
                                                <font-awesome-icon :icon="object.note ? 'pencil-alt' : 'plus'" class="text-primary me-3" />{{ object.note ? 'Edit' : 'Add' }} note
                                            </a>
                                        </li>
                                    </template>
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

    import Card from "/front-end/vue/common/Card.vue";
    import DropDownMenu from "/front-end/vue/common/DropDownMenu.vue";
    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

    export default {
        components: {
            Card,
            DropDownMenu,
            FontAwesomeIcon,
        },
        props: {
            objectUuid: {
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
        emits: ["open-object-select-modal"],
        setup(props, ctx) {
            const input = ref(null);
            const objectList = ref([]);

            let isEditingNote = false;

            function addObject(bcObject) {
                if (props.newQuestion) {
                    objectList.value.push(bcObject);
                    return;
                }

                doPost(
                    props.addObjectUrl,
                    {
                        "question_uuid": props.objectUuid,
                        "object_uuid": bcObject.uuid,
                    },
                    (response) => {
                        getRelatedObjects();
                    },
                    "Object added",
                    "",
                );
            };

            function getRelatedObjects() {
                doGet(
                    props.relatedObjectsUrl.replace(/00000000-0000-0000-0000-000000000000/, props.objectUuid),
                    (response) => {
                        objectList.value = response.data.related_objects;
                    },
                    "Error getting object list",
                );
            };

            function handleEditNote(bcObject, note) {
                if (isEditingNote) {
                    return;
                }
                isEditingNote = true;

                // If the note hasn't changed, abort
                if (note == bcObject.note) {
                    isEditingNote = false;
                    return;
                }

                if (props.newQuestion) {
                    bcObject.note = note;
                } else {
                    doPost(
                        props.editObjectNoteUrl,
                        {
                            "bc_object_uuid": bcObject.bc_object_uuid,
                            "note": note,
                        },
                        (response) => {
                            getRelatedObjects();
                        },
                        "",
                        "",
                    );
                }
                isEditingNote = false;
            };

            function handleRemoveObject(bcObjectUuid, uuid) {
                if (props.newQuestion) {
                    const newObjectList = objectList.value.filter((x) => x.uuid !== uuid);
                    objectList.value = newObjectList;
                    return;
                }

                doPost(
                    props.removeObjectUrl,
                    {
                        "question_uuid": props.objectUuid,
                        "bc_object_uuid": bcObjectUuid,
                    },
                    (response) => {
                        getRelatedObjects();
                    },
                    "Object removed",
                    "",
                );
            };

            function handleSetNoteIsEditable(bcObject, index) {
                bcObject.noteIsEditable = true;

                nextTick(() => {
                    input.value[index].focus();
                });
            };

            function openObjectSelectModal() {
                ctx.emit("open-object-select-modal");
            };

            onMounted(() => {
                if (!props.newQuestion) {
                    getRelatedObjects();
                }
            });

            return {
                addObject,
                input,
                objectList,
                handleEditNote,
                handleRemoveObject,
                handleSetNoteIsEditable,
                openObjectSelectModal,
            };
        },
    };

</script>
