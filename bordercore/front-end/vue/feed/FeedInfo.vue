<template>
    <card title="" class="backdrop-filter">
        <template #title-slot>
            <div class="d-flex">
                <h3>Feed Info</h3>
            </div>
            <hr>
        </template>
        <template #content>
            <div>
                <strong>Updated</strong>: {{ store.state.currentFeed.lastCheck }}
            </div>
            <div>
                <strong>Status</strong>: <font-awesome-icon class="ms-1" :class="status.class" :icon="status.font" />
            </div>
            <div class="mt-3">
                <button class="btn btn-primary" @click="onCreateFeed">
                    Add Feed
                </button>
            </div>
        </template>
    </card>
</template>

<script>

    import store from "./store.js";

    import Card from "/front-end/vue/common/Card.vue";
    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

    export default {
        components: {
            Card,
            FontAwesomeIcon,
        },
        props: {
            title: {
                default: "Card Title",
                type: String,
            },
        },
        emits: ["create-feed"],
        setup(props, ctx) {
            const status = computed(() => {
                if (store.state.currentFeed.lastResponse === "OK") {
                    return {
                        "class": "text-success",
                        "font": "check",
                    };
                } else {
                    return {
                        "class": "text-danger",
                        "font": "exclamation-triangle",
                    };
                }
            });

            function onCreateFeed() {
                ctx.emit("create-feed");
            }

            function showFeed(feed) {
                store.commit("updateCurrentFeed", feed);
            };

            return {
                onCreateFeed,
                showFeed,
                status,
                store,
            };
        },
    };

</script>
