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
                        <draggable v-model="objectList" draggable=".draggable" item-key="uuid" :component-data="{type:'transition-group'}" chosen-class="related-draggable" ghost-class="related-draggable" drag-class="related-draggable" @change="handleSort">
                            <template #item="{element}">
                                <li v-cloak :key="element.uuid" class="hover-target list-group-item list-group-item-secondary draggable px-0" :data-uuid="element.uuid">
                                    <div class="dropdown-height d-flex align-items-start">
                                        <div class="d-flex flex-column">
                                            <div v-if="element.type === 'bookmark'" class="pe-2">
                                                <img :src="element.cover_url" width="120" height="67">
                                            </div>
                                            <div v-else-if="element.type === 'blob'" class="pe-2">
                                                <img :src="element.cover_url">
                                            </div>
                                            <div>
                                                <a :href="element.url">{{ element.name }}</a>
                                            </div>
                                            <Transition name="fade" mode="out-in" @after-enter="handleInputTransition">
                                                <div v-if="!element.noteIsEditable" class="node-object-note" @click="element.noteIsEditable = true">
                                                    {{ element.note }}
                                                </div>
                                                <div v-else>
                                                    <input ref="input" type="text" class="form-control form-control-sm" :value="element.note" placeholder="" autocomplete="off" @blur="handleEditNote(element, $event.target.value)" @keydown.enter="handleEditNote(element, $event.target.value)">
                                                </div>
                                            </Transition>
                                        </div>
                                        <drop-down-menu ref="editNoteMenu" :show-on-hover="true">
                                            <template #dropdown>
                                                <li>
                                                    <a class="dropdown-item" href="#" @click.prevent="handleRemoveObject(element)">
                                                        <font-awesome-icon icon="trash-alt" class="text-primary me-3" />Remove
                                                    </a>
                                                    <a class="dropdown-item" :href="element.edit_url">
                                                        <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />Edit <span>{{ element.type }}</span>
                                                    </a>
                                                    <a class="dropdown-item" href="#" @click.prevent="element.noteIsEditable = true">
                                                        <font-awesome-icon :icon="element.note ? 'pencil-alt' : 'plus'" class="text-primary me-3" />{{ element.note ? 'Edit' : 'Add' }} note
                                                    </a>
                                                </li>
                                            </template>
                                        </drop-down-menu>
                                    </div>
                                </li>
                            </template>
                        </draggable>
                        <div v-cloak v-if="objectList.length == 0" :key="1" class="text-muted">
                            No related objects
                        </div>
                    </ul>
                </template>
            </card>
        </transition>
    </div>
</template>

<script>

    import Card from "/front-end/vue/common/Card.vue";
    import draggable from "vuedraggable";
    import DropDownMenu from "/front-end/vue/common/DropDownMenu.vue";
    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

    export default {
        components: {
            Card,
            draggable,
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
            sortRelatedObjectsUrl: {
                default: "url",
                type: String,
            },
            updateRelatedObjectNoteUrl: {
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
            newBlob: {
                default: false,
                type: Boolean,
            },
        },
        emits: ["open-object-select-modal"],
        setup(props, ctx) {
            const input = ref(null);
            const objectList = ref([]);

            function addObject(bcObject) {
                if (props.newBlob) {
                    objectList.value.push(bcObject);
                    return;
                }

                doPost(
                    props.addObjectUrl,
                    {
                        "node_uuid": props.objectUuid,
                        "object_uuid": bcObject.uuid,
                    },
                    (response) => {
                        getRelatedObjects();
                    },
                    "Object added",
                );
            };

            function getRelatedObjects() {
                doGet(
                    props.relatedObjectsUrl.replace(/00000000-0000-0000-0000-000000000000/, props.objectUuid),
                    (response) => {
                        objectList.value = response.data.blob_list;
                    },
                    "Error getting related objects",
                );
            };

            function handleEditNote(bcObject, note) {
                bcObject.noteIsEditable = false;

                // If the note hasn't changed, abort
                if (note == bcObject.note) {
                    return;
                }

                bcObject.note = note;
                doPost(
                    props.updateRelatedObjectNoteUrl,
                    {
                        "node_uuid": props.objectUuid,
                        "object_uuid": bcObject.uuid,
                        "note": note,
                    },
                    (response) => {
                        getRelatedObjects();
                    },
                );
            };

            function handleInputTransition(evt) {
                const input = evt.querySelector("input");
                if (input) {
                    input.focus();
                }
            };

            function handleRemoveObject(bcObject) {
                if (props.newBlob) {
                    const newObjectList = objectList.value.filter((x) => x.uuid !== bcObject.uuid);
                    objectList.value = newObjectList;
                    return;
                }

                doPost(
                    props.removeObjectUrl,
                    {
                        "node_uuid": props.objectUuid,
                        "object_uuid": bcObject.uuid,
                    },
                    (response) => {
                        getRelatedObjects();
                    },
                    "Object removed",
                );
            };

            function handleSort(evt) {
                const blobUuid = evt.moved.element.uuid;

                // The backend expects the ordering to begin
                // with 1, not 0, so add 1.
                const newPosition = evt.moved.newIndex + 1;

                if (props.newBlob) {
                    return;
                }

                doPost(
                    props.sortRelatedObjectsUrl,
                    {
                        "node_uuid": props.objectUuid,
                        "object_uuid": blobUuid,
                        "new_position": newPosition,
                    },
                    () => {},
                );
            };

            function openObjectSelectModal() {
                ctx.emit("open-object-select-modal");
            };

            onMounted(() => {
                if (!props.newBlob) {
                    getRelatedObjects();
                }
            });

            return {
                addObject,
                input,
                objectList,
                handleEditNote,
                handleInputTransition,
                handleRemoveObject,
                handleSort,
                openObjectSelectModal,
            };
        },
    };

</script>
