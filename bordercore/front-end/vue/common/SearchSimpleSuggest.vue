<template>
    <div>
        <form class="form-inline float-right" method="get" id="top-search-form">
            <span class="pr-2" v-if="searchFilter">Filter:
                <span id="top-search-filter-type">
                {{ searchFilter }}
                </span>
            </span>
            <div class="form-row">

                <div class="col-auto has-search">
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
                            <span v-html="boldenSuggestion(scope)"></span>
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
            uuidSearchUrl: String,
            noteTagSearchUrl: String,
            querySearchUrl: String,
            tagSearchUrl: String,
            noteQuerySearchUrl: String,
            bookmarkTagSearchUrl: String,
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
                    return axios.get(url + query + "&doc_type=" + this.searchFilter.toLowerCase())
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

                if (this.searchFilter === "Note") {
                    if (datum.object_type === "Tag") {
                        window.location = this.noteTagSearchUrl + datum.value;
                    } else {
                        window.location = this.uuidSearchUrl.replace(/00000000-0000-0000-0000-000000000000/, datum.uuid);
                    }
                } else if (this.searchFilter === "Bookmark") {
                    if (datum.object_type === "Tag") {
                        window.location = this.bookmarkTagSearchUrl.replace(/666/, datum.value);
                    } else {
                        window.location = datum.url;
                    }
                } else if (datum.object_type === "Blob" || datum.object_type === "Document") {
                    window.location = this.uuidSearchUrl.replace(/00000000-0000-0000-0000-000000000000/, datum.uuid);
                } else if (datum.object_type === "Tag") {
                    window.location = this.tagSearchUrl.replace(/666/, datum.value);
                } else if (datum.object_type === "Bookmark") {
                    window.location = datum.url;
                } else {
                    console.error(`Object type not supported: ${datum.object_type}`);
                }

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
