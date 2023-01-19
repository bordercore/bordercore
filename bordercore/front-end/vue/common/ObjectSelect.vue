<template>
    <div :id="`modalObjectSelect${label}`" class="modal fade" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        {{ title }}
                    </h4>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" />
                </div>
                <div class="modal-body">
                    <div class="d-flex flex-column">
                        <form @submit.prevent>
                            <div>
                                <vue-simple-suggest
                                    id="object-search"
                                    ref="suggestComponent"
                                    v-model="query"
                                    accesskey="s"
                                    :destyled="true"
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
                                             class="search-splitter"
                                             @click.stop=""
                                        >
                                            {{ scope.suggestion.name }}
                                        </div>
                                        <div v-else class="object-select-suggestion d-flex">
                                            <div v-if="scope.suggestion.cover_url" class="cover-image">
                                                <img class="mh-100 mw-100" :src="scope.suggestion.cover_url">
                                            </div>
                                            <div v-else-if="scope.suggestion.doctype === 'Note'" class="cover-image">
                                                <font-awesome-icon icon="sticky-note" class="fa-3x w-100 h-100 text-secondary" />
                                            </div>
                                            <div v-else-if="scope.suggestion.doctype === 'Document'" class="cover-image">
                                                <font-awesome-icon icon="fa-copy" class="fa-lg text-primary" />
                                            </div>
                                            <div v-else-if="scope.suggestion.doctype === 'Bookmark'" class="cover-image">
                                                <img width="120" height="67" :src="scope.suggestion.thumbnail_url">
                                            </div>
                                            <div class="name d-flex flex-column">
                                                <div class="ms-2" v-html="boldenSuggestion(scope)" />
                                                <div class="date ms-2">
                                                    {{ scope.suggestion.date }}
                                                    <span v-if="scope.suggestion.important === 10" class="ms-2">
                                                        <font-awesome-icon icon="heart" class="text-danger" />
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div v-if="suggestionsFound > maxSuggestions" slot="misc-item-below" class="object-select-misc-item-below p-2">
                                        <span>
                                            <strong>{{ suggestionsFound - maxSuggestions }}</strong> other matches
                                        </span>
                                    </div>
                                </vue-simple-suggest>
                            </div>
                        </form>
                        <div v-if="hasFilter" class="d-flex mt-2 ms-3">
                            <div>Filter:</div>
                            <div class="d-flex align-items-center ms-2">
                                <o-switch v-model="toggleBookmarks" data-filter-type="bookmarks" @input="onFilterChange('bookmarks', $event)" />
                                <label class="ms-2" @click="onFilterLabelClick('bookmarks', $event)">Bookmarks</label>
                            </div>
                            <div class="d-flex align-items-center ms-3">
                                <o-switch v-model="toggleBlobs" data-filter-type="blobs" @input="onFilterChange('blobs', $event)" />
                                <label class="ms-2" @click="onFilterLabelClick('blobs', $event)">Blobs</label>
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
            title: {
                type: String,
                default: "Select Object",
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
                returnArgs: null,
                query: "",
                autoCompleteStyle: {
                    vueSimpleSuggest: "position-relative",
                    inputWrapper: "",
                    defaultInput: "form-control",
                    suggestions: "position-absolute list-group z-1000",
                },
                suggestionsFound: 0,
                toggleBookmarks: false,
                toggleBlobs: false,
                // This is populated in the base template
                recentBlobs: JSON.parse(document.getElementById("recent_blobs").textContent),
                recentBookmarks: JSON.parse(document.getElementById("recent_bookmarks").textContent),
                recentMedia: JSON.parse(document.getElementById("recent_media").textContent),
            };
        },
        mounted() {
            if (this.initialDoctypes.length > 0) {
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

                const result = this.$refs.suggestComponent.displayProperty(suggestion);

                if (!query) return result;

                const texts = query.split(/[\s-_/\\|\.]/gm).filter((t) => !!t) || [""];
                return result.replace(new RegExp("(.*?)(" + texts.join("|") + ")(.*?)", "gi"), "$1<b class='matched'>$2</b>$3");
            },
            onFilterLabelClick(filterType, evt) {
                const input = evt.target.parentElement.querySelector("input");
                input.click();
                this.onFilterChange(filterType, evt);
            },
            onFilterChange(filterType, value) {
                if (value === false) {
                    // Remove the filter if we're unchecking an option
                    this.doctypes = ["blob", "book", "bookmark", "document", "note"];
                } else {
                    if (filterType === "blobs") {
                        this.doctypes = ["blob", "book", "document", "note"];
                        this.toggleBookmarks = false;
                    } else {
                        this.doctypes = ["bookmark"];
                        this.toggleBlobs = false;
                    }
                }
            },
            search(query) {
                this.suggestionsFound = 0;
                try {
                    return axios.get(this.getSearchObjectUrl(query))
                                .then((response) => {
                                    this.suggestionsFound = response.data.length;
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
                const suggest = this.$refs.suggestComponent;

                if (suggest.suggestions.length === 0) {
                    if (this.initialDoctypes.includes("media")) {
                        suggest.suggestions.push(
                            {
                                uuid: "__Recent_Media",
                                name: "Recent Media",
                                splitter: true,
                                value: "",
                            },
                        );
                        suggest.suggestions.push(...this.recentMedia.mediaList.slice(0, 10));
                    } else if (this.initialDoctypes.includes("bookmark")) {
                        suggest.suggestions.push(
                            {
                                uuid: "__Recent_Bookmarks",
                                name: "Recent Bookmarks",
                                splitter: true,
                                value: "",
                            },
                        );
                        suggest.suggestions.push(...this.recentBookmarks.bookmarkList.slice(0, 10));
                    } else {
                        suggest.suggestions.push(
                            {
                                uuid: "__Recent_Blobs",
                                name: "Recent Blobs",
                                splitter: true,
                                value: "",
                            },
                        );
                        suggest.suggestions.push(...this.recentBlobs.blobList.slice(0, 5));
                        suggest.suggestions.push(
                            {
                                uuid: "__Recent_Bookmarks",
                                name: "Recent Bookmarks",
                                splitter: true,
                                value: "",
                            },
                        );
                        suggest.suggestions.push(...this.recentBookmarks.bookmarkList.slice(0, 5));
                    }
                }
                suggest.listShown = true;
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
