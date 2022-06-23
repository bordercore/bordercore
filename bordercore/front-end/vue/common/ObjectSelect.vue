<template>
    <div :id="`modalObjectSelect${label}`" class="modal fade" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        Select Object
                    </h4>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" />
                </div>
                <div class="modal-body">
                    <div class="d-flex flex-column">
                        <form @submit.prevent>
                            <div class="search-with-doctypes">
                                <vue-simple-suggest
                                    id="object-search"
                                    ref="suggestComponent"
                                    v-model="query"
                                    accesskey="s"
                                    display-attribute="name"
                                    value-attribute="uuid"
                                    :list="search"
                                    name="search"
                                    :filter-by-query="true"
                                    :debounce="200"
                                    :min-length="2"
                                    :max-suggestions="maxSuggestions"
                                    placeholder="Search"
                                    autocomplete="off"
                                    autofocus="off"
                                    :styles="autoCompleteStyle"
                                    @select="select"
                                >
                                    <div slot="suggestion-item" slot-scope="scope">
                                        <!-- @*event*.stop="" handlers are needed to prevent the splitter from being selected -->
                                        <div v-if="scope.suggestion.splitter"
                                             class="top-search-splitter"
                                             @click.stop=""
                                        >
                                            {{ scope.suggestion.name }}
                                        </div>
                                        <div v-else class="object-select-suggestion d-flex">
                                            <div v-if="scope.suggestion.important === 10" class="me-1">
                                                <font-awesome-icon icon="heart" class="text-danger" />
                                            </div>
                                            <div v-if="scope.suggestion.cover_url" class="cover-image">
                                                <img class="mw-100" :src="scope.suggestion.cover_url">
                                            </div>
                                            <div v-else>
                                                {{ scope.suggestion.doctype }}
                                            </div>
                                            <div class="d-flex flex-column text-truncate">
                                                <div class="text-truncate ms-2" v-html="boldenSuggestion(scope)" />
                                                <div class="date ms-2">
                                                    {{ scope.suggestion.date }}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </vue-simple-suggest>
                            </div>
                        </form>
                        <div v-if="hasFilter" class="d-flex mt-2 ms-3">
                            <div>Filter:</div>
                            <div class="d-flex align-items-center ms-2">
                                <input class="object-select-filter" value="bookmarks" type="checkbox" @change="filter">
                                <label class="ms-2">Bookmarks</label>
                            </div>
                            <div class="d-flex align-items-center ms-3">
                                <input class="object-select-filter" value="blobs" type="checkbox" @change="filter">
                                <label class="ms-2">Blobs</label>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>

    import VueSimpleSuggest from "vue-simple-suggest";

    export default {

        components: {
            VueSimpleSuggest,
        },
        props: {
            hasFilter: {
                type: Boolean,
                default: true,
            },
            initialDoctypes: {
                type: Array,
                default: () => [],
            },
            label: {
                type: String,
                default: "",
            },
            maxSuggestions: {
                type: Number,
                default: 10,
            },
            searchObjectUrl: {
                default: "",
                type: String,
            },
        },
        data() {
            return {
                name: "",
                doctypes: ["blob", "book", "bookmark", "document", "note"],
                callback: null,
                objectSelectFilter: [],
                returnArgs: null,
                query: "",
                autoCompleteStyle: {
                    vueSimpleSuggest: "position-relative",
                    inputWrapper: "",
                    defaultInput: "form-control search-box-input",
                    suggestions: "position-absolute list-group z-1000",
                    suggestItem: "list-group-item",
                },
            };
        },
        mounted() {
            if (this.initialDoctypes) {
                this.doctypes = this.initialDoctypes;
            }
        },
        methods: {
            boldenSuggestion(scope) {
                // If the parent provided a custom boldenSuggestion function, use that.
                //  Otherwise use this default code.
                if (typeof this.$parent.boldenSuggestion === "function") {
                    return this.$parent.boldenSuggestion(scope);
                }

                if (!scope) return scope;

                const {suggestion, query} = scope;

                let result = this.$refs.suggestComponent.displayProperty(suggestion);

                if (!query) return result;

                const texts = query.split(/[\s-_/\\|\.]/gm).filter((t) => !!t) || [""];
                return result.replace(new RegExp("(.*?)(" + texts.join("|") + ")(.*?)", "gi"), "$1<b class='matched'>$2</b>$3");
            },
            filter(evt, foo) {
                this.objectSelectFilter = evt.target.value;

                if (this.objectSelectFilter === "blobs") {
                    this.doctypes = ["blob", "book", "document", "note"];
                } else {
                    this.doctypes = ["bookmark"];
                }

                document.querySelectorAll(".object-select-filter").forEach(function(checkbox) {
                    if (checkbox.value !== evt.target.value) {
                        checkbox.checked = false;
                    }
                });
            },
            search(query) {
                try {
                    return axios.get(this.getSearchObjectUrl(query))
                                .then((response) => {
                                    return response.data;
                                });
                } catch (error) {
                    console.log(`Error: ${error}`);
                }
            },
            getSearchObjectUrl(query) {
                let url = this.searchObjectUrl;
                url += "?doc_type=" + this.doctypes.join(",");
                url += "&term=" + query;
                return url;
            },
            openModal(callback, returnArgs) {
                this.callback = callback;
                this.returnArgs = returnArgs;
                const modal = new Modal(`#modalObjectSelect${this.label}`);
                modal.show();
                setTimeout( () => {
                    this.$refs.suggestComponent.input.focus();
                }, 500);
            },
            select(selection) {
                // The parent component receives the selected object info
                this.$emit("select-object", selection, this.callback, this.returnArgs);

                const modal = Modal.getInstance(document.getElementById(`modalObjectSelect${this.label}`));
                modal.hide();

                this.$nextTick(() => {
                    this.$refs.suggestComponent.$el.querySelector("input").blur();
                    this.$refs.suggestComponent.setText("");
                    this.$refs.suggestComponent.clearSuggestions();
                });
            },
        },

    };

</script>
