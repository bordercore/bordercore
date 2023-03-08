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
                                <template #dropdown>
                                    <li>
                                        <a class="dropdown-item" href="#" @click.prevent="openObjectSelectModal">
                                            <span>
                                                <font-awesome-icon icon="plus" class="text-primary me-3" />
                                            </span>
                                            Add Bookmark
                                        </a>
                                    </li>
                                </template>
                            </drop-down-menu>
                        </div>
                    </div>
                </template>

                <template #content>
                    <hr class="divider">
                    <ul id="sort-container-tags" class="list-group list-group-flush interior-borders">
                        <div v-cloak v-if="bookmarkList.length == 0" :key="1" class="text-muted">
                            No bookmarks
                        </div>
                        <draggable v-model="bookmarkList" draggable=".draggable" item-key="uuid" :component-data="{type:'transition-group'}" @change="handleSort">
                            <template #item="{element, index}">
                                <li v-cloak :key="element.uuid" class="hover-target list-group-item list-group-item-secondary draggable px-0" :data-uuid="element.uuid">
                                    <div class="dropdown-height d-flex align-items-start">
                                        <div class="pe-2" v-html="element.favicon_url" />
                                        <div>
                                            <a :href="element.url">{{ element.name }}</a>

                                            <div v-show="!element.noteIsEditable" v-if="element.note" class="node-object-note" @click="handleSetNoteIsEditable(element, {index})">
                                                {{ element.note }}
                                            </div>
                                            <span v-show="element.noteIsEditable">
                                                <input :id="`related_bookmark_${index}`" type="text" class="form-control form-control-sm" :value="element.note" placeholder="" autocomplete="off" @blur="handleEditNote(element, $event.target.value)" @keydown.enter="handleEditNote(element, $event.target.value)">
                                            </span>
                                        </div>
                                        <drop-down-menu ref="editNoteMenu" :show-on-hover="true">
                                            <template #dropdown>
                                                <li>
                                                    <a class="dropdown-item" href="#" @click.prevent="handleRemove(element.uuid)">
                                                        <font-awesome-icon icon="trash-alt" class="text-primary me-3" />Remove
                                                    </a>
                                                    <a class="dropdown-item" :href="element.edit_url">
                                                        <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />Edit Bookmark
                                                    </a>
                                                    <a class="dropdown-item" href="#" @click.prevent="handleSetNoteIsEditable(element, index)">
                                                        <font-awesome-icon :icon="element.note ? 'pencil-alt' : 'plus'" class="text-primary me-3" />{{ element.note ? 'Edit' : 'Add' }} note
                                                    </a>
                                                </li>
                                            </template>
                                        </drop-down-menu>
                                    </div>
                                </li>
                            </template>
                        </draggable>
                    </ul>
                </template>
            </card>
        </transition>
    </div>
</template>

<script>

    import draggable from "vuedraggable";
    import Card from "/front-end/vue/common/Card.vue";
    import DropDownMenu from "/front-end/vue/common/DropDownMenu.vue";
    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

    export default {
        components: {
            Card,
            draggable,
            DropDownMenu,
            FontAwesomeIcon,
        },
        props: {
            objectUuid: {
                default: "",
                type: String,
            },
            modelName: {
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
            transitionName: {
                default: "fade",
                type: String,
            },
            showEmptyList: {
                default: true,
                type: Boolean,
            },
            newBookmark: {
                default: false,
                type: Boolean,
            },
        },
        emits: ["open-object-select-modal"],
        setup(props, ctx) {
            const bookmarkList = ref([]);

            let isEditingNote = false;

            function addBookmark(bookmark) {
                let url = props.addBookmarkUrl;

                if (props.newBookmark) {
                    bookmark.noteIsEditable = false;
                    bookmarkList.value.push(bookmark);
                    return;
                }

                if (props.updateModified) {
                    url = url + "?update_modified=true";
                }

                doPost(
                    url,
                    {
                        "object_uuid": props.objectUuid,
                        "model_name": props.modelName,
                        "bookmark_uuid": bookmark.uuid,
                    },
                    (response) => {
                        getBookmarkList();
                    },
                    "Bookmark added",
                );
            };

            function getBookmarkList() {
                doGet(
                    props.getBookmarkListUrl.replace(/00000000-0000-0000-0000-000000000000/, props.objectUuid),
                    (response) => {
                        bookmarkList.value = response.data.bookmark_list;
                    },
                    "Error getting bookmark list",
                );
            };

            function handleEditNote(bookmark, note) {
                if (isEditingNote) {
                    return;
                }
                isEditingNote = true;

                if (note === bookmark.note) {
                    // If the note hasn't changed, abort
                    isEditingNote = false;
                    return;
                }

                if (props.newBookmark) {
                    bookmark.note = note;
                } else {
                    doPost(
                        props.editBookmarkNoteUrl,
                        {
                            "object_uuid": props.objectUuid,
                            "model_name": props.modelName,
                            "bookmark_uuid": bookmark.uuid,
                            "note": note,
                        },
                        (response) => {
                            getBookmarkList();
                        },
                    );
                }
                isEditingNote = false;
            };

            function handleRemove(bookmarkUuid) {
                if (props.newBookmark) {
                    const newBookmarkList = bookmarkList.value.filter((x) => x.uuid !== bookmarkUuid);
                    bookmarkList.value = newBookmarkList;
                    return;
                }

                doPost(
                    props.removeBookmarkUrl,
                    {
                        "object_uuid": props.objectUuid,
                        "model_name": props.modelName,
                        "bookmark_uuid": bookmarkUuid,
                    },
                    (response) => {
                        getBookmarkList();
                    },
                    "Bookmark removed",
                );
            };

            function handleSetNoteIsEditable(bookmark, index) {
                bookmark.noteIsEditable = true;

                nextTick(() => {
                    document.getElementById(`related_bookmark_${index}`).focus();
                });
            };

            function handleSort(evt) {
                const bookmarkUuid = evt.moved.element.uuid;

                // The backend expects the ordering to begin
                // with 1, not 0, so add 1.
                const newPosition = evt.moved.newIndex + 1;

                if (props.newBookmark) {
                    return;
                }

                doPost(
                    props.sortBookmarkListUrl,
                    {
                        "object_uuid": props.objectUuid,
                        "model_name": props.modelName,
                        "bookmark_uuid": bookmarkUuid,
                        "new_position": newPosition,
                    },
                    () => {},
                );
            };

            function openObjectSelectModal() {
                ctx.emit("open-object-select-modal", ["bookmark"]);
            };

            onMounted(() => {
                if (!props.newBookmark) {
                    getBookmarkList();
                }
            });

            return {
                addBookmark,
                bookmarkList,
                handleEditNote,
                handleRemove,
                handleSetNoteIsEditable,
                handleSort,
                openObjectSelectModal,
            };
        },
    };

</script>
