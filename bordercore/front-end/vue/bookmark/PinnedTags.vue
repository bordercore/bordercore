<template>
    <div class="card-body backdrop-filter h-100">
        <div class="card-title-large">
            Pinned Tags
        </div>
        <hr class="divider">
        <ul v-cloak class="list-group flex-column w-100">
            <div id="tag-list">
                <draggable v-model="tags" item-key="id" :component-data="{type:'transtion-group'}" @change="onSortTags">
                    <template #item="{element}">
                        <li
                            :key="element.id"
                            class="list-with-counts rounded d-flex ps-2 py-1 pr-1"
                            :class="{ 'selected': element.name === selectedTagName, draggable: element.isDraggable }"
                            :data-tag="element.name"
                            :data-id="element.id"
                            @click.prevent="onClickTag"
                            @dragover="onDragOverTag($event)"
                            @dragleave="onDragLeaveTag($event)"
                            @drop="onAddTagToBookmark($event, element)"
                        >
                            <div class="ps-2 text-truncate">
                                {{ element.name }}
                            </div>
                            <div v-if="element.bookmark_count" class="ms-auto pe-2">
                                <span class="px-2 badge rounded-pill">
                                    {{ element.bookmark_count }}
                                </span>
                            </div>
                        </li>
                    </template>
                </draggable>
            </div>
        </ul>
    </div>
</template>

<script>

    import draggable from "vuedraggable";

    export default {
        components: {
            draggable,
        },
        props: {
            addTagUrl: {
                type: String,
                default: "",
            },
            removeTagUrl: {
                type: String,
                default: "",
            },
            sortTagsUrl: {
                type: String,
                default: "",
            },
        },
        emits: ["getPage", "searchTag"],
        setup(props, ctx) {
            const selectedTagName = ref("Untagged");
            const tags = ref([]);

            function setTags(tagsParam, untaggedCount) {
                tags.value = tagsParam;
                tags.value.unshift(
                    {
                        id: -1,
                        name: "Untagged",
                        isDraggable: false,
                        count: untaggedCount,
                    },
                );
            };

            function onClickTag(evt) {
                const tagName = evt.currentTarget.dataset.tag;
                ctx.emit("searchTag", tagName);
            };

            function onDragOverTag(evt) {
                evt.currentTarget.classList.add("hover-tag");
            };

            function onDragLeaveTag(evt) {
                evt.currentTarget.classList.remove("hover-tag");
            };

            function onAddTagToBookmark(evt, tag) {
                evt.currentTarget.classList.remove("hover-tag");

                // Ignore if we're dragging a bookmark from a tag list
                //  onto the same tag.
                if (tag.name === selectedTagName.value) {
                    return;
                }

                const bookmarkUuid = evt.dataTransfer.getData("application/x-moz-node");

                // Ignore if we're sorting the tag list instead of
                //  dragging a bookmark onto a tag (both events
                //  will trigger this handler). That will be taken
                //  care of in another handler.
                if (!bookmarkUuid) {
                    return;
                }

                if (tag.id === -1) {
                    // We're moving a bookmark from a tagged category to the 'Untagged' category,
                    //  which means we need to remove that tag from the bookmark.
                    doPost(
                        props.removeTagUrl,
                        {
                            "tag_name": selectedTagName.value,
                            "bookmark_uuid": bookmarkUuid,
                        },
                        (response) => {
                            ctx.emit("searchTag", selectedTagName.value);
                        },
                        "",
                        "Error removing tag",
                    );
                } else {
                    doPost(
                        props.addTagUrl,
                        {
                            "tag_id": tag.id,
                            "bookmark_uuid": bookmarkUuid,
                        },
                        (response) => {
                            ctx.emit("getPage", 1);
                        },
                        "",
                        "Error adding tag",
                    );
                }
            };

            function onSortTags(evt) {
                if (evt.added) {
                    return;
                }
                const tagId = evt.moved.element.id;

                doPost(
                    props.sortTagsUrl,
                    {
                        "tag_id": tagId,
                        "new_position": evt.moved.newIndex,
                    },
                    () => {},
                    "",
                    "Error sorting tags",
                );
            };

            return {
                onClickTag,
                onDragOverTag,
                onDragLeaveTag,
                onAddTagToBookmark,
                onSortTags,
                selectedTagName,
                setTags,
                tags,
            };
        },
    };

</script>
