<template>
    <div>

        <div>
            <card title="Related Bookmarks">
                <template v-slot:top-right>
                    <span class="button-plus float-right" @click="chooseBookmark()">
                        <font-awesome-icon icon="plus"></font-awesome-icon>
                    </span>
                </template>

                <template v-slot:content>

                    <ul class="list-group list-group-flush" id="sort-container-tags">
                        <draggable v-model="bookmarkList" @change="onChange" ghost-class="sortable-ghost" draggable=".draggable">
                            <transition-group type="transition" class="w-100">
                                <li v-for="(bookmark, index) in bookmarkList" class="list-group-item list-group-item-secondary text-info draggable pl-0" :data-uuid="bookmark.uuid" :key="bookmark.id" v-cloak v-b-hover="handleHover">
                                    <div class="dropdownmenu hidden float-right node-bookmark-menu">
                                        <dropdown-menu v-model="show" transition="translate-fade-down" class="text-center">
                                            <font-awesome-icon icon="ellipsis-v" class="burger-menu"></font-awesome-icon>
                                            <div slot="dropdown">
                                                <a class="dropdown-item" href="#" @click="removeBookmark(bookmark.uuid)">Remove</a>
                                                <a class="dropdown-item" :href="bookmark.edit_url">Edit</a>
                                                <a v-if="!bookmark.note" class="dropdown-item" href="#" @click="addNote(bookmark.uuid, index)">Add note</a>
                                            </div>
                                        </dropdown-menu>
                                    </div>
                                    <div class="d-flex">
                                        <div v-html="bookmark.favicon_url" class="float-left pr-2"></div>
                                        <div>
                                            <a :href="bookmark.url">{{ bookmark.name }}</a>

                                            <div v-if="bookmark.note" v-on:click="activateInEditMode(bookmark, $event.target)" v-show="!bookmark.noteIsEditable" class="node-note">{{ bookmark.note }}</div>
                                            <span v-show="bookmark.noteIsEditable">
                                                <input type="text" class="form-control form-control-sm" id="add-bookmark-input" :value="bookmark.note" placeholder="Add Bookmark" @blur="editNote(bookmark.uuid, $event.target.value)" @keydown.enter="editNote(bookmark.uuid, $event.target.value)" >
                                            </span>

                                        </div>
                                    </div>
                                </li>
                                <div class="text-secondary" v-if="bookmarkList.length == 0" :key="1" v-cloak>
                                  No bookmarks
                                </div>
                            </transition-group>
                        </draggable>
                    </ul>
                </template>
            </card>
        </div>

        <bookmark-search
            ref="bookmarkSearch"
            :getTitleFromUrlUrl="getTitleFromUrlUrl"
            :createBookmarkUrl="createBookmarkUrl"
            :questionUuid="questionUuid"
            @addBookmark="addBookmark"
        >
        </bookmark-search>

    </div>

</template>

<script>

    import BookmarkSearch from "../bookmark/BookmarkSearch.vue";

    export default {

        props: {
            questionUuid: {
                default: "",
                type: String,
            },
            getBookmarkListUrl: {
                default: "url",
                type: String,
            },
            sortBookmarkListUrl: {
                default: "url",
                type: String,
            },
            addBookmarkUrl: {
                default: "url",
                type: String,
            },
            removeBookmarkUrl: {
                default: "url",
                type: String,
            },
            editBookmarkNoteUrl: {
                default: "url",
                type: String,
            },
            searchUrl: {
                default: "url",
                type: String,
            },
            getTitleFromUrlUrl: {
                default: "url",
                type: String,
            },
            createBookmarkUrl: {
                default: "url",
                type: String,
            },
        },
        data() {
            return {
                bookmarkList: [],
                show: false,
            };
        },
        methods: {
            getBookmarkList() {
                doGet(
                    this,
                    this.getBookmarkListUrl.replace(/00000000-0000-0000-0000-000000000000/, this.questionUuid),
                    (response) => {
                        this.bookmarkList = response.data.bookmark_list;

                        // Let Vue know that each blob's "noteIsEditable" property is reactive
                        for (const bookmark of this.bookmarkList) {
                            this.$set(bookmark, "noteIsEditable", false);
                        }
                    },
                    "Error getting bookmark list",
                );
            },
            chooseBookmark() {
                $("#modalAddBookmark").modal("show");
                setTimeout( () => {
                    document.getElementById("bookmark-search-url").focus();
                }, 500);
            },
            onChange(evt) {
                const bookmarkUuid = evt.moved.element.uuid;

                // The backend expects the ordering to begin
                // with 1, not 0, so add 1.
                const newPosition = evt.moved.newIndex + 1;

                doPost(
                    this,
                    this.sortBookmarkListUrl,
                    {
                        "question_uuid": this.questionUuid,
                        "bookmark_uuid": bookmarkUuid,
                        "new_position": newPosition,
                    },
                    () => {},
                    "",
                    "",
                );
            },
            activateInEditMode(bookmark, event) {
                const isId = (value) => value.id == bookmark.id;
                const index = this.bookmarkList.findIndex(isId);

                this.$set(this.bookmarkList[index], "noteIsEditable", true);

                setTimeout( () => {
                    event.nextElementSibling.querySelector("input").focus();
                }, 100);
            },
            addNote(bookmarkUuid, index) {
                for (const bookmark of this.bookmarkList) {
                    if (bookmark.uuid == bookmarkUuid) {
                        bookmark.noteIsEditable = true;
                    }
                }

                this.$nextTick(() => {
                    this.$refs.input[index].focus();
                });
            },
            addBookmark(bookmarkUuid) {
                doPost(
                    this,
                    this.addBookmarkUrl,
                    {
                        "question_uuid": this.questionUuid,
                        "bookmark_uuid": bookmarkUuid,
                    },
                    (response) => {
                        this.getBookmarkList();
                    },
                    "",
                    "",
                );
            },
            handleHover(hovered, evt) {
                evt.currentTarget.querySelector(".dropdownmenu").classList.remove("hidden");
                if (hovered == true) {
                    evt.currentTarget.querySelector(".dropdownmenu").classList.remove("hidden");
                } else {
                    evt.currentTarget.querySelector(".dropdownmenu").classList.add("hidden");
                };
            },
            removeBookmark(bookmarkUuid) {
                doPost(
                    this,
                    this.removeBookmarkUrl,
                    {
                        "question_uuid": this.questionUuid,
                        "bookmark_uuid": bookmarkUuid,
                    },
                    (response) => {
                        this.getBookmarkList();
                    },
                    "Bookmark removed",
                    "",
                );
            },
            editNote(bookmarkUuid, note) {
                if (this.editingNote) {
                    return;
                }
                this.editingNote = true;

                for (const bookmark of this.bookmarkList) {
                    if (bookmark.uuid == bookmarkUuid) {
                        // If the note hasn't changed, abort
                        if (note == bookmark.note) {
                            bookmark.noteIsEditable = false;
                            this.editingNote = false;
                            return;
                        }

                        doPost(
                            this,
                            this.editBookmarkNoteUrl,
                            {
                                "question_uuid": this.questionUuid,
                                "bookmark_uuid": bookmarkUuid,
                                "note": note,
                            },
                            (response) => {
                                this.getBookmarkList();
                            },
                            "",
                            "",
                        );

                        this.editingNote = false;
                    }
                }
            },
        },
        mounted() {
            this.getBookmarkList();
        },
        components: {
            BookmarkSearch,
        },
    };

</script>
