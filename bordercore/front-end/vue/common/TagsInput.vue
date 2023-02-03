<template>
    <div :class="classList">
        <v-select
            ref="tagsInputComponent"
            v-model="tags"
            multiple
            taggable
            :autofocus="autofocus"
            :placeholder="placeHolder"
            :options="options"
            :dropdown-should-open="({search, open}) => open && search.length > 2"
            :disabled="disabled"
            :create-option="createTag"
            :selectable="() => maxTags ? tags.length < maxTags : true"
            @search="fetchOptions"
            @option:selected="tagsChanged"
            @option:deselected="tagsChanged"
            @blur="onBlur"
            @focus="onFocus"
        >
            <template #no-options="{ search, searching }">
                <div v-if="notFound">
                    No tags found!
                </div>
            </template>
        </v-select>
        <input type="hidden" :name="name" :value="tagsCommaSeparated">
    </div>
</template>

<script>

    import vSelect from "vue-select";

    export default {

        components: {
            vSelect,
        },
        props: {
            autofocus: {
                type: Boolean,
                default: false,
            },
            classList: {
                type: String,
                default: "w-100",
            },
            searchUrl: {
                default: "search-url",
                type: String,
            },
            getTagsFromEvent: {
                default: false,
                type: Boolean,
            },
            name: {
                default: "tags",
                type: String,
            },
            placeHolder: {
                default: "",
                type: String,
            },
            disabled: {
                default: false,
                type: Boolean,
            },
            maxTags: {
                default: undefined,
                type: Number,
            },
        },
        data() {
            return {
                tags: [],
                options: [],
                notFound: false,
            };
        },
        computed: {
            tagsCommaSeparated: function() {
                return this.tags.map((x) => x.label).join(",");
            },
        },
        mounted() {
            // The initial set of tags can either be passed in via an event
            //  or read from the DOM, depending on the value of the prop
            //  "getTagsFromEvent".

            if (this.getTagsFromEvent) {
                EventBus.$on("addTags", (payload) => {
                    this.tags = payload.map( (x) => ({label: x}) );
                });
            } else {
                const initialTags = JSON.parse(document.getElementById("initial-tags").textContent);
                if (initialTags) {
                    this.tags = initialTags.map( (x) => ({label: x}) );
                }
            }

            if (this.autofocus) {
                this.$refs.tagsInputComponent.$refs.search.focus();
            }
        },
        methods: {
            addTag(tagName) {
                this.tags.push({"label": tagName});
            },
            createTag(tagName, foo) {
                const newTag = {label: tagName};
                this.$emit("option:created", newTag);
                return newTag;
            },
            tagsChanged() {
                // Re-emit this event in case a parent component is interested
                this.$emit("tags-changed", this.tags.map( (x) => x.label ));
                this.options = [];
            },
            fetchOptions(search, loading) {
                // Set a minimum character count to trigger the ajax call
                if (search.length < 3) return;

                return doGet(
                    this,
                    this.searchUrl + search,
                    (response) => {
                        this.options = response.data.map((a) => {
                            return {label: a.label};
                        });
                    },
                    "",
                );
            },
            onBlur(evt) {
                this.$emit("blur", evt);
            },
            onFocus(evt) {
                this.$emit("focus", evt);
            },
        },

    };

</script>
