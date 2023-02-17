<template>
    <div>
        <div v-if="textAreaValue || isEditingNote" :class="extraClass" class="editable-textarea position-relative">
            <slot name="title" />
            <Transition name="fade" mode="out-in" @before-leave="onBeforeLeave" @before-enter="onBeforeEnter" @enter="onEnter">
                <label v-if="!isEditingNote" class="w-100" data-bs-toggle="tooltip" data-placement="bottom" title="Doubleclick to edit note" @dblclick="editNote(false)" v-html="textAreaMarkdown" />
                <textarea v-else v-model="textAreaValue" class="px-3 w-100" placeholder="Note text" @blur="onBlur()" />
            </Transition>
        </div>
        <div v-else>
            <div class="text-notice">
                {{ defaultValue }}
            </div>
            <div v-if="!hideAddButton" class="ms-2" :class="extraClass">
                <font-awesome-icon icon="plus" />
                <a href="#" @click="addNote">Add Note</a>
            </div>
        </div>
    </div>
</template>

<script>

    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

    export default {
        components: {
            FontAwesomeIcon,
        },
        props: {
            defaultValue: {
                default: "",
                type: String,
            },
            modelValue: {
                default: "",
                type: String,
            },
            editUrl: {
                type: String,
                default: "",
            },
            extraClass: {
                type: String,
                default: "mt-4",
            },
            hideAddButton: {
                type: Boolean,
                default: false,
            },
        },
        data() {
            return {
                isEditingNote: false,
                labelOffsetHeight: 0,
                minNumberRows: 10,
                textAreaValue: this.modelValue,
            };
        },
        computed: {
            textAreaMarkdown() {
                if (!this.textAreaValue) {
                    return "";
                }
                return markdown.render(this.textAreaValue);
            },
        },
        methods: {
            setTextAreaValue(value) {
                this.textAreaValue = modelValue;
                this.$nextTick(() => {
                    Prism.highlightAll();
                });
            },
            onEnter() {
                // When transitioning from editing to non-editing,
                // ie from the textarea to the label, then
                // tell prism.js to re-highlight any code.
                if (!this.isEditingNote) {
                    Prism.highlightAll();
                }
            },
            onBeforeLeave() {
                // When transitioning from non-editing to editing,
                // ie from the label to the textarea, then
                // save the offset height.
                // We'll need it in the 'onBeforeEnter' handler.
                if (this.isEditingNote) {
                    // We want the generated textarea to equal the size
                    //  of the note itself. To do this, we need to know
                    //  how many rows to use.
                    this.labelOffsetHeight = this.$el.querySelector(".editable-textarea label").offsetHeight;
                }
            },
            onBeforeEnter() {
                this.$nextTick(() => {
                    const txtarea = this.$el.querySelector(".editable-textarea textarea");
                    if (txtarea) {
                        // The lineHeight is the height of each row
                        const lineHeight = getComputedStyle(txtarea).lineHeight;

                        // Divide the note text height by the row height to
                        //  get target number of rows for the textarea
                        const rows = this.labelOffsetHeight / parseInt(lineHeight, 10);

                        if (rows > this.minNumberRows) {
                            txtarea.setAttribute("rows", rows);
                        } else {
                            txtarea.setAttribute("rows", this.minNumberRows);
                        }

                        // Position the cursor at the beginning of the textarea
                        this.$nextTick(() => {
                            txtarea.focus();
                        });
                        txtarea.setSelectionRange(0, 0);
                    }
                });
            },
            editNote(focusTextArea=false) {
                this.beforeEditCache = this.textAreaValue;
                this.isEditingNote = true;
                if (focusTextArea) {
                    // This is typically true when creating a new value,
                    //  in which case the usual Vue transitions won't
                    //  trigger when would ordinarily focus the element.
                    //  So we need to do that ourselves.
                    this.$nextTick(() => {
                        this.$el.querySelector(".editable-textarea textarea").focus();
                    });
                }
            },
            onBlur() {
                this.isEditingNote = false;
                // If the note hasn't changed, abort
                if (this.beforeEditCache == this.textAreaValue) {
                    return;
                }
                this.updateNote();
            },
            updateNote() {
                this.$emit("update-note");
            },
            addNote() {
                this.$nextTick(() => {
                    this.editNote(false);
                });
            },
            deleteNote() {
                this.textAreaValue = "";
                this.updateNote();
            },
        },
    };

</script>
