<template>
    <div>
        <vue-tags-input
            ref="tagsInputComponent"
            v-model="tag"
            :tags="tags"
            @tags-changed=tagsChanged
            :autocomplete-items="filteredItems"
            :add-only-from-autocomplete="false"
            placeholder="">
            <div slot="autocomplete-item" slot-scope="scope" @click="scope.performAdd(scope.item)">
                <div>{{ scope.item.text }}</div>
            </div>
        </vue-tags-input>
        <input type="hidden" :name="name" :value="tagsCommaSeparated" />
    </div>
</template>

<script>

    import Vue from "vue";
    import VueTagsInput from "@johmun/vue-tags-input";

    export default {

        props: {
            searchUrl: {
                default: "search-url",
                type: String
            },
            getTagsFromEvent: {
                default: false,
                type: Boolean
            },
            name: {
                default: "tags",
                type: String
            }
        },
        data() {
            return {
                tag: "",
                tags: [],
                autocompleteItems: [],
            }
        },
        watch: {
            "tag": "initItems",
        },
        methods: {
            tagsChanged(newTags) {
                this.tags = newTags;
            },
            initItems() {

                // Set a minimum character count to trigger the ajax call
                if (this.tag.length < 3) return;

                return doGet(
                    this,
                    this.searchUrl + this.tag,
                    (response) => {
                        this.autocompleteItems = response.data.map(a => {
                            return { text: a.text, value: a.value };
                        })
                    },
                    ""
                );

            },
        },
        mounted() {

            // The initial set of tags can either be passed in via an event
            //  or read from the DOM, depending on the value of the prop
            //  "getTagsFromEvent".

            if (this.getTagsFromEvent) {

                EventBus.$on("addTags", payload => {
                    this.tags = payload;
                });

            } else {

                const initialTags = JSON.parse(document.getElementById("initial-tags").textContent);
                if (initialTags) {
                    this.tags = initialTags;
                }

            }

        },
        computed: {
            tagsCommaSeparated: function() {
                // Be sure to use the 'text' field rather than 'value'.
                //  The 'value' field only exists for existing tags that
                //  are added by autocomplete, not new tags typed in
                //  by the user.
                return this.tags.map(x => x.text).join(",")
            },
            filteredItems() {
                return this.autocompleteItems.filter(i => {
                    return i.text.toLowerCase().indexOf(this.tag.toLowerCase()) !== -1;
                });
            }
        },
        components: {
            VueTagsInput
        }

    };

</script>
