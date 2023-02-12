<template>
    <ul>
        <draggable v-model="localFeedList" animation="500" item-key="id" @change="onChange">
            <template #item="{element}">
                <li v-for="feed in {element}" v-cloak :key="feed.id" :class="getFeedClass(feed)" class="ps-2">
                    <a href="#" :data-id="feed.id" @click.prevent="onClick(feed)">
                        {{ feed.name }}
                    </a>
                    <small v-if="feed.lastResponse !== 'OK'" class="text-danger">{{ feed.lastResponse }}</small>
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
            const localFeedList = props.feedList.slice();

            function getFeedClass(feed) {
                if (feed === store.state.currentFeed) {
                    return "selected rounded-sm";
                }
            }

            function onChange(evt) {
                const feedId = evt.moved.element.id;

                // The backend expects the ordering to begin
                // with 1, not 0, so add 1.
                newPosition = evt.moved.newIndex + 1;

                const bodyFormData = new URLSearchParams();
                bodyFormData.append("feed_id", feedId);
                bodyFormData.append("position", newPosition);

                axios(props.feedSortUrl, {
                    method: "POST",
                    data: bodyFormData,
                });
            }

            function onClick(feed) {
                EventBus.$emit("showFeed", feed);

                doPost(
                    null,
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
                getFeedClass,
                localFeedList,
                onChange,
                onClick,
            };
        },
    };

</script>
