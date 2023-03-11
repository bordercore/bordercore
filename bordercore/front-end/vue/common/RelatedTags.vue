<template>
    <transition name="fade">
        <card v-if="tagList.length > 0" class="backdrop-filter">
            <template #title-slot>
                <div class="d-flex">
                    <div class="card-title d-flex">
                        <font-awesome-icon icon="tags" class="text-primary me-3 mt-1" />Related Tags
                    </div>
                </div>
            </template>

            <template #content>
                <div v-for="tagInfo in tagList" :key="tagInfo.name">
                    <hr class="divider">
                    <h5 class="text-success">
                        {{ tagInfo.name }}
                    </h5>
                    <ul class="related-tags list-unstyled text-truncate ms-2 pb-1">
                        <li v-for="tag in tagInfo.related" :key="tag.name" class="mt-3" @click="handleTagClick(tag.tag_name)">
                            <span class="tag">{{ tag.tag_name }}</span>
                            <span class="count text-white ms-1">
                                {{ tag.count }}
                            </span>
                        </li>
                    </ul>
                </div>
            </template>
        </card>
    </transition>
</template>

<script>

    import Card from "/front-end/vue/common/Card.vue";
    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

    export default {
        components: {
            Card,
            FontAwesomeIcon,
        },
        props: {
            relatedTagsUrl: {
                type: String,
                default: "",
            },
            docType: {
                type: String,
                default: "",
            },
            initialTags: {
                type: Array,
                default: () => [],
            },
        },
        emits: ["click-tag"],
        setup(props, ctx) {
            const tagList = ref([]);

            function getTagInfo(tags) {
                tagList.value = [];
                for (const tag of tags) {
                    doGet(
                        `${props.relatedTagsUrl}?tag_name=${tag}&doc_type=${props.docType}`,
                        (response) => {
                            if (response.data.info.length > 0) {
                                tagList.value.push(
                                    {
                                        "name": tag,
                                        "related": response.data.info,
                                    },
                                );
                            }
                        },
                        "Error getting related tags",
                    );
                }
            };

            function handleTagClick(tag) {
                ctx.emit("click-tag", tag);
            };

            function setTags(tags) {
                getTagInfo(tags);
            };

            onMounted(() => {
                if (props.initialTags) {
                    getTagInfo(props.initialTags);
                }
            });

            return {
                handleTagClick,
                tagList,
                setTags,
            };
        },
    };

</script>
