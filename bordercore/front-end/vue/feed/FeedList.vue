<template>
    <ul>
        <draggable v-model="localFeedList" animation="500" item-key="id" draggable=".draggable" chosen-class="feed-draggable" ghost-class="feed-draggable" drag-class="feed-draggable" @change="handleSort">
            <template #item="{element}">
                <li v-cloak :key="element.id" :class="{'selected rounded-sm': element.id === $store.state.currentFeed.id}" class="draggable ps-2">
                    <a href="#" :data-id="element.id" @click.prevent="onClick(element)">
                        {{ element.name }}
                    </a>
                    <small v-if="element.lastResponse !== 'OK'" class="text-danger">{{ element.lastResponse }}</small>
                </li>
            </template>
        </draggable>
        <div v-if="feedList.length === 0" v-cloak class="text-secondary">
            No feeds found. <a href="#" @click.prevent="handleUpdateFeed('Update')">Add one here.</a>
        </div>
    </ul>
</template>

<script>

    import draggable from "vuedraggable";

    export default {
        components: {
            draggable,
        },
        props: {
            feedList: {
                default: () => [],
                type: Array,
            },
            feedSortUrl: {
                default: "",
                type: String,
            },
            storeInSessionUrl: {
                default: "",
                type: String,
            },
        },
        setup(props) {
            const store = useStore();
            const localFeedList = ref(props.feedList.slice());

            function handleSort(evt) {
                const feedId = evt.moved.element.id;

                // The backend expects the ordering to begin
                // with 1, not 0, so add 1.
                const newPosition = evt.moved.newIndex + 1;

                doPost(
                    props.feedSortUrl,
                    {
                        "feed_id": feedId,
                        "position": newPosition,
                    },
                    () => {},
                );
            }

            function onClick(feed) {
                EventBus.$emit("showFeed", feed);

                doPost(
                    props.storeInSessionUrl,
                    {
                        "current_feed": feed.id,
                    },
                    (response) => {},
                    "",
                    "",
                );
            }

            onMounted(() => {
                EventBus.$on("deleteFeed", (feedUuid) => {
                    for (i = 0; i < feedList.length; i++) {
                        if (feedList[i].uuid == feedUuid) {
                            feedList.splice(i, 1);
                        }
                    }

                    // Now that the current feed is deleted, we need to select a
                    //  different current feed. Select the first in the list.
                    store.commit("updateCurrentFeed", feedList[0]);
                });

                EventBus.$on("addFeed", (feedInfo) => {
                    feedList.unshift(feedInfo);
                });
            });

            return {
                handleSort,
                localFeedList,
                onClick,
            };
        },
    };

</script>
