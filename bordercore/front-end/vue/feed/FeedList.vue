<template>
    <ul>
        <draggable v-model="localFeedList" animation="500" item-key="id" draggable=".draggable" chosen-class="feed-draggable" ghost-class="feed-draggable" drag-class="feed-draggable" @change="handleSort">
            <template #item="{element}">
                <li v-cloak :key="element.id" :class="{'selected rounded-sm': element.id === $store.state.currentFeed.id}" class="draggable ps-2">
                    <a href="#" :data-id="element.id" @click.prevent="onClick(element)">
                        {{ element.name }}
                    </a>
                    <small v-if="element.lastResponse !== 'OK'" class="text-danger ms-2">{{ element.lastResponse }}</small>
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
        emits: ["show-feed"],
        setup(props, ctx) {
            const store = useStore();
            const localFeedList = ref(props.feedList.slice());

            function deleteFeed(feedUuid) {
                for (const i = 0; i < localFeedList.value.length; i++) {
                    if (localFeedList.value[i].uuid == feedUuid) {
                        localFeedList.value.splice(i, 1);
                    }
                }

                // Now that the current feed is deleted, we need to select a
                //  different current feed. Select the first in the list.
                store.commit("updateCurrentFeed", localFeedList.value[0]);
            };

            function addFeed(feedInfo) {
                localFeedList.value.unshift(feedInfo);
            };

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
                ctx.emit("show-feed", feed);

                doPost(
                    props.storeInSessionUrl,
                    {
                        "current_feed": feed.id,
                    },
                    (response) => {},
                );
            }

            return {
                addFeed,
                deleteFeed,
                handleSort,
                localFeedList,
                onClick,
            };
        },
    };

</script>
