<template>
    <div class="position-fixed top-0 end-0 p-3" style="z-index: 11">
        <div id="liveToast" class="toast hide" :class="variant" role="alert" :data-bs-autohide="autoHide" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <strong class="me-auto" v-html="title" />
                <small>11 mins ago</small>
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
                body: "Toast Body",
                variant: "info",
                autoHide: false,
                bsToast: null,
            };
        },
        mounted() {
            const el = document.querySelector(".toast");
            this.bsToast = new Toast(el, {});
            EventBus.$on("toast", (payload) => {
                console.log("toast received: " + payload);
                this.toast(payload);
            });
        },
        methods: {
            toast(payload) {
                this.title = payload.title;
                this.body = payload.body;
                this.variant = payload.variant ? payload.variant : "info";
                this.bsToast.show();
            },
        },
    };

</script>
