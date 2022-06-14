<template>
    <div class="hover-target">
        <card class="backdrop-filter">
            <template #title-slot>
                <div v-cloak class="card-title d-flex">
                    <div class="dropdown-height d-flex">
                        <div>
                            <font-awesome-icon icon="sticky-note" class="text-primary me-3" />
                        </div>
                        <div class="w-100">
                            <input v-if="isEditingTitle" v-model="note.name" class="form-control w-100" @blur="onBlur()" @keydown.enter="onBlur">
                            <span v-else-if="note">
                                {{ note.name }}
                            </span>
                        </div>
                    </div>
                    <div v-if="note !== ''" class="ms-auto">
                        <drop-down-menu :show-on-hover="true">
                            <div slot="dropdown">
                                <a v-if="note" class="dropdown-item" href="#" @click.prevent="onEditNote()">
                                    <span>
                                        <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />
                                    </span>
                                    Edit note
                                </a>
                                <a v-if="note" class="dropdown-item" href="#" @click.prevent="onEditNoteTitle()">
                                    <span>
                                        <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />
                                    </span>
                                    Edit note title
                                </a>
                                <a v-if="note" class="dropdown-item" href="#" @click.prevent="onDeleteNote()">
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
                    :note="note"
                    :uuid="nodeUuid"
                    :hide-add-button="true"
                    @update-note="onUpdateNote"
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
            getNodeUrl: {
                type: String,
                default: "",
            },
            updateNoteUrl: {
                type: String,
                default: "",
            },
        },
        data() {
            return {
                note: null,
                isEditingTitle: false,
            };
        },
        mounted() {
            this.getNote();
        },
        methods: {
            onEditNote() {
                this.$refs.note.editNote();
            },
            onEditNoteTitle() {
                this.beforeEditCache = this.note.name;
                this.isEditingTitle = true;
                self = this;
                setTimeout( () => {
                    self.$el.querySelector("input").focus();
                }, 100);
            },
            onBlur() {
                // If the note hasn't changed, abort
                if (this.beforeEditCache == this.note.name) {
                    this.isEditingTitle = false;
                    return;
                }
                this.onUpdateNote();
                this.isEditingTitle = false;
            },
            onDeleteNote() {
                this.$emit("delete-note", this.note.uuid);
            },
            onUpdateNote() {
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
