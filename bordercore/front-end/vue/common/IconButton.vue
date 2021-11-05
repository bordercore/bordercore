<template>
    <div class="d-flex flex-column align-items-center w-25">
        <div class="option-icon" :class="{'enabled': enabled}" @click="onClick">
            <font-awesome-icon :icon="icon" class="text-primary" />
        </div>
        <div>
            {{ label }}
        </div>
    </div>
</template>

<script>

    export default {

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
        data() {
            return {
                enabled: false,
            };
        },
        mounted() {
            this.enabled = this.initialEnabled;
        },
        methods: {
            onClick() {
                this.enabled = !this.enabled;
                this.$emit("enable-option", this.formName, this.enabled);
            },
        },

    };

</script>
