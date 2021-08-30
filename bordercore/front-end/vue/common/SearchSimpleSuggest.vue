<template>
    <div>
        <form id="top-search-form" class="form-inline" method="get">
            <span v-if="searchFilter" class="pr-2">Filter:
                <span id="top-search-filter-type">
                    {{ searchFilter }}
                </span>
            </span>
            <div class="form-row">
                <div id="top-search-container" class="col-auto has-search">
                    <font-awesome-icon icon="search" class="text-dark" />

                    <vue-simple-suggest id="top-simple-suggest"
                                        ref="suggestComponent"
                                        v-model="query"
                                        :accesskey="accesskey"
                                        :display-attribute="displayAttribute"
                                        :value-attribute="valueAttribute"
                                        :list="search"
                                        :filter-by-query="false"
                                        :debounce="200"
                                        :min-length="2"
                                        :max-suggestions="maxSuggestions"
                                        placeholder="Search"
                                        autocomplete="off"
                                        name="search"
                                        :styles="autoCompleteStyle"
                                        @keydown.native="onKeyDown"
                                        @select="select"
                                        @keydown.native.enter.prevent="onEnter"
                                        @blur="onBlur"
                    >
                        <div slot="suggestion-item" slot-scope="scope">
                            <!-- @*event*.stop="" handlers are needed to prevent the splitter from being selected -->
                            <span v-if="scope.suggestion.splitter"
                                  class="top-search-splitter"
                                  @click.stop=""
                            >{{ scope.suggestion.name }}</span>
                            <span v-else class="top-search-suggestion">
                                <font-awesome-icon v-if="scope.suggestion.important === 10" icon="heart" class="text-danger mr-1" />
                                <span class="d-inline" v-html="boldenSuggestion(scope)" />
                            </span>
                        </div>
                    </vue-simple-suggest>
                </div>
            </div>
        </form>
    </div>
</template>

<script>

    import VueSimpleSuggest from "vue-simple-suggest";

    export default {
        components: {
            VueSimpleSuggest,
        },
        props: {
            accesskey: {
                type: String,
                default: null,
            },
            id: {
                type: String,
                default: "simple-suggest",
            },
            displayAttribute: {
                type: String,
                default: "value",
            },
            valueAttribute: {
                type: String,
                default: "value",
            },
            maxSuggestions: {
                default: 10,
                type: Number,
            },
            initialSearchType: {
                default: "",
                type: String,
            },
            suggestSearchUrl: {
                default: "",
                type: String,
            },
            querySearchUrl: {
                default: "",
                type: String,
            },
            noteQuerySearchUrl: {
                default: "",
                type: String,
            },
            drillQuerySearchUrl: {
                default: "",
                type: String,
            },
            storeInSessionUrl: {
                default: "",
                type: String,
            },
        },
        data() {
            return {
                query: "",
                autoCompleteStyle: {
                    vueSimpleSuggest: "position-relative",
                    inputWrapper: "",
                    defaultInput: "form-control search-box-input",
                    suggestions: "position-absolute list-group z-1000",
                    suggestItem: "list-group-item",
                },
                searchFilter: this.initialSearchType,
                searchUrl: this.suggestSearchUrl,
            };
        },
        methods: {
            search(query) {
                try {
                    const url = this.searchUrl;
                    return axios.get(url + query + "&filter=" + this.searchFilter.toLowerCase())
                        .then((response) => {
                            return response.data;
                        });
                } catch (error) {
                    console.log(`Error: ${error}`);
                }
            },
            boldenSuggestion(scope) {
                // If the parent provided a custom boldenSuggestion function, use that.
                //  Otherwise use this default code.
                if (typeof this.$parent.boldenSuggestion === "function") {
                    return this.$parent.boldenSuggestion(scope);
                }

                if (!scope) return scope;

                const {suggestion, query} = scope;

                const result = this.$refs.suggestComponent.displayProperty(suggestion);
                if (!suggestion.object_type) {
                    return result;
                }

                if (!query) return result;

                const texts = query.split(/[\s-_/\\|\.]/gm).filter((t) => !!t) || [""];

                const boldResult = result.replace(new RegExp("(.*?)(" + texts.join("|") + ")(.*?)", "gi"), "$1<b class='text-primary'>$2</b>$3");

                return ` <em class="top-search-object-type">${suggestion.object_type}</em> - ${boldResult}`;
            },
            select(datum) {
                window.location = datum.link;
            },
            onEnter(evt) {
                if (this.$refs.suggestComponent.hoveredIndex != -1) {
                    return;
                }

                const inputValue = document.getElementById("top-simple-suggest").value;
                if (inputValue === "") {
                    return;
                }

                const form = document.getElementById("top-search-form");

                if (this.searchFilter === "Note") {
                    form.action = this.noteQuerySearchUrl;
                } else if (this.searchFilter === "Bookmark") {
                    form.action = this.bookmarkQuerySearchUrl;
                } else if (this.searchFilter === "Drill") {
                    form.action = this.drillQuerySearchUrl;
                } else {
                    form.action = this.querySearchUrl;
                }

                form.submit();
            },
            onKeyDown(evt) {
                if (evt.code === "KeyN" && evt.altKey) {
                    this.handleFilter("Note");
                } else if (evt.code === "KeyL" && evt.altKey) {
                    this.handleFilter("Bookmark");
                } else if (evt.code === "KeyB" && evt.altKey) {
                    this.handleFilter("Book");
                } else if (evt.code === "KeyM" && evt.altKey) {
                    this.handleFilter("Music");
                    // Hack to prevent Chrome on OS X from submitting the form.
                    // I have no idea why this happens.
                    evt.preventDefault();
                } else if (evt.code === "KeyD" && evt.altKey) {
                    this.handleFilter("Drill");
                } else if (evt.key === "a" && evt.altKey) {
                    document.getElementById("top-simple-suggest").select();
                }
            },
            onBlur(evt) {
                this.$refs.suggestComponent.setText("");
            },
            handleFilter(objectType) {
                if (this.searchFilter === objectType) {
                    this.searchFilter = "";
                } else {
                    this.searchFilter = this.searchFilter === objectType ? "" : objectType;
                }
                this.saveSearchFilter(this.searchFilter);
                this.$refs.suggestComponent.research();
            },
            saveSearchFilter(searchFilter) {
                doPost(
                    this,
                    this.storeInSessionUrl,
                    {
                        "top_search_filter": searchFilter,
                    }
                    ,
                    (response) => {},
                    "",
                    "",
                );
            },
        },
    };

</script>
