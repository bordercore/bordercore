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
                                <select-value
                                    id="object-search"
                                    ref="selectValue"
                                    label="name"
                                    name="search"
                                    place-holder="Search"
                                    :search-url="getSearchObjectUrl()"
                                    :bolden-option="true"
                                    @select="select"
                                >
                                    <template #option="props">
                                        <!-- @click.stop="" handler is needed to prevent the splitter from being selected -->
                                        <div v-if="props.option.splitter"
                                             class="search-splitter"
                                             @click.stop=""
                                        >
                                            {{ props.option.name }}
                                        </div>
                                        <div v-else class="object-select-suggestion d-flex">
                                            <div v-if="props.option.cover_url" class="cover-image">
                                                <img class="mh-100 mw-100" :src="props.option.cover_url">
                                            </div>
                                            <div v-else-if="props.option.doctype === 'Note'" class="cover-image">
                                                <font-awesome-icon icon="sticky-note" class="fa-3x w-100 h-100 text-secondary" />
                                            </div>
                                            <div v-else-if="props.option.doctype === 'Document'" class="cover-image">
                                                <font-awesome-icon icon="fa-copy" class="fa-lg text-primary" />
                                            </div>
                                            <div v-else-if="props.option.doctype === 'Bookmark'" class="cover-image">
                                                <img width="120" height="67" :src="props.option.thumbnail_url">
                                            </div>
                                            <div class="name d-flex flex-column">
                                                <div class="ms-2">
                                                    {{ props.option.name }}
                                                </div>
                                                <div class="date ms-2">
                                                    {{ props.option.date }}
                                                    <span v-if="props.option.important === 10" class="ms-2">
                                                        <font-awesome-icon icon="heart" class="text-danger" />
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </template>
                                    <!-- <template slot="afterList">
                                         <div v-if="hasMoreThanMax()" slot="misc-item-below" class="object-select-misc-item-below p-2">
                                         <span>
                                         <strong>Too many mathces</strong> other matches
                                         </span>
                                         </div>
                                         </template> -->
                                </select-value>
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

    export default {
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
            hasMoreThanMax() {
                console.log("GOT HERE!!!!!!!!!!");
                /* console.log(this.$refs.selectValue.options.length);
                 * console.log(maxSuggestions);
                 * return this.$refs.selectValue.options.length > maxSuggestions; */
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
            getSearchObjectUrl(query) {
                let url = this.searchObjectUrl;
                url += "?doc_type=" + this.doctypes.join(",");
                url += "&term=";
                return url;
            },
            openModal(callback, returnArgs) {
                this.callback = callback;
                this.returnArgs = returnArgs;
                const modal = new Modal(`#modalObjectSelect${this.label}`);
                modal.show();
                setTimeout( () => {
                    this.$refs.selectValue.$el.querySelector("input").focus();
                }, 500);
                const suggest = this.$refs.selectValue;

                if (suggest.$refs.multiselect.options.length === 0) {
                    if (this.initialDoctypes.includes("media")) {
                        suggest.$refs.multiselect.options.push(
                            {
                                uuid: "__Recent_Media",
                                name: "Recent Media",
                                splitter: true,
                                value: "",
                            },
                        );
                        suggest.$refs.multiselect.options.push(...this.recentMedia.mediaList.slice(0, 10));
                    } else if (this.initialDoctypes.includes("bookmark")) {
                        suggest.$refs.multiselect.options.push(
                            {
                                uuid: "__Recent_Bookmarks",
                                name: "Recent Bookmarks",
                                splitter: true,
                                value: "",
                            },
                        );
                        suggest.$refs.multiselect.options.push(...this.recentBookmarks.bookmarkList.slice(0, 10));
                    } else {
                        suggest.$refs.multiselect.options.push(
                            {
                                uuid: "__Recent_Blobs",
                                name: "Recent Blobs",
                                splitter: true,
                                value: "",
                            },
                        );
                        suggest.$refs.multiselect.options.push(...this.recentBlobs.blobList.slice(0, 5));
                        suggest.$refs.multiselect.options.push(
                            {
                                uuid: "__Recent_Bookmarks",
                                name: "Recent Bookmarks",
                                splitter: true,
                                value: "",
                            },
                        );
                        suggest.$refs.multiselect.options.push(...this.recentBookmarks.bookmarkList.slice(0, 5));
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
                    this.$refs.selectValue.$refs.multiselect.$el.querySelector("input").blur();
                    this.$refs.selectValue.value = "";
                });
            },
        },

    };

</script>
