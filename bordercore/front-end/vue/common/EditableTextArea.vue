<template>
    <div>
        <div v-if="textAreaValue || isEditingNote" :class="extraClass" class="editable-textarea position-relative">
            <slot name="title" />
            <Transition name="fade" mode="out-in" @after-enter="onAfterEnterTransition" @enter="onEnterTransition">
                <label v-if="!isEditingNote" ref="noteLabel" class="w-100" data-bs-toggle="tooltip" data-placement="bottom" title="Doubleclick to edit note" @dblclick="editNote(false)" v-html="textAreaMarkdown" />
                <textarea v-else ref="textarea" v-model="textAreaValue" class="px-3 w-100" placeholder="Note text" @blur="onBlur()" />
            </Transition>
        </div>
        <div v-else>
            <div class="text-notice">
                {{ defaultValue }}
            </div>
            <div v-if="!hideAddButton" class="ms-2" :class="extraClass">
                <font-awesome-icon icon="plus" />
                <a href="#" @click="onAddNote">Add Note</a>
            </div>
        </div>
    </div>
</template>

<script>

    import {toRefs} from "vue";
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
        emits: ["update:modelValue"],
        setup(props, ctx) {
            const isEditingNote = ref(false);
            const textAreaValue = ref(props.modelValue);
            const textAreaMarkdown = ref("");

            let cache = null;
            let labelOffsetHeight = 0;
            const minNumberRows = 10;
            const stateRef = toRefs(props).modelValue;

            const noteLabel = ref(null);
            const textarea = ref(null);

            watch(stateRef, (newValue) => {
                updateValue(newValue);
            });

            function editNote(focusTextArea=false) {
                cache = textAreaValue.value;

                // When transitioning from non-editing to editing, ie
                // from the label to the textarea, save the offset height.
                // We'll need it in the 'onAfterEnterTransition' handler.
                if (noteLabel.value) {
                    labelOffsetHeight = noteLabel.value.offsetHeight;
                }

                isEditingNote.value = true;
                if (focusTextArea) {
                    // This is often set when creating a new value,
                    //  in which case the usual Vue transitions won't
                    //  trigger which would ordinarily focus the element.
                    //  So we need to do that ourselves.
                    nextTick(() => {
                        textarea.value.focus();
                    });
                }
            };

            function onAddNote() {
                nextTick(() => {
                    editNote(false);
                });
            };

            function onAfterEnterTransition() {
                nextTick(() => {
                    // If textarea is not null, then we have transitioned
                    //  from label to textarea
                    if (textarea.value) {
                        // The lineHeight is the height of each row
                        const lineHeight = getComputedStyle(textarea.value).lineHeight;

                        // We want the textarea to equal the size of the note
                        //  itself. To do this, we need to know how many rows to use.

                        // Divide the note text height by the row height to
                        //  get target number of rows for the textarea
                        const rows = labelOffsetHeight / parseInt(lineHeight, 10);

                        textarea.value.setAttribute(
                            "rows",
                            rows > minNumberRows ? rows : minNumberRows,
                        );

                        // Position the cursor at the beginning of the textarea
                        nextTick(() => {
                            textarea.value.focus();
                        });
                        textarea.value.setSelectionRange(0, 0);
                    }
                });
            };

            function onBlur() {
                isEditingNote.value = false;
                // If the note hasn't changed, abort
                if (cache === textAreaValue.value) {
                    return;
                }
                updateNote();
            };

            function onEnterTransition() {
                // When transitioning from editing to non-editing,
                // ie from the textarea to the label, then
                // tell prism.js to re-highlight any code.
                if (!isEditingNote.value) {
                    Prism.highlightAll();
                }
            };

            function updateNote() {
                ctx.emit("update:modelValue", textAreaValue.value);
            };

            function updateValue(value) {
                if (value !== null) {
                    textAreaValue.value = value;
                    textAreaMarkdown.value = markdown.render(value);
                    nextTick(() => {
                        Prism.highlightAll();
                    });
                }
            };

            onMounted(() => {
                updateValue(props.modelValue);
            });

            return {
                editNote,
                isEditingNote,
                labelOffsetHeight,
                minNumberRows,
                noteLabel,
                onAddNote,
                onAfterEnterTransition,
                onBlur,
                onEnterTransition,
                textarea,
                textAreaMarkdown,
                textAreaValue,
            };
        },
    };

</script>
