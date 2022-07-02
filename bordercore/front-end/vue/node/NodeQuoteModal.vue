<template>
    <div id="modalUpdateQuote" class="modal fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        {{ action }} Quote
                    </h4>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" />
                </div>
                <div class="modal-body">
                    <div class="row mb-3">
                        <label class="col-lg-3 col-form-label" for="inputTitle">Color</label>
                        <div class="col-lg-9">
                            <div class="d-flex">
                                <div v-for="color in colors" :key="color" class="node-note-color flex-grow-1 mx-2" :class="getClass(color)" @click="onSelectColor(color)" />
                            </div>
                        </div>
                    </div>
                    <div class="row mb-3">
                        <label class="col-lg-3 col-form-label" for="inputTitle">Rotate</label>
                        <div class="col-lg-9">
                            <select v-model="selectedRotate" class="form-control form-select">
                                <option v-for="option in rotateInterval" :key="option.value" :value="option.value">
                                    {{ option.display }}
                                </option>
                            </select>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <input id="btn-action" class="btn btn-primary" type="button" value="Update" @click="onUpdateQuote">
                </div>
            </div>
        </div>
    </div>
</template>

<script>

    export default {

        name: "QuoteModal",
        data() {
            return {
                action: "Update",
                callback: null,
                modal: null,
                data: {},
                selectedColor: null,
                selectedRotate: null,
                colors: [1, 2, 3],
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
            this.modal = new Modal("#modalUpdateQuote");
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
                this.selectedColor = data.color;
                this.selectedRotate = data.rotate;
                this.modal.show();
                setTimeout( () => {
                    document.querySelector("#modalUpdateQuote input").focus();
                }, 500);
            },
            onSelectColor(color) {
                this.selectedColor = color;
            },
            onUpdateQuote() {
                this.callback(this.selectedColor, this.selectedRotate);
                this.modal.hide();
            },
        },

    };

</script>
