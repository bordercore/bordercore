<template>
    <div id="modalUpdateCollection" class="modal fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        {{ action }} Collection
                    </h4>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" />
                </div>
                <div class="modal-body">
                    <div class="row mb-3">
                        <label class="col-lg-3 col-form-label" for="inputTitle">Name</label>
                        <div class="col-lg-9">
                            <input v-model="collectionObjectList.name" type="text" class="form-control" autocomplete="off" maxlength="200" required @keyup.enter="onUpdateCollection">
                        </div>
                    </div>
                    <div class="row mb-3">
                        <label class="col-lg-3 col-form-label" for="inputTitle">Display</label>
                        <div class="col-lg-9">
                            <div class="d-flex flex-column">
                                <select v-model="collectionObjectList.display" class="form-control form-select">
                                    <option v-for="option in displayOptions" :key="option.value" :value="option.value">
                                        {{ option.display }}
                                    </option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div v-if="collectionObjectList.display === 'individual'" class="row mb-3">
                        <label class="col-lg-3 col-form-label" for="inputTitle">Rotate</label>
                        <div class="col-lg-9">
                            <div class="d-flex flex-column">
                                <select v-model="collectionObjectList.rotate" class="form-control form-select">
                                    <option v-for="option in rotateOptions" :key="option.value" :value="option.value">
                                        {{ option.display }}
                                    </option>
                                </select>
                            </div>
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
                action: "Update",
                callback: null,
                collectionObjectList: {},
                collectionObjectListInitial: {},
                modal: null,
                displayOptions: [
                    {
                        value: "list",
                        display: "List",
                    },
                    {
                        value: "individual",
                        display: "Individual",
                    },
                ],
                rotateOptions: [
                    {
                        value: -1,
                        display: "Never",
                    },
                    {
                        value: 1,
                        display: "Every Minute",
                    },
                    {
                        value: 5,
                        display: "Every 5 Minutes",
                    },
                    {
                        value: 10,
                        display: "Every 10 Minutes",
                    },
                    {
                        value: 30,
                        display: "Every 30 Minutes",
                    },
                    {
                        value: 60,
                        display: "Every Hour",
                    },
                    {
                        value: 1440,
                        display: "Every Day",
                    },
                ],
            };
        },
        mounted() {
            this.modal = new Modal("#modalUpdateCollection");
        },
        methods: {
            openModal(action, callback, collectionObjectList) {
                this.collectionObjectList = collectionObjectList;
                this.collectionObjectListInitial = {...collectionObjectList};
                this.action = action;
                this.callback = callback;
                this.modal.show();
                setTimeout( () => {
                    document.querySelector("#modalUpdateCollection input").focus();
                }, 500);
            },
            onUpdateCollection() {
                // If any of the properties have changed, trigger the callback
                if (this.collectionObjectList !== this.collectionObjectListInitial) {
                    this.callback(this.collectionObjectList);
                }
                this.modal.hide();
            },
        },

    };

</script>
