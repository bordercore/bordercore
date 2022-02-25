<template>
    <div>
        <vue-tags-input
            ref="tagsInputComponent"
            v-model="tag"
            :tags="tags"
            :autocomplete-items="filteredItems"
            :autofocus="autofocus"
            :add-only-from-autocomplete="false"
            :placeholder="placeHolder"
            :disabled="disabled"
            :max-tags="maxTags"
            @tags-changed="tagsChanged"
        >
            <div slot="autocomplete-item" slot-scope="scope" @click="scope.performAdd(scope.item)">
                <div v-if="scope.item.display">
                    {{ scope.item.display }}
                </div>
                <div v-else>
                    {{ scope.item.text }}
                </div>
            </div>
        </vue-tags-input>
        <input type="hidden" :name="name" :value="tagsCommaSeparated">
    </div>
</template>

<script>

    import VueTagsInput from "@johmun/vue-tags-input";

    export default {

        components: {
            VueTagsInput,
        },
        props: {
            autofocus: {
                type: Boolean,
                default: false,
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
                tag: "",
                tags: [],
                autocompleteItems: [],
            };
        },
        computed: {
            tagsCommaSeparated: function() {
                return this.tags.map((x) => x.text).join(",");
            },
            filteredItems() {
                return this.autocompleteItems.filter((i) => {
                    return i.text.toLowerCase().indexOf(this.tag.toLowerCase()) !== -1;
                });
            },
        },
        watch: {
            "tag": "initItems",
        },
        mounted() {
            // The initial set of tags can either be passed in via an event
            //  or read from the DOM, depending on the value of the prop
            //  "getTagsFromEvent".

            if (this.getTagsFromEvent) {
                EventBus.$on("addTags", (payload) => {
                    this.tags = payload;
                });
            } else {
                const initialTags = JSON.parse(document.getElementById("initial-tags").textContent);
                if (initialTags) {
                    this.tags = initialTags;
                }
            }
        },
        methods: {
            tagsChanged(newTags) {
                this.tags = newTags;
                // Re-emit this event in case a parent component is interested
                this.$emit("tags-changed", newTags);
            },
            initItems() {
                // Set a minimum character count to trigger the ajax call
                if (this.tag.length < 3) return;

                return doGet(
                    this,
                    this.searchUrl + this.tag,
                    (response) => {
                        this.autocompleteItems = response.data.map((a) => {
                            return {text: a.text, display: a.display};
                        });
                    },
                    "",
                );
            },
        },

    };

</script>
