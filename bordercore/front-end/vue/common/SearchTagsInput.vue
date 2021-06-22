<script>

    import TagsInput from "./TagsInput.vue";

    export default {

        extends: TagsInput,
        props: {
            tagsChangedUrl: {
                default: "",
                type: String,
            },
        },
        methods: {
            tagsChanged(newTags) {
                const tags = newTags.map((x) => x.value).join(",");
                window.location = this.tagsChangedUrl.replace("666", tags);
            },
        },

    };

</script>
