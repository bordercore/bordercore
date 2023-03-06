<template>
    <div class="hover-target">
        <card class="backdrop-filter" :class="cardClass">
            <template #title-slot>
                <div v-cloak class="card-title d-flex">
                    <div class="dropdown-height d-flex">
                        <div>
                            <font-awesome-icon icon="sticky-note" class="text-primary me-3" />
                        </div>
                        <div class="w-100">
                            <input v-if="isEditingName" v-model="nodeNote.name" class="form-control w-100" @blur="onUpdateName" @keydown.enter="onUpdateName">
                            <span v-else-if="note" @dblclick="onEditName">
                                {{ nodeNote.name }}
                            </span>
                        </div>
                    </div>
                    <div v-if="note !== ''" class="dropdown-menu-container ms-auto">
                        <drop-down-menu :show-on-hover="true">
                            <template #dropdown>
                                <li>
                                    <a class="dropdown-item" href="#" @click.prevent="onUpdateNote()">
                                        <span>
                                            <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />
                                        </span>
                                        Update note
                                    </a>
                                </li>
                                <li>
                                    <a class="dropdown-item" href="#" @click.prevent="onOpenNoteMetadataModal()">
                                        <span>
                                            <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />
                                        </span>
                                        Update note metadata
                                    </a>
                                </li>
                                <li>
                                    <a class="dropdown-item" href="#" @click.prevent="onDeleteNote()">
                                        <span>
                                            <font-awesome-icon icon="times" class="text-primary me-3" />
                                        </span>
                                        Delete note
                                    </a>
                                </li>
                            </template>
                        </drop-down-menu>
                    </div>
                </div>
            </template>
            <template #content>
                <hr class="divider">
                <editable-text-area
                    ref="editableTextArea"
                    v-model="noteContents"
                    default-value="No content"
                    class="node-note"
                    :hide-add-button="true"
                />
            </template>
        </card>
    </div>
</template>

<script>

    import Card from "/front-end/vue/common/Card.vue";
    import DropDownMenu from "/front-end/vue/common/DropDownMenu.vue";
    import EditableTextArea from "/front-end/vue/common/EditableTextArea.vue";
    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

    export default {
        components: {
            Card,
            DropDownMenu,
            EditableTextArea,
            FontAwesomeIcon,
        },
        emits: ["deleteNote", "openNoteMetadataModal", "updateLayout"],
        props: {
            nodeUuid: {
                type: String,
                default: "",
            },
            nodeNoteInitial: {
                type: Object,
                default: function() {},
            },
            deleteNoteUrl: {
                type: String,
                default: "",
            },
            noteUrl: {
                type: String,
                default: "",
            },
            setNoteColorUrl: {
                type: String,
                default: "",
            },
        },
        setup(props, ctx) {
            let nameCache = null;
            const isEditingName = ref(false);
            const nodeNote = ref({});
            const note = ref("");
            const noteContents = ref("");

            const editableTextArea = ref(null);

            watch(noteContents, (newValue) => {
                if (newValue) {
                    updateNoteContents();
                }
            });

            function onUpdateNote() {
                editableTextArea.value.editNote(!note.value.content);
            };

            function onEditName() {
                nameCache = note.value.name;
                isEditingName.value = true;
            };

            function onOpenNoteMetadataModal() {
                ctx.emit("openNoteMetadataModal", updateNoteMetadata, nodeNote.value);
            };

            function onUpdateName() {
                isEditingName.value = false;
                // If the name hasn't changed, abort
                if (nameCache === nodeNote.value.name) {
                    return;
                }
                updateNoteMetadata(nodeNote.value);
            };

            function onDeleteNote() {
                doPost(
                    props.deleteNoteUrl,
                    {
                        "node_uuid": props.nodeUuid,
                        "note_uuid": note.value.uuid,
                    },
                    (response) => {
                        ctx.emit("updateLayout", response.data.layout);
                    },
                    "Note deleted",
                );

                ctx.emit("deleteNote", note.value.uuid);
            };

            function updateNoteMetadata(note) {
                doPost(
                    props.setNoteColorUrl,
                    {
                        "node_uuid": props.nodeUuid,
                        "note_uuid": note.uuid,
                        "color": note.color,
                    },
                    (response) => {
                        nodeNote.value.color = note.color;
                    },
                    "",
                    "",
                );
                updateNoteContents();
            };

            function updateNoteContents() {
                doPut(
                    null,
                    props.noteUrl,
                    {
                        "uuid": nodeNote.value.uuid,
                        "name": nodeNote.value.name,
                        "content": noteContents.value,
                        "is_note": true,
                    },
                    (response) => {},
                    "",
                );
            };

            const cardClass = computed(() => {
                return `node-color-${nodeNote.value.color}`;
            });

            onMounted(() => {
                nodeNote.value = props.nodeNoteInitial;
                getNote();
            });

            function getNote() {
                doGet(
                    props.noteUrl,
                    (response) => {
                        note.value = response.data;
                        noteContents.value = response.data.content;
                    },
                    "Error getting note",
                );
            };

            return {
                cardClass,
                editableTextArea,
                isEditingName,
                getNote,
                onDeleteNote,
                onEditName,
                onOpenNoteMetadataModal,
                onUpdateName,
                onUpdateNote,
                nodeNote,
                note,
                noteContents,
                updateNoteContents,
                updateNoteMetadata,
            };
        },
    };

</script>
