<template>
    <div id="modalUpdateCollection" class="modal fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        Update Collection
                    </h4>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" />
                </div>
                <div class="modal-body">
                    <div class="row mb-3">
                        <label class="col-lg-3 col-form-label" for="inputTitle">Name</label>
                        <div class="col-lg-9">
                            <input id="id_name_collection" type="text" name="name" :value="data.name" class="form-control" autocomplete="off" maxlength="200" required @keyup.enter="onUpdateCollection">
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <input id="btn-action" class="btn btn-primary" type="button" value="Update" @click="onUpdateCollection">
                </div>
            </div>
        </div>
    </div>
</template>

<script>

    export default {

        name: "CollectionObjectListModal",
        data() {
            return {
                callback: null,
                modal: null,
                data: {},
            };
        },
        mounted() {
            this.modal = new Modal("#modalUpdateCollection");
        },
        methods: {
            openModal(callback, data) {
                this.callback = callback;
                this.data = data;
                this.modal.show();
                setTimeout( () => {
                    document.querySelector("#modalUpdateCollection input").focus();
                }, 500);
            },
            onUpdateCollection() {
                this.callback();
                this.modal.hide();
            },
        },

    };

</script>
