<template>
    <div>
        <ul class="related-tags list-unstyled ms-2">
            <li v-for="tag in info" :key="tag.name" class="mt-3">
                <a class="tag" :href="startStudySessionTagUrl.replace('666', tag.tag_name)">
                    {{ tag.tag_name }}
                    <span class="count text-white">
                        {{ tag.count }}
                    </span>
                </a>
            </li>
        </ul>
        <div v-if="noRelatedTagsFound" class="text-primary m-3">
            No tags found
        </div>
    </div>
</template>

<script>

    export default {

        components: {
        },
        props: {
            relatedTagsUrl: {
                type: String,
                default: "",
            },
            startStudySessionTagUrl: {
                type: String,
                default: "",
            },
            tagName: {
                type: String,
                default: "",
            },
        },
        data() {
            return {
                info: [],
                noRelatedTagsFound: false,
            };
        },
        mounted() {
            doGet(
                this,
                `${this.relatedTagsUrl}?tag_name=${this.tagName}`,
                (response) => {
                    this.info = response.data.info;
                    if (response.data.info.length === 0) {
                        this.noRelatedTagsFound = true;
                    }
                },
                "Error getting related tags",
            );
        },
        methods: {
            addTag(tagName) {
                const tag = createTag(tagName, [tagName]);
                this.$refs.tagsInputComponent.addTag(tag);
            },
        },

    };

</script>
