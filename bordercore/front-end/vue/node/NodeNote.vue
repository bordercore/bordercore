<template>
    <div class="hover-target">
        <card class="backdrop-filter" :class="`node-note-color-${color}`">
            <template #title-slot>
                <div v-cloak class="card-title d-flex">
                    <div class="dropdown-height d-flex">
                        <div>
                            <font-awesome-icon icon="sticky-note" class="text-primary me-3" />
                        </div>
                        <div class="w-100">
                            <input v-if="isEditingName" v-model="note.name" class="form-control w-100" @blur="onBlur()" @keydown.enter="onBlur">
                            <span v-else-if="note" @dblclick="onEditNote">
                                {{ note.name }}
                            </span>
                        </div>
                    </div>
                    <div v-if="note !== ''" class="ms-auto">
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
                    @update-note="onUpdateNote(color)"
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
            noteColor: {
                type: Number,
                default: 1,
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
                note: null,
                color: null,
                isEditingName: false,
            };
        },
        mounted() {
            this.getNote();
            this.color = this.noteColor;
        },
        methods: {
            onUpdateNoteContents() {
                this.$refs.note.editNote();
            },
            onEditNote() {
                this.$emit("open-modal-note-update", this.onUpdateNote, {"note": this.note, "color": this.color});
            },
            onBlur() {
                // If the note hasn't changed, abort
                if (this.beforeEditCache == this.note.name) {
                    this.isEditingName = false;
                    return;
                }
                this.onUpdateNote(this.color);
                this.isEditingName = false;
            },
            onDeleteNote() {
                this.$emit("delete-note", this.note.uuid);
            },
            onUpdateNote(color) {
                if (color !== this.color) {
                    doPost(
                        this,
                        this.setNoteColorUrl,
                        {
                            "node_uuid": this.$store.state.nodeUuid,
                            "note_uuid": this.note.uuid,
                            "color": color,
                        },
                        (response) => {
                            this.color = color;
                        },
                        "",
                        "",
                    );
                }
                doPut(
                    this,
                    this.updateNoteUrl,
                    {
                        "uuid": this.note.uuid,
                        "name": this.note.name,
                        "content": this.$refs.note.textAreaValue || "",
                        "is_note": true,
                    },
                    (response) => {},
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
