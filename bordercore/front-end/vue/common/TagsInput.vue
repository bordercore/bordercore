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
                tags.value.push({"label": tagName, "value": tagName});
            };

            function createTag(tagName) {
                const newTag = {"label": tagName, "value": tagName};
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
                            return {
                                "label": a.label,
                                "value": a.value ? a.value : a.label,
                            };
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

            function setTags(tagList) {
                tags.value = tagList.map( (x) => ({"label": x, "value": x}) );
            };

            function tagsChanged() {
                // Enforce lowercase for all tag names
                tags.value.forEach(function(element, index, tagList) {
                    tagList[index] = {
                        "label": element.label.toLowerCase(),
                        "value": element.value.toLowerCase(),
                    };
                });

                ctx.emit("tags-changed", tags.value.map( (x) => x.value ));
                options.value = [];
                nextTick(() => {
                    tagsInputComponent.value.$refs.search.focus();
                });
            };

            const tagsCommaSeparated = computed(() => {
                return tags.value.map((x) => x.value).join(",");
            });

            onMounted(() => {
                const initialTags = document.getElementById("initial-tags");
                if (initialTags) {
                    const tagsJson = JSON.parse(initialTags.textContent);
                    if (Array.isArray(tagsJson)) {
                        tags.value = tagsJson.map( (x) => ({"label": x, "value": x}) );
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
                setTags,
                tags,
                tagsChanged,
                tagsCommaSeparated,
                tagsInputComponent,
            };
        },
    };

</script>
