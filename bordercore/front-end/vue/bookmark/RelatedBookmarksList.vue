<template>
    <div v-b-hover="hoverAddButton" :class="extraClass">
        <transition :name="transitionName">
            <card v-if="bookmarkList.length > 0 || showEmptyList" :title="title">
                <template #top-right>
                    <div v-if="showAddButton" class="node-add-button">
                        <add-button href="#" :click-handler="openModal" class="hover-target d-none" />
                    </div>
                </template>

                <template #content>
                    <ul id="sort-container-tags" class="list-group list-group-flush">
                        <draggable v-model="bookmarkList" ghost-class="sortable-ghost" draggable=".draggable" @change="onSort">
                            <transition-group type="transition" class="w-100">
                                <li v-for="(bookmark, index) in bookmarkList" v-cloak :key="bookmark.uuid" v-b-hover="hoverDropdown" class="list-group-item list-group-item-secondary text-info draggable px-0" :data-uuid="bookmark.uuid">
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
                                        <div class="dropdownmenu d-flex">
                                            <dropdown-menu v-model="showDropdown" transition="translate-fade-down" class="d-none" :right="true">
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
        </transition>
        <bookmark-select
            ref="bookmarkSearch"
            :search-url="searchBookmarkUrl"
            :create-bookmark-url="createBookmarkUrl"
            :get-title-from-url-url="getTitleFromUrlUrl"
            @select-bookmark="selectBookmark"
        />
    </div>
</template>

<script>

    export default {

        props: {
            objectUuid: {
                default: "",
                type: String,
            },
            modelName: {
                default: "",
                type: String,
            },
            blobUuid: {
                default: "",
                type: String,
            },
            title: {
                default: "Related Bookmarks",
                type: String,
            },
            getBookmarkListUrl: {
                default: "",
                type: String,
            },
            searchBookmarkUrl: {
                default: "",
                type: String,
            },
            getTitleFromUrlUrl: {
                default: "",
                type: String,
            },
            createBookmarkUrl: {
                default: "",
                type: String,
            },
            addBookmarkUrl: {
                default: "",
                type: String,
            },
            updateModified: {
                default: false,
                type: Boolean,
            },
            removeBookmarkUrl: {
                default: "",
                type: String,
            },
            sortBookmarkListUrl: {
                default: "",
                type: String,
            },
            editBookmarkNoteUrl: {
                default: "url",
                type: String,
            },
            showAddButton: {
                default: true,
                type: Boolean,
            },
            extraClass: {
                default: "",
                type: String,
            },
            transitionName: {
                default: "fade",
                type: String,
            },
            showEmptyList: {
                default: true,
                type: Boolean,
            },
        },
        data() {
            return {
                mode: "search",
                name: "",
                bookmarkList: [],
                showDropdown: false,
            };
        },
        mounted() {
            this.getBookmarkList();
        },
        methods: {
            getBookmarkList() {
                doGet(
                    this,
                    this.getBookmarkListUrl.replace(/00000000-0000-0000-0000-000000000000/, this.objectUuid),
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
            removeBookmark(bookmarkUuid) {
                doPost(
                    this,
                    this.removeBookmarkUrl,
                    {
                        "object_uuid": this.objectUuid,
                        "model_name": this.modelName,
                        "bookmark_uuid": bookmarkUuid,
                    },
                    (response) => {
                        this.getBookmarkList();
                    },
                    "Bookmark removed",
                    "",
                );
            },
            hoverDropdown(isHovered, evt) {
                this.handleHover(isHovered, evt, ".dropdown");
            },
            hoverAddButton(isHovered, evt) {
                this.handleHover(isHovered, evt, ".hover-target");
            },
            handleHover(isHovered, evt, selector) {
                const target = evt.currentTarget.querySelector(selector);
                if (target === null) {
                    return;
                }
                // Note: I've found that using a more concise "toggle" command
                //  can cause the button's state to become out of sync, so instead
                //  I choose to be more specific instead.
                if (isHovered) {
                    target.classList.remove("d-none");
                } else {
                    target.classList.add("d-none");
                }
            },
            openModal() {
                $("#modalAddBookmark").modal("show");
                setTimeout( () => {
                    this.$refs.bookmarkSearch.$refs.simpleSuggest.$refs.suggestComponent.input.focus();
                }, 500);
            },
            selectBookmark(bookmarkUuid) {
                let url = this.addBookmarkUrl;
                if (this.updateModified) {
                    url = url + "?update_modified=true";
                }

                doPost(
                    this,
                    url,
                    {
                        "object_uuid": this.objectUuid,
                        "model_name": this.modelName,
                        "bookmark_uuid": bookmarkUuid,
                    },
                    (response) => {
                        this.getBookmarkList();
                    },
                    "Bookmark added",
                    "",
                );
            },
            onSort(evt) {
                const bookmarkUuid = evt.moved.element.uuid;

                // The backend expects the ordering to begin
                // with 1, not 0, so add 1.
                const newPosition = evt.moved.newIndex + 1;

                doPost(
                    this,
                    this.sortBookmarkListUrl,
                    {
                        "object_uuid": this.objectUuid,
                        "model_name": this.modelName,
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
                                "object_uuid": this.objectUuid,
                                "model_name": this.modelName,
                                "bookmark_uuid": bookmark.uuid,
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
