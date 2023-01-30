// This debounce method is meant to be used as a mixin for Vue components

const delay = 300; // default debounce delay in milliseconds

export default {
    methods: {
        debounce(method, timer = delay) {
            if (this.$_debounceTimer !== null) {
                clearTimeout(this.$_debounceTimer);
            }
            this.$_debounceTimer = setTimeout(() => {
                method();
            }, timer);
        },
    },
    created() {
        this.$_debounceTimer = null;
    },
};
