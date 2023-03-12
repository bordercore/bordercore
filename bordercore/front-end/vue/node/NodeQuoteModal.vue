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
                                <div v-for="color in colors" :key="color" class="node-color flex-grow-1 mx-2" :class="getClass(color)" @click="handleColorSelect(color)" />
                            </div>
                        </div>
                    </div>
                    <div class="row mb-3">
                        <label class="col-lg-3 col-form-label" for="inputTitle">Rotate</label>
                        <div class="col-lg-9">
                            <div class="d-flex flex-column">
                                <select v-model="nodeQuote.rotate" class="form-control form-select">
                                    <option v-for="option in rotateOptions" :key="option.value" :value="option.value">
                                        {{ option.display }}
                                    </option>
                                </select>
                                <div class="d-flex align-items-center mt-1">
                                    <o-switch v-model="nodeQuote.favorites_only" value="favorites-only" />
                                    <label class="ms-2">Favorites Only</label>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="row mb-3">
                        <label class="col-lg-3 col-form-label" for="inputTitle">Format</label>
                        <div class="col-lg-9">
                            <div class="d-flex flex-column">
                                <select v-model="nodeQuote.format" class="form-control form-select">
                                    <option v-for="option in formatOptions" :key="option.value" :value="option.value">
                                        {{ option.display }}
                                    </option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <input class="btn btn-primary" type="button" value="Update" @click="handleQuoteUpdate">
                </div>
            </div>
        </div>
    </div>
</template>

<script>

    export default {
        setup() {
            const action = ref("Update");
            const nodeQuote = ref({});

            let callback = null;
            const colors = [1, 2, 3, 4];
            const formatOptions = [
                {
                    value: "standard",
                    display: "Standard",
                },
                {
                    value: "minimal",
                    display: "Minimal",
                },
            ];
            let modal = null;
            let nodeQuoteInitial = {};
            const rotateOptions = [
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
            ];

            function getClass(color) {
                const selectedColor = color === (nodeQuote.value && nodeQuote.value.color) ? "selected-color" : "";
                return `node-color-${color} ${selectedColor}`;
            };

            function handleQuoteUpdate() {
                // If any of the properties have changed, trigger the callback
                if (nodeQuote.value !== nodeQuoteInitial) {
                    callback(nodeQuote.value);
                }
                modal.hide();
            };

            function openModal(actionParam, callbackParam, nodeQuoteParam) {
                nodeQuote.value = nodeQuoteParam;
                nodeQuoteInitial = {...nodeQuote};
                action.value = actionParam;
                callback = callbackParam;
                modal.show();
                setTimeout( () => {
                    document.querySelector("#modalUpdateQuote input").focus();
                }, 500);
            };

            function handleColorSelect(color) {
                nodeQuote.value.color = color;
            };

            onMounted(() => {
                modal = new Modal("#modalUpdateQuote");
            });

            return {
                action,
                colors,
                formatOptions,
                getClass,
                handleColorSelect,
                handleQuoteUpdate,
                openModal,
                nodeQuote,
                rotateOptions,
            };
        },
    };

</script>
