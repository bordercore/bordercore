<template>
    <transition name="fade">
        <card v-if="info.length > 0" class="backdrop-filter">
            <template #title-slot>
                <div class="d-flex">
                    <div class="card-title d-flex">
                        <font-awesome-icon icon="tags" class="text-primary me-3 mt-1" />Related Tags
                    </div>
                </div>
            </template>

            <template #content>
                <div v-for="tagInfo in info" :key="tagInfo.name">
                    <hr class="divider">
                    <h5 class="text-success">
                        {{ tagInfo.name }}
                    </h5>
                    <ul class="related-tags list-unstyled text-truncate ms-2 pb-1">
                        <li v-for="tag in tagInfo.related" :key="tag.name" class="mt-3" @click="onClickTag(tag.tag_name)">
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

    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

    export default {
        components: {
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
        data() {
            return {
                info: [],
            };
        },
        mounted() {
            if (this.initialTags) {
                this.getTagInfo(this.initialTags);
            }
        },
        methods: {
            getTagInfo(tags) {
                this.info = [];
                for (const tag of tags) {
                    doGet(
                        this,
                        `${this.relatedTagsUrl}?tag_name=${tag}&doc_type=${this.docType}`,
                        (response) => {
                            if (response.data.info.length > 0) {
                                this.info.push({"name": tag, "related": response.data.info});
                            }
                        },
                        "Error getting related tags",
                    );
                }
            },
            onClickTag(tag) {
                this.$emit("click-tag", tag);
            },
            setTags(tags) {
                this.getTagInfo(tags);
            },
        },

    };

</script>
