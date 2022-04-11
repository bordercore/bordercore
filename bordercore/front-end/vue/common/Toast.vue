<template>
    <div class="toast-wrapper position-fixed top-0 end-0 p-3">
        <div id="liveToast" class="toast hide" :class="variant" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <strong class="me-auto" v-html="title" />
                <small v-html="additionalTitle" />
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close" />
            </div>
            <div class="toast-body" v-html="body" />
        </div>
    </div>
</template>

<script>

    import {Toast} from "bootstrap";
    window.Toast = Toast;

    export default {
        name: "Toast",
        data() {
            return {
                title: "Info",
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
        },
        methods: {
            toast(payload) {
                this.title = payload.title;
                this.body = payload.body;
                this.variant = payload.variant ? payload.variant : "info";
                if (payload.autoHide !== null) {
                    this.bsToast._config.autohide = payload.autoHide;
                }
                if (payload.delay) {
                    this.bsToast._config.delay = payload.delay;
                }
                this.bsToast.show();
            },
        },
    };

</script>
