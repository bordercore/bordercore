<template>
    <Transition name="fade">
        <div v-show="showSearchWindow" id="top-search">
            <form class="form-inline" method="get">
                <input type="hidden" name="doctype" :value="searchFilter">
                <div class="form-row">
                    <div class="has-search me-1">
                        <font-awesome-icon icon="search" />

                        <select-value
                            ref="selectValue"
                            label="name"
                            name="search"
                            place-holder="Search"
                            :search-url="suggestSearchUrl"
                            @search-change="onSearchChange"
                            @select="select"
                            @enter="onEnter"
                            @keydown.prevent="onKeyDown"
                        >
                            <template #option="props">
                                <!-- @click.stop="" handlers are needed to prevent the splitter from being selected -->
                                <span v-if="props.option.splitter"
                                      class="search-splitter"
                                      @click.stop=""
                                >
                                    {{ props.option.name }}
                                </span>
                                <div v-else class="search-suggestion">
                                    <span v-if="props.option.important === 10" class="me-1">
                                        <font-awesome-icon icon="heart" class="text-danger" />
                                    </span>
                                    <span v-if="props.option.doctype">
                                        <em class="top-search-object-type">{{ props.option.doctype }}</em> -
                                    </span>
                                    <span class="d-inline" v-html="boldenSuggestion(props)" />
                                </div>
                            </template>
                        </select-value>
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
            <div v-if="showFilter" id="top-search-filter-options" class="ms-3 mt-2 p-2">
                <div class="search-splitter">
                    Filter Options
                </div>
                <div class="d-flex flex-column">
                    <div v-for="filter in searchFilterTypes" :key="filter.icon" class="search-suggestion d-flex" :class="getFilterClass(filter.doctype)" @click.prevent="handleFilter(filter.doctype)">
                        <div class="top-search-filter-icon d-flex justify-content-center align-items-center">
                            <font-awesome-icon class="me-2" :icon="filter.icon" />
                        </div>
                        <div>
                            {{ filter.name }}
                        </div>
                    </div>
                </div>
                <div class="search-splitter">
                    Recent Searches
                </div>
                <div class="d-flex flex-column">
                    <div v-for="recentSearch in recentSearches" :key="recentSearch.id" class="search-suggestion d-flex" @click.prevent="handleRecentSearch(recentSearch)">
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

    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";
    import SelectValue from "../common/SelectValue.vue";

    export default {
        components: {
            FontAwesomeIcon,
            SelectValue,
        },
        props: {
            initialSearchFilter: {
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
        setup(props) {
            function focusSearch() {
                selectValue.value.$el.querySelector("input").focus();
            }

            function handleFilter(filter) {
                searchFilter.value = searchFilter.value === filter ? "" : filter;
                saveSearchFilter(searchFilter);
            }

            function saveSearchFilter(searchFilter) {
                doPost(
                    null,
                    props.storeInSessionUrl,
                    {
                        "top_search_filter": searchFilter,
                    }
                    ,
                    (response) => {},
                    "",
                    "",
                );
            }

            onMounted(() => {
                document.addEventListener("keydown", function(evt) {
                    if (evt.key === "s" && evt.altKey) {
                        self.showSearchWindow = true;
                    }
                } );
            });

            const showFilter = ref(true);
            const showSearchWindow = ref(false);
            const searchFilter = ref(props.initialSearchFilter);
            const selectValue = ref(null);

            return {
                focusSearch,
                handleFilter,
                saveSearchFilter,
                selectValue,
                searchUrl: props.suggestSearchUrl,
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
                showFilter,
                showSearchWindow,
                searchFilter,
            };
        },
        mounted() {
            const self = this;

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
            boldenSuggestion(scope) {
                if (!scope) return scope;

                const {option, query} = scope;

                const result = option.name;
                if (!option.doctype) {
                    return result;
                }

                if (!query) return result;

                const texts = query.split(/[\s-_/\\|\.]/gm).filter((t) => !!t) || [""];

                const boldResult = result.replace(new RegExp("(.*?)(" + texts.join("|") + ")(.*?)", "gi"), "$1<b class='text-primary'>$2</b>$3");
                return boldResult;
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
            onSearchChange(query) {
                this.showFilter = query === "";
            },
            handleRecentSearch(searchTerm) {
                window.location=this.querySearchUrl + "?search=" + searchTerm.search_text;
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
