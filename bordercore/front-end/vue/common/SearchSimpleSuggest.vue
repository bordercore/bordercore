<template>
    <div>
        <form class="form-inline float-right" method="get" id="top-search-form">
            <span class="pr-2" v-if="searchFilter">Filter:
                <span id="top-search-filter-type">
                {{ searchFilter }}
                </span>
            </span>
            <div class="form-row">

                <div class="col-auto has-search" id="top-search-container">
                    <font-awesome-icon icon="search" class="form-control-feedback text-dark"></font-awesome-icon>

                    <vue-simple-suggest ref="suggestComponent"
                                        id="top-simple-suggest"
                                        :accesskey="accesskey"
                                        v-model="query"
                                        :display-attribute="displayAttribute"
                                        :value-attribute="valueAttribute"
                                        :list="search"
                                        :filter-by-query=false
                                        :debounce=200
                                        :min-length=2
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
                            <!-- @*event*.stop="null" handlers are needed to prevent the splitter from being selected -->
                            <span v-if="scope.suggestion.splitter"
                                  @click.stop="{}"
                                  @keyup.stop="{}"
                                  @mouseenter.stop="{}"
                                  @mouseleave.stop="{}"
                                  @keydown.stop="{}"
                                  class="top-search-splitter"
                            >{{ scope.suggestion.title }}</span>
                            <span v-else v-html="boldenSuggestion(scope)" class="top-search-suggestion"></span>
                        </div>

                    </vue-simple-suggest>

                </div>

                <div class="col-auto">
                    <span class="align-text-bottom" id="greeting">Hello <strong>{{ userName }}</strong></span>
                </div>

            </div>
        </form>
    </div>
</template>

<script>

    import Vue from "vue";
    import VueSimpleSuggest from "vue-simple-suggest";

    export default {
        props: {
            accesskey: {
                default: null
            },
            id: {
                default: "simple-suggest"
            },
            displayAttribute: {
                default: "value"
            },
            valueAttribute: {
                default: "value"
            },
            maxSuggestions: {
                default: 10,
                type: Number
            },
            userName: String,
            initialSearchType: {
                default: "",
                type: String
            },
            suggestSearchUrl: String,
            querySearchUrl: String,
            noteQuerySearchUrl: String,
            drillQuerySearchUrl: String,
            storeInSessionUrl: String,
        },
        data() {
            return {
                query: "",
                autoCompleteStyle: {
                    vueSimpleSuggest: "position-relative",
                    inputWrapper: "",
                    defaultInput: "form-control search-box-input",
                    suggestions: "position-absolute list-group z-1000",
                    suggestItem: "list-group-item"
                },
                searchFilter: this.initialSearchType,
                searchUrl: this.suggestSearchUrl
            }
        },
        methods: {
            search(query) {

                try {
                    let url = this.searchUrl;
                    return axios.get(url + query + "&filter=" + this.searchFilter.toLowerCase())
                                .then(response => {
                                    return response.data;
                                })
                } catch(error) {
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

                const { suggestion, query } = scope;

                let result = this.$refs.suggestComponent.displayProperty(suggestion);

                if (!suggestion.object_type) {
                    return result;
                }

                if (!query) return result;

                const texts = query.split(/[\s-_/\\|\.]/gm).filter(t => !!t) || [''];

                const bold_result = result.replace(new RegExp('(.*?)(' + texts.join('|') + ')(.*?)','gi'), '$1<b>$2</b>$3');

                return "<em class=\"top-search-object-type\">" + suggestion.object_type + "</em> - " + bold_result;

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
                console.log(evt);
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
                        "top_search_filter": searchFilter
                    }
                    ,
                    (response) => {},
                    "",
                    ""
                );

            }
        },
        components: {
            VueSimpleSuggest
        }
    };

</script>
