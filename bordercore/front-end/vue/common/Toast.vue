<template>
    <div class="toast-wrapper position-fixed top-0 end-0 p-3" :class="variant">
        <div id="liveToast" class="toast hide" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <strong class="me-auto" v-html="title" />
                <small v-html="additionalTitle" />
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close" />
            </div>
            <div class="toast-body d-flex align-items-top">
                <font-awesome-icon class="fa-lg me-2 mt-1 mb-1 pt-1" :class="'text-' + variant" :icon="getIcon()" />
                <div v-html="body" />
            </div>
        </div>
    </div>
</template>

<script>

    import {Toast} from "bootstrap";
    window.Toast = Toast;

    export default {
        name: "Toast",
        props: {
            initialMessages: {
                type: Array,
                default: () => [],
            },
            defaultVariant: {
                type: String,
                default: "info",
            },
        },
        data() {
            return {
                title: "",
                additionalTitle: "",
                body: "Toast Body",
                variant: "info",
                delay: 5000,
                autoHide: true,
                bsToast: null,
            };
        },
        mounted() {
            const el = document.querySelector(".toast");
            this.bsToast = new Toast(el, {autohide: this.autoHide, delay: this.delay});
            EventBus.$on("toast", (payload) => {
                this.toast(payload);
            });

            for (const message of this.initialMessages) {
                this.toast(message);
            }
        },
        methods: {
            toast(payload) {
                if (payload.variant !== undefined) {
                    this.variant = payload.variant;
                } else {
                    this.variant = this.defaultVariant;
                }
                if (payload.title !== undefined) {
                    this.title = payload.title;
                } else {
                    this.title = this.variant.charAt(0).toUpperCase() + this.variant.slice(1);
                }
                this.body = payload.body;
                if (payload.autoHide !== undefined) {
                    this.bsToast._config.autohide = payload.autoHide;
                }
                if (payload.delay) {
                    this.bsToast._config.delay = payload.delay;
                }
                this.bsToast.show();
            },
            getIcon() {
                if (this.variant === "danger") {
                    return "exclamation-triangle";
                } else if (this.variant === "warning") {
                    return "question";
                } else {
                    return "check";
                }
            },
        },
    };

</script>
