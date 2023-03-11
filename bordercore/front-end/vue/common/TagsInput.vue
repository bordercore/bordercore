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
            @search:blur="onBlur"
            @search:focus="onFocus"
        >
            <template #no-options="{ search, searching }">
                <div v-if="notFound">
                    No tags found!
                </div>
            </template>
            <template #open-indicator="{ attributes }">
                <div class="vs__open-indicator me-2">
                    <font-awesome-icon icon="angle-down" class="align-middle" />
                </div>
            </template>
        </v-select>
        <input type="hidden" :name="name" :value="tagsCommaSeparated">
    </div>
</template>

<script>

    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";
    import vSelect from "vue-select";

    export default {

        components: {
            FontAwesomeIcon,
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
        emits: [
            "blur",
            "focus",
            "option:created",
            "tags-changed",
        ],
        setup(props, ctx) {
            const notFound = ref(false);
            const options = ref([]);
            const tags = ref([]);

            const tagsInputComponent = ref(null);

            function addTag(tagName) {
                tags.value.push({"label": tagName});
            };

            function createTag(tagName, foo) {
                const newTag = {label: tagName};
                ctx.emit("option:created", newTag);
                return newTag;
            };

            function fetchOptions(search, loading) {
                // Set a minimum character count to trigger the ajax call
                if (search.length < 3) return;

                return doGet(
                    props.searchUrl + search,
                    (response) => {
                        options.value = response.data.map((a) => {
                            return {label: a.label};
                        });
                    },
                );
            };

            function onBlur(evt) {
                ctx.emit("blur", evt);
            };

            function onFocus(evt) {
                ctx.emit("focus", evt);
            };

            function tagsChanged() {
                // Enforce lowercase for all tag names
                tags.value.forEach(function(element, index, tagList) {
                    tagList[index] = {
                        "label": element.label.toLowerCase(),
                    };
                });

                ctx.emit("tags-changed", tags.value.map( (x) => x.label ));
                options.value = [];
                nextTick(() => {
                    tagsInputComponent.value.$refs.search.focus();
                });
            };

            const tagsCommaSeparated = computed(() => {
                return tags.value.map((x) => x.label).join(",");
            });

            onMounted(() => {
                // The initial set of tags can either be passed in via an event
                //  or read from the DOM, depending on the value of the prop
                //  "getTagsFromEvent".

                if (props.getTagsFromEvent) {
                    EventBus.$on("addTags", (payload) => {
                        tags.value = payload.map( (x) => ({label: x}) );
                    });
                } else {
                    const initialTags = JSON.parse(document.getElementById("initial-tags").textContent);
                    if (initialTags) {
                        tags.value = initialTags.map( (x) => ({label: x}) );
                    }
                }

                if (props.autofocus) {
                    tagsInputComponent.value.$refs.search.focus();
                }
            });

            return {
                addTag,
                createTag,
                fetchOptions,
                onBlur,
                onFocus,
                options,
                notFound,
                tags,
                tagsChanged,
                tagsCommaSeparated,
                tagsInputComponent,
            };
        },
    };

</script>
