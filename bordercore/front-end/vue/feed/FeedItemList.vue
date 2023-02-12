<template>
    <div class="card-body backdrop-filter h-100 me-2">
        <div class="d-flex">
            <h3 v-cloak id="feed-title">
                <a :href="$store.state.currentFeed.homepage">{{ $store.state.currentFeed.name }}</a>
            </h3>
            <drop-down-menu ref="dropDownMenu" :links="feedDetailMenuItems" />
        </div>
        <hr>
        <ul>
            <li v-for="url in $store.state.currentFeed.feedItems" v-cloak :key="url.id">
                <a :href="url.link">{{ url.title }}</a>
            </li>
            <div v-if="$store.state.currentFeed.feedItems?.length == 0">
                No feed items found.
            </div>
        </ul>
    </div>
</template>

<script>

    import DropDownMenu from "/front-end/vue/common/DropDownMenu.vue";

    export default {
        components: {
            DropDownMenu,
        },
        emits: ["open-modal"],
        setup(props, ctx) {
            const store = useStore();

            const feedDetailMenuItems = [
                {
                    id: uuidv4(),
                    title: "Update Feed",
                    url: "#",
                    clickHandler: handleUpdateFeed,
                    icon: "pencil-alt",
                },
                {
                    id: uuidv4(),
                    title: "Delete Feed",
                    url: "#",
                    clickHandler: handleDeleteFeed,
                    icon: "times",
                },
            ];

            function handleUpdateFeed(evt, action = "Update") {
                // this.$parent.$refs.updateFeed.setAction(action);
                if (action === "Update") {
                    ctx.emit("open-modal", action, store.state.currentFeed);
                    // this.$parent.$refs.updateFeed.feedInfo = this.$store.state.currentFeed;
                } else {
                    ctx.emit("open-modal", action, {});
                    // this.$parent.$refs.updateFeed.feedInfo = {};
                }
                /* const modal = new Modal("#modalUpdateFeed");
                 * modal.show(); */
            }

            function handleDeleteFeed() {
                const modal = new Modal("#modalDeleteFeed");
                modal.show();
            }

            onMounted(() => {
                EventBus.$on("showFeed", (feed) => {
                    store.state.currentFeed = feed;
                });

                EventBus.$on("createFeed", () => {
                    handleUpdateFeed(null, "Create");
                });
            });

            return {
                feedDetailMenuItems,
                handleUpdateFeed,
                handleDeleteFeed,
            };
        },
    };

</script>
