<template>
    <div class="d-flex flex-column align-items-center w-25">
        <div class="option-icon" :class="{'enabled': enabled}" @click="handleEnable">
            <font-awesome-icon :icon="icon" class="text-primary" />
        </div>
        <div>
            {{ label }}
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
            icon: {
                type: String,
                default: "",
            },
            label: {
                type: String,
                default: "Label",
            },
            initialEnabled: {
                type: Boolean,
                default: false,
            },
            formName: {
                type: String,
                default: "form-name",
            },
        },
        emits: ["enable-option"],
        setup(props, ctx) {
            const enabled = ref(false);

            enabled.value = props.initialEnabled;

            function handleEnable() {
                enabled.value = !enabled.value;
                ctx.emit("enable-option", props.formName, enabled.value);
            };

            return {
                enabled,
                handleEnable,
            };
        },
    };

</script>
