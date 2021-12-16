import Vue from "vue";
window.Vue = Vue;

import {AlertPlugin, PopoverPlugin, TablePlugin, ToastPlugin, VBHoverPlugin} from "bootstrap-vue";
Vue.use(AlertPlugin);
Vue.use(PopoverPlugin);
Vue.use(TablePlugin);
Vue.use(ToastPlugin);
Vue.use(VBHoverPlugin);

import DropdownMenu from "@innologica/vue-dropdown-menu";
Vue.component("DropdownMenu", DropdownMenu);

import draggable from "vuedraggable";
Vue.component("draggable", draggable);

import Sortable from "sortablejs";
Vue.component("Sortable", Sortable);
window.Sortable = Sortable;

import Vuex from "vuex";
window.Vuex = Vuex;
Vue.use(Vuex);

import Datepicker from "vuejs-datepicker";
Vue.component("vuejs-datepicker", Datepicker);
window.Datepicker = Datepicker;

import pluralize from "pluralize";
window.pluralize = pluralize;

import axios from "axios";
window.axios = axios;

import $ from "jquery";
import jQuery from "jquery";
window.$ = $;
window.jQuery= jQuery;

import "bootstrap";

import {library} from "@fortawesome/fontawesome-svg-core";
import {faAlignLeft, faAngleDown, faAngleRight, faArrowsAltH, faBars, faBook, faBookmark, faBox, faBriefcase, faCalendarAlt, faChartBar, faCheck, faChevronLeft, faChevronRight, faCopy, faDownload, faEllipsisV, faExclamationTriangle, faHeart, faHome, faImage, faInfo, faGraduationCap, faLink, faLock, faMusic, faNewspaper, faPlus, faQuestion, faRunning, faSearch, faSignOutAlt, faStickyNote, faTags, faTasks, faTimesCircle} from "@fortawesome/free-solid-svg-icons";
import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";
library.add(faAlignLeft);
library.add(faAngleDown);
library.add(faAngleRight);
library.add(faArrowsAltH);
library.add(faBars);
library.add(faBookmark);
library.add(faBook);
library.add(faBox);
library.add(faBriefcase);
library.add(faCalendarAlt);
library.add(faChartBar);
library.add(faCheck);
library.add(faChevronLeft);
library.add(faChevronRight);
library.add(faCopy);
library.add(faDownload);
library.add(faEllipsisV);
library.add(faExclamationTriangle);
library.add(faHeart);
library.add(faHome);
library.add(faImage);
library.add(faInfo);
library.add(faGraduationCap);
library.add(faLink);
library.add(faLock);
library.add(faMusic);
library.add(faNewspaper);
library.add(faPlus);
library.add(faQuestion);
library.add(faRunning);
library.add(faSearch);
library.add(faStickyNote);
library.add(faTags);
library.add(faSignOutAlt);
library.add(faTasks);
library.add(faTimesCircle);
Vue.component("font-awesome-icon", FontAwesomeIcon);

import {format} from "date-fns";
window.format = format;

import EasyMDE from "easymde";
window.EasyMDE = EasyMDE;

import hljs from "highlight.js";
window.hljs = hljs;

import markdownit from "markdown-it";
window.markdownit = markdownit;

import {v4 as uuidv4} from "uuid";
window.uuidv4 = uuidv4;

import {doGet, doPost, getFormattedDate, getMarkdown} from "./util.js";
window.doGet = doGet;
window.doPost = doPost;
window.getFormattedDate = getFormattedDate;
window.markdown = getMarkdown();

import EditableTextArea from "./vue/common/EditableTextArea.vue";
Vue.component("EditableTextArea", EditableTextArea);
window.EditableTextArea = EditableTextArea;

import SimpleSuggest from "./vue/common/SimpleSuggest.vue";
Vue.component("SimpleSuggest", SimpleSuggest);
window.SimpleSuggest = SimpleSuggest;

import SearchSimpleSuggest from "./vue/common/SearchSimpleSuggest.vue";
Vue.component("SearchSimpleSuggest", SearchSimpleSuggest);
window.SearchSimpleSuggest = SearchSimpleSuggest;

import TagsInput from "./vue/common/TagsInput.vue";
Vue.component("TagsInput", TagsInput);
window.TagsInput = TagsInput;

import SearchTagsInput from "./vue/common/SearchTagsInput.vue";
Vue.component("SearchTagsInput", SearchTagsInput);
window.SearchTagsInput = SearchTagsInput;

import Card from "./vue/common/Card.vue";
Vue.component("Card", Card);
window.Card = Card;

import SearchNoResult from "./vue/common/SearchNoResult.vue";
Vue.component("SearchNoResult", SearchNoResult);
window.SearchNoResult = SearchNoResult;

import TreeMenu from "./vue/common/TreeMenu.vue";
Vue.component("TreeMenu", TreeMenu);
window.TreeMenu = TreeMenu;

import BookmarkSearch from "./vue/bookmark/BookmarkSearch.vue";
Vue.component("BookmarkSearch", BookmarkSearch);
window.BookmarkSearch = BookmarkSearch;

import Bookmark from "./vue/bookmark/Bookmark.vue";
Vue.component("Bookmark", Bookmark);
window.Bookmark = Bookmark;

import BlobSelect from "./vue/blob/BlobSelect.vue";
Vue.component("BlobSelect", BlobSelect);
window.BlobSelect = BlobSelect;

import DrillTagProgress from "./vue/common/DrillTagProgress.vue";
Vue.component("DrillTagProgress", DrillTagProgress);
window.DrillTagProgress = DrillTagProgress;

import DrillBookmarks from "./vue/drill/DrillBookmarks.vue";
Vue.component("DrillBookmarks", DrillBookmarks);
window.DrillBookmarks = DrillBookmarks;

import DrillBlobs from "./vue/drill/DrillBlobs.vue";
Vue.component("DrillBlobs", DrillBlobs);
window.DrillBlobs = DrillBlobs;

import AddButton from "./vue/common/AddButton.vue";
Vue.component("AddButton", AddButton);
window.AddButton = AddButton;

import DropDownMenu from "./vue/common/DropDownMenu.vue";
Vue.component("DropDownMenu", DropDownMenu);
window.DropDownMenu = DropDownMenu;

import VueSidebarMenu from "vue-sidebar-menu";
import "vue-sidebar-menu/dist/vue-sidebar-menu.css";
Vue.use(VueSidebarMenu);

import AddToPlaylist from "./vue/music/AddToPlaylist.vue";
Vue.component("AddToPlaylist", AddToPlaylist);
window.AddToPlaylist = AddToPlaylist;

import CreateUpdatePlaylist from "./vue/music/CreateUpdatePlaylist.vue";
window.CreateUpdatePlaylist = CreateUpdatePlaylist;

import BlobDetailCover from "./vue/blob/BlobDetailCover.vue";
Vue.component("BlobDetailCover", BlobDetailCover);
window.BlobDetailCover = BlobDetailCover;

import AddToCollection from "./vue/blob/AddToCollection.vue";
Vue.component("AddToCollection", AddToCollection);
window.AddToCollection = AddToCollection;

import IconButton from "./vue/common/IconButton.vue";
Vue.component("IconButton", IconButton);
window.IconButton = IconButton;

import PerfectScrollbar from "perfect-scrollbar";
window.PerfectScrollbar = PerfectScrollbar;

import Pagination from "./vue/common/Pagination.vue";
Vue.component("Pagination", Pagination);
window.Pagination = Pagination;
