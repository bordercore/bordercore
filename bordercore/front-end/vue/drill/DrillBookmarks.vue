<template>
    <div>
        <div>
            <card title="Related Bookmarks">
                <template #top-right>
                    <span class="button-plus float-right" @click="chooseBookmark()">
                        <font-awesome-icon icon="plus" />
                    </span>
                </template>

                <template #content>
                    <ul id="sort-container-tags" class="list-group list-group-flush">
                        <draggable v-model="bookmarkList" ghost-class="sortable-ghost" draggable=".draggable" @change="onChange">
                            <transition-group type="transition" class="w-100">
                                <li v-for="(bookmark, index) in bookmarkList" v-cloak :key="bookmark.id" v-b-hover="handleHover" class="list-group-item list-group-item-secondary text-info draggable px-0" :data-uuid="bookmark.uuid">
                                    <div class="d-flex">
                                        <div class="pr-2" v-html="bookmark.favicon_url" />
                                        <div>
                                            <a :href="bookmark.url">{{ bookmark.name }}</a>

                                            <div v-show="!bookmark.noteIsEditable" v-if="bookmark.note" class="node-note" @click="activateInEditMode(bookmark, index)">
                                                {{ bookmark.note }}
                                            </div>
                                            <span v-show="bookmark.noteIsEditable">
                                                <input id="add-bookmark-input" ref="input" type="text" class="form-control form-control-sm" :value="bookmark.note" placeholder="" autocomplete="off" @blur="editNote(bookmark.uuid, $event.target.value)" @keydown.enter="editNote(bookmark.uuid, $event.target.value)">
                                            </span>
                                        </div>
                                        <div class="dropdownmenu">
                                            <dropdown-menu v-model="show" transition="translate-fade-down" class="hidden">
                                                <font-awesome-icon icon="ellipsis-v" />
                                                <div slot="dropdown">
                                                    <a class="dropdown-item" href="#" @click.prevent="removeBookmark(bookmark.uuid)">Remove</a>
                                                    <a class="dropdown-item" :href="bookmark.edit_url">Edit Bookmark</a>
                                                    <a v-if="!bookmark.note" class="dropdown-item" href="#" @click.prevent="addNote(bookmark.uuid)">Add note</a>
                                                    <a v-if="bookmark.note" class="dropdown-item" href="#" @click.prevent="activateInEditMode(bookmark, index)">Edit note</a>
                                                </div>
                                            </dropdown-menu>
                                        </div>
                                    </div>
                                </li>
                                <div v-cloak v-if="bookmarkList.length == 0" :key="1" class="text-secondary">
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
            :get-title-from-url-url="getTitleFromUrlUrl"
            :create-bookmark-url="createBookmarkUrl"
            :question-uuid="questionUuid"
            @addBookmark="addBookmark"
        />
    </div>
</template>

<script>

    import BookmarkSearch from "../bookmark/BookmarkSearch.vue";

    export default {

        components: {
            BookmarkSearch,
        },
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
        mounted() {
            this.getBookmarkList();
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
            activateInEditMode(bookmark, index) {
                this.$set(this.bookmarkList[index], "noteIsEditable", true);

                self = this;
                setTimeout( () => {
                    self.$refs.input[index].focus();
                }, 100);
            },
            addNote(bookmarkUuid) {
                for (const bookmark of this.bookmarkList) {
                    if (bookmark.uuid == bookmarkUuid) {
                        bookmark.noteIsEditable = true;
                    }
                }

                this.$nextTick(() => {
                    this.$refs.input[0].focus();
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
                evt.currentTarget.querySelector(".dropdown").classList.toggle("hidden");
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
    };

</script>
