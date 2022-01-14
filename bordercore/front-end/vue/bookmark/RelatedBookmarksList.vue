<template>
    <div :class="extraClass">
        <card :title="title">
            <template #top-right>
                <span v-if="showAddButton" class="button-plus float-right" @click="chooseBookmark()">
                    <font-awesome-icon icon="plus" />
                </span>
            </template>

            <template #content>
                <ul id="sort-container-tags" class="list-group list-group-flush">
                    <draggable v-model="bookmarkList" ghost-class="sortable-ghost" draggable=".draggable" @change="onSort">
                        <transition-group type="transition" class="w-100">
                            <li v-for="(bookmark, index) in bookmarkList" v-cloak :key="bookmark.uuid" v-b-hover="handleHover" class="list-group-item list-group-item-secondary text-info draggable px-0" :data-uuid="bookmark.uuid">
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
                                        <dropdown-menu v-model="showDropdown" transition="translate-fade-down" class="hidden" :right="true">
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
        <div id="modalAddBookmark" class="modal fade" tabindex="-1" role="dialog">
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h4 id="myModalLabel" class="modal-title">
                            Select bookmark
                        </h4>
                        <button type="button" class="close" data-dismiss="modal">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <div class="d-flex flex-column">
                            <form v-if="mode==='search'" @submit.prevent>
                                <div class="form-group">
                                    <simple-suggest
                                        ref="simpleSuggest"
                                        class="w-100"
                                        display-attribute="name"
                                        value-attribute="uuid"
                                        place-holder="Url or Title"
                                        :search-url="searchBookmarkUrl + '?term='"
                                    />
                                </div>
                            </form>
                            <form v-else @submit.prevent>
                                <div class="form-group row">
                                    <label class="col-form-label col-lg-1">URL</label>
                                    <div class="col-lg-10 d-flex">
                                        <input id="bookmark-search-url" v-model="url" class="form-control" type="text" autocomplete="off" placeholder="https://" @change="onChange">
                                    </div>
                                    <div class="col-lg-1">
                                        <div class="spinner-border ml-2" :class="{'d-none': hideSpinner}" role="status">
                                            <span class="sr-only">Loading...</span>
                                        </div>
                                    </div>
                                </div>
                                <div class="form-group row" :class="{'d-none': hideNameInput}">
                                    <label class="col-form-label col-lg-1">Title</label>
                                    <div class="col-lg-10">
                                        <input v-model="name" class="form-control" :disabled="nameInputIsDisabled" type="text" placeholder="Name" autocomplete="off">
                                    </div>
                                </div>

                                <div class="row" :class="{'d-none': hideAddButton}">
                                    <div class="col-lg-10 offset-lg-1 d-flex">
                                        <div class="d-flex flex-column">
                                            <div class="mt-2 text-info">
                                                <font-awesome-icon class="mr-1 pt-1 success" icon="exclamation-triangle" />
                                                {{ message }}
                                            </div>
                                            <div class="mt-2 text-info" :class="{'d-none': hideBookmarkAdded}">
                                                <font-awesome-icon class="mr-1 pt-1 success" icon="check" /> Bookmark successfully added
                                            </div>
                                        </div>
                                        <div class="ml-auto">
                                            <button type="button" class="btn btn-primary" @click="onAdd">
                                                Add
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </form>
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
                    this.getBookmarkListUrl.replace(/00000000-0000-0000-0000-000000000000/, this.blobUuid),
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
                        "blob_uuid": this.blobUuid,
                        "bookmark_uuid": bookmarkUuid,
                    },
                    (response) => {
                        this.getBookmarkList();
                    },
                    "Bookmark removed",
                    "",
                );
            },
            handleHover(hovered, evt) {
                evt.currentTarget.querySelector(".dropdown").classList.toggle("hidden");
            },
            openModal() {
                $("#modalAddBookmark").modal("show");
                setTimeout( () => {
                    this.$refs.simpleSuggest.$refs.suggestComponent.input.focus();
                }, 500);
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
                        "blob_uuid": this.blobUuid,
                        "bookmark_uuid": bookmarkUuid,
                        "new_position": newPosition,
                    },
                    () => {},
                    "",
                    "",
                );
            },
            select(selection) {
                // The parent component receives the bookmark uuid and takes action
                this.$emit("select-bookmark", selection.uuid);
                $("#modalAddBookmark").modal("hide");

                this.$nextTick(() => {
                    this.$refs.simpleSuggest.$refs.suggestComponent.$el.querySelector("input").blur();
                    this.$refs.simpleSuggest.$refs.suggestComponent.setText("");
                });
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
                                "blob_uuid": this.blobUuid,
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
