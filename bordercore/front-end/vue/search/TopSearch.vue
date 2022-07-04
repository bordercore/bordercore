<template>
    <Transition name="fade">
        <div v-if="showSearchWindow" id="top-search">
            <form class="form-inline" method="get">
                <input type="hidden" name="doctype" :value="searchFilter">
                <div class="form-row">
                    <div class="search-with-doctypes has-search me-1">
                        <font-awesome-icon icon="search" />

                        <vue-simple-suggest id="top-simple-suggest"
                                            ref="suggestComponent"
                                            v-model="query"
                                            accesskey="s"
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
                        >
                            <div slot="suggestion-item" slot-scope="scope">
                                <!-- @*event*.stop="" handlers are needed to prevent the splitter from being selected -->
                                <span v-if="scope.suggestion.splitter"
                                      class="top-search-splitter"
                                      @click.stop=""
                                >{{ scope.suggestion.name }}</span>
                                <div v-else class="top-search-suggestion">
                                    <span v-if="scope.suggestion.important === 10" class="me-1">
                                        <font-awesome-icon icon="heart" class="text-danger" />
                                    </span>
                                    <span class="d-inline" v-html="boldenSuggestion(scope)" />
                                </div>
                            </div>
                        </vue-simple-suggest>
                        <div v-if="searchFilter" id="top-search-filter" class="tag label label-info d-flex align-items-center">
                            <div>{{ getFilterName(searchFilter) }}</div>
                            <div>
                                <a class="ms-1" href="#" @click.prevent="removeFilter()">
                                    <font-awesome-icon icon="times" class="text-primary" />
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </form>
            <div v-if="query === ''" id="top-search-filter-options" class="ms-3 mt-2 p-3">
                <div class="text-primary mb-2">
                    <strong>Filter Options</strong>
                </div>
                <div class="d-flex flex-column">
                    <div v-for="filter in searchFilterTypes" :key="filter.icon" class="tag-list d-flex p-1" :class="getFilterClass(filter.doctype)" @click.prevent="handleFilter(filter.doctype)">
                        <div class="top-search-filter-icon d-flex justify-content-center align-items-center">
                            <font-awesome-icon class="me-2" :icon="filter.icon" />
                        </div>
                        <div>
                            {{ filter.name }}
                        </div>
                    </div>
                </div>
                <div class="recent-searches-header text-primary my-2 pt-2">
                    <strong>Recent Searches</strong>
                </div>
                <div class="d-flex flex-column">
                    <div v-for="recentSearch in recentSearches" :key="recentSearch.id" class="tag-list d-flex p-1" @click.prevent="handleRecentSearch(recentSearch)">
                        <div class="top-search-filter-icon d-flex justify-content-center align-items-center">
                            <font-awesome-icon class="me-2" icon="search" />
                        </div>
                        <div class="text-truncate">
                            {{ recentSearch.search_text }}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </Transition>
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
                default: "name",
            },
            valueAttribute: {
                type: String,
                default: "name",
            },
            maxSuggestions: {
                type: Number,
                default: 10,
            },
            initialSearchType: {
                type: String,
                default: "",
            },
            suggestSearchUrl: {
                type: String,
                default: "",
            },
            querySearchUrl: {
                type: String,
                default: "",
            },
            noteQuerySearchUrl: {
                type: String,
                default: "",
            },
            drillQuerySearchUrl: {
                type: String,
                default: "",
            },
            storeInSessionUrl: {
                type: String,
                default: "",
            },
            recentSearches: {
                type: Array,
                default: () => [],
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
                searchFilterTypes: [
                    {
                        "name": "Books",
                        "icon": "book",
                        "doctype": "book",
                    },
                    {
                        "name": "Bookmarks",
                        "icon": "bookmark",
                        "doctype": "bookmark",
                    },
                    {
                        "name": "Notes",
                        "icon": "sticky-note",
                        "doctype": "note",
                    },
                    {
                        "name": "Music",
                        "icon": "music",
                        "doctype": "music",
                    },
                    {
                        "name": "Drill Questions",
                        "icon": "graduation-cap",
                        "doctype": "drill",
                    },
                ],
                showSearchWindow: false,
            };
        },
        mounted() {
            const self = this;
            document.addEventListener("keydown", function(evt) {
                if (evt.key === "s" && evt.altKey) {
                    self.showSearchWindow = true;
                }
            } );

            // If a click was detected outside this component, *and*
            //  the click wasn't on the "Search icon", then hide the
            //  component.
            document.addEventListener("click", function(event) {
                const specifiedElement = document.getElementById("top-search");
                if (!specifiedElement) {
                    return;
                }
                const isClickInside = specifiedElement.contains(event.target) || specifiedElement.contains(event.target.parentElement);
                // We check for the search icon by looking for a click on the
                //  font-awesome 'svg' element, which has a custom 'top-search-target'
                //  class on it, or the containing 'path' element by looking for a 'svg'
                //  parent element with the same class.
                if (!isClickInside &&
                    !event.target.classList.contains("top-search-target") &&
                    !event.target.parentElement.classList.contains("top-search-target") &&
                    !event.target.classList.contains("fa-times") &&
                    !event.target.parentElement.classList.contains("fa-times")
                ) {
                    self.showSearchWindow = false;
                }
            });
        },
        methods: {
            search(query) {
                try {
                    const url = this.searchUrl;
                    return axios.get(url + query + "&doc_type=" + this.searchFilter.toLowerCase())
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
                if (!suggestion.doctype) {
                    return result;
                }

                if (!query) return result;

                const texts = query.split(/[\s-_/\\|\.]/gm).filter((t) => !!t) || [""];

                const boldResult = result.replace(new RegExp("(.*?)(" + texts.join("|") + ")(.*?)", "gi"), "$1<b class='text-primary'>$2</b>$3");
                return ` <em class="top-search-object-type">${suggestion.doctype}</em> - ${boldResult}`;
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
                const form = document.querySelector("#top-search form");

                if (this.searchFilter === "note") {
                    form.action = this.noteQuerySearchUrl;
                } else if (this.searchFilter === "bookmark") {
                    form.action = this.bookmarkQuerySearchUrl;
                } else if (this.searchFilter === "drill") {
                    form.action = this.drillQuerySearchUrl;
                } else {
                    form.action = this.querySearchUrl;
                }

                form.submit();
            },
            onKeyDown(evt) {
                if (evt.code === "KeyN" && evt.altKey) {
                    this.handleFilter("note");
                } else if (evt.code === "KeyL" && evt.altKey) {
                    this.handleFilter("bookmark");
                } else if (evt.code === "KeyB" && evt.altKey) {
                    this.handleFilter("book");
                } else if (evt.code === "KeyM" && evt.altKey) {
                    this.handleFilter("music");
                    // Hack to prevent Chrome on OS X from submitting the form.
                    // I have no idea why this happens.
                    evt.preventDefault();
                } else if (evt.code === "KeyD" && evt.altKey) {
                    this.handleFilter("drill");
                } else if (evt.key === "a" && evt.altKey) {
                    document.getElementById("top-simple-suggest").select();
                } else if (evt.code === "Escape") {
                    this.showSearchWindow = false;
                }
            },
            handleFilter(filter) {
                this.searchFilter = this.searchFilter === filter ? "" : filter;
                this.saveSearchFilter(this.searchFilter);
                this.$refs.suggestComponent.research();
            },
            handleRecentSearch(searchTerm) {
                window.location=this.querySearchUrl + "?search=" + searchTerm.search_text;
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
            getFilterClass(filter) {
                if (filter === this.searchFilter) {
                    return "selected rounded-sm";
                }
            },
            removeFilter() {
                this.searchFilter = "";
                this.handleFilter("");
            },
            getFilterName(doctype) {
                const filter = this.searchFilterTypes.filter((x) => {
                    return x.doctype === doctype;
                });
                return filter.length > 0 ? filter[0].name : "";
            },
        },
    };

</script>
