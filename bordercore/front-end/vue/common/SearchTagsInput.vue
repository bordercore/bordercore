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
            tagsChanged() {
                window.location = this.tagsChangedUrl.replace("666", this.tagsCommaSeparated);
            },
        },

    };

</script>
