<template>
    <div id="modalUpdateNote" class="modal fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        {{ action }} Note
                    </h4>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" />
                </div>
                <div class="modal-body">
                    <div class="row mb-3">
                        <label class="col-lg-3 col-form-label" for="inputTitle">Name</label>
                        <div class="col-lg-9">
                            <input id="id_name_note" v-model="data.name" type="text" class="form-control" autocomplete="off" maxlength="200" required @keyup.enter="onUpdateNote">
                        </div>
                    </div>
                    <div class="row mb-3">
                        <label class="col-lg-3 col-form-label" for="inputTitle">Color</label>
                        <div class="col-lg-9">
                            <div class="d-flex">
                                <div v-for="color in colors" :key="color" class="node-note-color flex-grow-1 mx-2" :class="getClass(color)" @click="onSelectColor(color)" />
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <input id="btn-action" class="btn btn-primary" type="button" value="Update" @click="onUpdateNote">
                </div>
            </div>
        </div>
    </div>
</template>

<script>

    export default {

        name: "NoteModal",
        data() {
            return {
                action: "Update",
                callback: null,
                modal: null,
                data: {},
                selectedColor: null,
                colors: [1, 2, 3],
            };
        },
        mounted() {
            this.modal = new Modal("#modalUpdateNote");
        },
        methods: {
            getClass(color) {
                const currentColor = `node-note-color-${color}`;
                const selectedColor = color === this.selectedColor ? "selected-color" : "";
                return `${currentColor} ${selectedColor}`;
            },
            openModal(action, callback, data) {
                this.action = action;
                this.callback = callback;
                this.data = data.note;
                this.selectedColor = data.color;
                this.modal.show();
                setTimeout( () => {
                    document.querySelector("#modalUpdateNote input").focus();
                }, 500);
            },
            onSelectColor(color) {
                this.selectedColor = color;
            },
            onUpdateNote() {
                this.callback(this.selectedColor);
                this.modal.hide();
            },
        },

    };

</script>
