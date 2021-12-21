<template>
    <div>
        <div v-if="textAreaValue || isEditingNote" :class="[isEditingNote ? 'editing' : '', extraClass]">
            <slot name="title" />
            <label class="editable-textarea-label w-100" data-toggle="tooltip" data-placement="bottom" title="Doubleclick to edit note" @dblclick="editNote" v-html="textAreaMarkdown" />
            <textarea id="note" v-model="textAreaValue" class="editable-textarea px-3" placeholder="Enter note text here" @blur="doneEdit()" />
        </div>
        <div v-else class="ml-2" :class="extraClass">
            <font-awesome-icon icon="plus" />
            <a href="#" @click="addNote">Add Note</a>
        </div>
    </div>
</template>

<script>

    export default {
        props: {
            value: {
                default: "",
                type: String,
            },
            uuid: {
                type: String,
                default: "",
            },
            editUrl: {
                type: String,
                default: "",
            },
            extraClass: {
                type: String,
                default: "mt-4",
            },
        },
        data() {
            return {
                isEditingNote: false,
                minNumberRows: 10,
                textAreaValue: this.value,
            };
        },
        computed: {
            textAreaMarkdown() {
                if (!this.textAreaValue) {
                    return "";
                }

                const md = window.markdownit({
                    highlight: function(str, lang) {
                        if (lang && hljs.getLanguage(lang)) {
                            try {
                                return hljs.highlight(str, {language: lang}).value;
                            } catch (__) {}
                        }

                        return ""; // use external default escaping
                    },
                });
                const result = md.render(this.textAreaValue);
                return result;
            },
        },
        methods: {
            setTextAreaValue(value) {
                this.textAreaValue = value;
            },
            editNote() {
                this.beforeEditCache = this.textAreaValue;
                this.isEditingNote = true;

                // We want the generated textarea to equal the size
                //  of the note itself. To do this, we need to know
                //  how many rows to use.

                const txtarea = document.getElementById("note");

                if (txtarea) {
                    // The lineHeight is the height of each row
                    const style = getComputedStyle(txtarea);
                    const lineHeight = style.lineHeight;

                    // Get the height of the note text
                    const offsetHeight = document.querySelector(".editable-textarea-label").offsetHeight;

                    // Divide the note text height by the row height to
                    //  get target number of rows for the textarea
                    const rows = offsetHeight / parseInt(lineHeight, 10);

                    if (rows > this.minNumberRows) {
                        txtarea.setAttribute("rows", rows);
                    } else {
                        txtarea.setAttribute("rows", this.minNumberRows);
                    }

                    // Position the cursor at the beginning of the textarea
                    txtarea.focus();
                    txtarea.setSelectionRange(0, 0);
                }

                this.$nextTick(() => {
                    document.getElementById("note").focus();
                });
            },
            doneEdit() {
                // If the note hasn't changed, abort
                if (this.beforeEditCache == this.textAreaValue) {
                    this.isEditingNote = false;
                    return;
                }

                doPost(
                    this,
                    this.editUrl,
                    {
                        "uuid": this.uuid,
                        "note": this.textAreaValue,
                    },
                    (response) => {
                        // Let the parent element know about the new value
                        this.$emit("input", this.textAreaValue);
                    },
                    "",
                    "",
                );

                this.isEditingNote = false;
            },
            addNote() {
                this.$nextTick(() => {
                    this.editNote();
                });
            },
        },
    };

</script>
