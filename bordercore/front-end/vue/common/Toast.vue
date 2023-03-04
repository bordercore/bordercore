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
                <div class="mt-1" v-html="body" />
            </div>
        </div>
    </div>
</template>

<script>

    import {Toast} from "bootstrap";
    window.Toast = Toast;
    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

    export default {
        name: "Toast",
        components: {
            FontAwesomeIcon,
        },
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
        setup(props) {
            const title = ref("");
            const additionalTitle = ref("");
            const body = ref("Toast Body");
            const variant = ref("info");
            const delay = ref(5000);
            const autoHide = ref(true);
            const bsToast = ref(null);

            function toast(payload) {
                if (payload.variant !== undefined) {
                    variant.value = payload.variant;
                } else {
                    variant.value = props.defaultVariant;
                }
                if (payload.title !== undefined) {
                    title.value = payload.title;
                } else {
                    title.value = variant.value.charAt(0).toUpperCase() + variant.value.slice(1);
                }
                body.value = payload.body;
                if (payload.autoHide !== undefined) {
                    bsToast.value._config.autohide = payload.autoHide;
                }
                if (payload.delay) {
                    bsToast.value._config.delay = payload.delay;
                }
                bsToast.value.show();
            };

            function getIcon() {
                if (variant.value === "danger") {
                    return "exclamation-triangle";
                } else if (variant.value === "warning") {
                    return "question";
                } else {
                    return "check";
                }
            };

            onMounted(() => {
                const el = document.querySelector(".toast");
                bsToast.value = new Toast(el, {autohide: autoHide.value, delay: delay.value});
                EventBus.$on("toast", (payload) => {
                    toast(payload);
                });

                for (const message of props.initialMessages) {
                    toast(message);
                }
            });

            return {
                additionalTitle,
                autoHide,
                body,
                bsToast,
                delay,
                getIcon,
                title,
                toast,
                variant,
            };
        },
    };

</script>
