<template>
    <div class="hover-target">
        <card class="mx-0">
            <template #title-slot>
                <div v-cloak class="card-title d-flex">
                    <div class="dropdown-height">
                        <font-awesome-icon icon="sticky-note" class="text-primary me-3" />Notes
                    </div>
                    <div v-if="note !== ''" class="ms-auto">
                        <drop-down-menu :show-on-hover="true">
                            <div slot="dropdown">
                                <li>
                                    <a v-if="note" class="dropdown-item" href="#" @click.prevent="editNote()">Edit note</a>
                                </li>
                            </div>
                        </drop-down-menu>
                    </div>
                </div>
            </template>
            <template #content>
                <editable-text-area
                    ref="note"
                    :note="note"
                    :uuid="nodeUuid"
                    :edit-url="editUrl"
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
            editUrl: {
                type: String,
                default: "",
            },
        },
        data() {
            return {
                note: null,
                show: false,
                minNumberRows: 10,
            };
        },
        mounted() {
            this.getNote();
        },
        methods: {
            editNote() {
                this.$refs.note.editNote();
            },
            getNote() {
                doGet(
                    this,
                    this.getNodeUrl,
                    (response) => {
                        this.note = response.data.note;
                        this.$refs.note.setTextAreaValue(response.data.note);
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
