<template>
    <div v-if="bookmarkList.length > 0 || showEmptyList" class="hover-reveal-target mb-3">
        <transition :name="transitionName">
            <card class="position-relative h-100 backdrop-filter z-index-positive">
                <template #title-slot>
                    <div class="d-flex">
                        <div class="card-title d-flex">
                            <font-awesome-icon icon="bookmark" class="text-primary me-3 mt-1" />
                            {{ title }}
                        </div>
                        <div class="dropdown-menu-container ms-auto">
                            <drop-down-menu class="d-none hover-reveal-object" :show-on-hover="false">
                                <div slot="dropdown">
                                    <li>
                                        <a class="dropdown-item" href="#" @click.prevent="openModal">
                                            <span>
                                                <font-awesome-icon icon="plus" class="text-primary me-3" />
                                            </span>
                                            Add Bookmark
                                        </a>
                                    </li>
                                </div>
                            </drop-down-menu>
                        </div>
                    </div>
                </template>

                <template #content>
                    <hr class="divider mt-0">
                    <ul id="sort-container-tags" class="list-group list-group-flush interior-borders">
                        <draggable v-model="bookmarkList" draggable=".draggable" @change="onSort">
                            <transition-group type="transition" class="w-100">
                                <li v-for="(bookmark, index) in bookmarkList" v-cloak :key="bookmark.uuid" class="hover-target list-group-item list-group-item-secondary text-info draggable px-0" :data-uuid="bookmark.uuid">
                                    <div class="dropdown-height d-flex align-items-start">
                                        <div class="pe-2" v-html="bookmark.favicon_url" />
                                        <div>
                                            <a :href="bookmark.url">{{ bookmark.name }}</a>

                                            <div v-show="!bookmark.noteIsEditable" v-if="bookmark.note" class="node-object-note" @click="activateInEditMode(bookmark, index)">
                                                {{ bookmark.note }}
                                            </div>
                                            <span v-show="bookmark.noteIsEditable">
                                                <input id="add-bookmark-input" ref="input" type="text" class="form-control form-control-sm" :value="bookmark.note" placeholder="" autocomplete="off" @blur="editNote(bookmark.uuid, $event.target.value)" @keydown.enter="editNote(bookmark.uuid, $event.target.value)">
                                            </span>
                                        </div>
                                        <drop-down-menu ref="editNoteMenu" :show-on-hover="true">
                                            <div slot="dropdown">
                                                <li>
                                                    <a class="dropdown-item" href="#" @click.prevent="removeBookmark(bookmark.uuid)">
                                                        <font-awesome-icon icon="trash-alt" class="text-primary me-3" />Remove
                                                    </a>
                                                    <a class="dropdown-item" :href="bookmark.edit_url">
                                                        <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />Edit Bookmark
                                                    </a>
                                                    <a v-if="bookmark.note" class="dropdown-item" href="#" @click.prevent="activateInEditMode(bookmark, index)">
                                                        <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />Edit note
                                                    </a>
                                                    <a v-else class="dropdown-item" href="#" @click.prevent="addNote(bookmark.uuid)">
                                                        <font-awesome-icon icon="plus" class="text-primary me-3" />Add note
                                                    </a>
                                                </li>
                                            </div>
                                        </drop-down-menu>
                                    </div>
                                </li>
                                <div v-cloak v-if="bookmarkList.length == 0" :key="1" class="text-muted">
                                    No bookmarks
                                </div>
                            </transition-group>
                        </draggable>
                    </ul>
                </template>
            </card>
        </transition>
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
                default: "Bookmarks",
                type: String,
            },
            getBookmarkListUrl: {
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
            newQuestion: {
                default: false,
                type: Boolean,
            },
        },
        data() {
            return {
                mode: "search",
                name: "",
                bookmarkList: [],
            };
        },
        mounted() {
            if (!this.newQuestion) {
                this.getBookmarkList();
            }
        },
        methods: {
            getBookmarkList() {
                doGet(
                    this,
                    this.getBookmarkListUrl.replace(/00000000-0000-0000-0000-000000000000/, this.objectUuid),
                    (response) => {
                        this.bookmarkList = response.data.bookmark_list;

                        // Let Vue know that each bookmark's "noteIsEditable" property is reactive
                        for (const bookmark of this.bookmarkList) {
                            this.$set(bookmark, "noteIsEditable", false);
                        }
                    },
                    "Error getting bookmark list",
                );
            },
            removeBookmark(bookmarkUuid) {
                if (this.newQuestion) {
                    const newBookmarkList = this.bookmarkList.filter((x) => x.uuid !== bookmarkUuid);
                    this.bookmarkList = newBookmarkList;
                    return;
                }

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
            openModal() {
                this.$parent.$refs.objectSelectBookmark.openModal(["bookmark"]);
            },
            selectBookmark(bookmark) {
                let url = this.addBookmarkUrl;

                if (this.newQuestion) {
                    this.bookmarkList.push(bookmark);
                    // Let Vue know that the bookmark's "noteIsEditable" property is reactive
                    this.$set(bookmark, "noteIsEditable", false);
                    return;
                }

                if (this.updateModified) {
                    url = url + "?update_modified=true";
                }

                doPost(
                    this,
                    url,
                    {
                        "object_uuid": this.objectUuid,
                        "model_name": this.modelName,
                        "bookmark_uuid": bookmark.uuid,
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

                if (this.newQuestion) {
                    return;
                }

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

                        if (this.newQuestion) {
                            bookmark.note = note;
                            bookmark.noteIsEditable = false;
                        } else {
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
                        }
                        this.editingNote = false;
                    }
                }
            },
        },
    };

</script>
