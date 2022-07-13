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
                            <input v-if="isEditingName" v-model="nodeNote.name" class="form-control w-100" @blur="onBlur()" @keydown.enter="onBlur">
                            <span v-else-if="note" @dblclick="onEditName">
                                {{ nodeNote.name }}
                            </span>
                        </div>
                    </div>
                    <div v-if="note !== ''" class="dropdown-menu-container ms-auto">
                        <drop-down-menu :show-on-hover="true">
                            <div slot="dropdown">
                                <a class="dropdown-item" href="#" @click.prevent="onUpdateNoteContents()">
                                    <span>
                                        <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />
                                    </span>
                                    Update note contents
                                </a>
                                <a class="dropdown-item" href="#" @click.prevent="onEditNote()">
                                    <span>
                                        <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />
                                    </span>
                                    Update note
                                </a>
                                <a class="dropdown-item" href="#" @click.prevent="onDeleteNote()">
                                    <span>
                                        <font-awesome-icon icon="times" class="text-primary me-3" />
                                    </span>
                                    Delete note
                                </a>
                            </div>
                        </drop-down-menu>
                    </div>
                </div>
            </template>
            <template #content>
                <hr class="filter-divider mt-0">
                <editable-text-area
                    ref="note"
                    class="node-note"
                    :uuid="nodeUuid"
                    :hide-add-button="true"
                    @update-note="onUpdateNote(nodeNote)"
                />
            </template>
        </card>
    </div>
</template>

<script>

    export default {

        name: "Notes",
        props: {
            nodeUuid: {
                type: String,
                default: "",
            },
            nodeNoteInitial: {
                type: Object,
                default: function() {},
            },
            getNodeUrl: {
                type: String,
                default: "",
            },
            updateNoteUrl: {
                type: String,
                default: "",
            },
            setNoteColorUrl: {
                type: String,
                default: "",
            },
        },
        data() {
            return {
                isEditingName: false,
                nodeNote: {},
                note: null,
            };
        },
        computed: {
            cardClass() {
                return `node-color-${this.nodeNote.color}`;
            },
        },
        mounted() {
            this.nodeNote = this.nodeNoteInitial;
            this.getNote();
        },
        methods: {
            onUpdateNoteContents() {
                this.$refs.note.editNote(!this.note.content);
            },
            onEditName() {
                this.beforeEditCache = this.note.name;
                this.isEditingName = true;
            },
            onEditNote() {
                this.$emit("open-modal-note-update", this.onUpdateNote, this.nodeNote);
            },
            onBlur() {
                this.isEditingName = false;
                // If the name hasn't changed, abort
                if (this.beforeEditCache === this.nodeNote.name) {
                    return;
                }
                this.onUpdateNote(this.nodeNote);
            },
            onDeleteNote() {
                this.$emit("delete-note", this.note.uuid);
            },
            onUpdateNote(note) {
                doPost(
                    this,
                    this.setNoteColorUrl,
                    {
                        "node_uuid": this.$store.state.nodeUuid,
                        "note_uuid": this.note.uuid,
                        "color": note.color,
                    },
                    (response) => {
                        this.nodeNote.color = note.color;
                    },
                    "",
                    "",
                );
                const noteContent = this.$refs.note.textAreaValue || "";
                doPut(
                    this,
                    this.updateNoteUrl,
                    {
                        "uuid": this.note.uuid,
                        "name": this.nodeNote.name,
                        "content": noteContent,
                        "is_note": true,
                    },
                    (response) => {
                        this.note.content = noteContent;
                    },
                    "",
                );
            },
            getNote() {
                doGet(
                    this,
                    this.getNodeUrl,
                    (response) => {
                        this.note = response.data;
                        this.$refs.note.setTextAreaValue(response.data.content);
                    },
                    "Error getting note",
                );
            },
            setSelectionRange(input, selectionStart, selectionEnd) {
                if (input.setSelectionRange) {
                }
            },
        },
    };

</script>
