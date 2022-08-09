<template>
    <div id="modalNote" class="modal fade" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    {{ header }}
                </div>
                <div class="modal-body" />
            </div>
        </div>
    </div>
</template>

<script>

    export default {
        name: "NoteModal",
        props: {
            header: {
                type: String,
                default: "Note",
            },
        },
        data() {
            return {
                modalNote: null,
            };
        },
        mounted() {
            this.modalNote = new Modal("#modalNote");
        },
        methods: {
            showNote(note) {
                const el = document.querySelector("#modalNote .modal-body");
                el.innerHTML = markdown.render(note);
                this.modalNote.show();
            },
        },
    };

</script>
