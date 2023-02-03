import Vue from "vue";
window.Vue = Vue;

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

import FloatingVue from "floating-vue";
Vue.use(FloatingVue);
// Allow the user to hover over the tooltip content
FloatingVue.options.popperTriggers = ["hover"];

import pluralize from "pluralize";
window.pluralize = pluralize;

import axios from "axios";
window.axios = axios;
axios.defaults.xsrfCookieName = "csrftoken";
axios.defaults.xsrfHeaderName = "X-CSRFTOKEN";

import "bootstrap";
import {Dropdown, Modal, Tab} from "bootstrap";
window.Dropdown = Dropdown;
window.Modal = Modal;
window.Tab = Tab;

import {library} from "@fortawesome/fontawesome-svg-core";
import {faAlignLeft, faAngleDown, faAngleRight, faArrowsAltH, faExchangeAlt, faBars, faBook, faBookmark, faBox, faBriefcase, faCalendarAlt, faCaretUp, faChartBar, faCheck, faChevronLeft, faChevronRight, faChevronUp, faClone, faCopy, faDownload, faEllipsisV, faExclamationTriangle, faFileAlt, faFileImport, faHeart, faHome, faImage, faImages, faInfo, faGraduationCap, faLink, faList, faLock, faMusic, faNewspaper, faObjectGroup, faPencilAlt, faPlus, faQuestion, faQuoteLeft, faRandom, faRunning, faSearch, faSignOutAlt, faSplotch, faSquareRootAlt, faStar, faStickyNote, faTags, faTasks, faThumbtack, faTimes, faTimesCircle, faTrashAlt} from "@fortawesome/free-solid-svg-icons";
import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";
import {faAws} from "@fortawesome/free-brands-svg-icons";
import {faPython} from "@fortawesome/free-brands-svg-icons";
library.add(faAlignLeft);
library.add(faAngleDown);
library.add(faAngleRight);
library.add(faArrowsAltH);
library.add(faAws);
library.add(faExchangeAlt);
library.add(faBars);
library.add(faBookmark);
library.add(faBook);
library.add(faBox);
library.add(faBriefcase);
library.add(faCalendarAlt);
library.add(faCaretUp);
library.add(faChartBar);
library.add(faCheck);
library.add(faChevronLeft);
library.add(faChevronRight);
library.add(faChevronUp);
library.add(faClone);
library.add(faCopy);
library.add(faDownload);
library.add(faEllipsisV);
library.add(faExclamationTriangle);
library.add(faFileAlt);
library.add(faFileImport);
library.add(faHeart);
library.add(faHome);
library.add(faImage);
library.add(faImages);
library.add(faInfo);
library.add(faGraduationCap);
library.add(faLink);
library.add(faList);
library.add(faLock);
library.add(faMusic);
library.add(faNewspaper);
library.add(faObjectGroup);
library.add(faPencilAlt);
library.add(faPlus);
library.add(faPython);
library.add(faQuestion);
library.add(faQuoteLeft);
library.add(faRandom);
library.add(faRunning);
library.add(faSearch);
library.add(faSquareRootAlt);
library.add(faStar);
library.add(faStickyNote);
library.add(faTags);
library.add(faSignOutAlt);
library.add(faSplotch);
library.add(faTasks);
library.add(faThumbtack);
library.add(faTimes);
library.add(faTimesCircle);
library.add(faTrashAlt);
Vue.component("font-awesome-icon", FontAwesomeIcon);

import {format} from "date-fns";
window.format = format;

import markdownit from "markdown-it";
window.markdown = markdownit();

import "media-chrome";

import {v4 as uuidv4} from "uuid";
window.uuidv4 = uuidv4;

import {
    getReasonPhrase,
} from "http-status-codes";
window.getReasonPhrase = getReasonPhrase;

import {doGet, doPost, doPut, getFormattedDate, animateCSS} from "./util.js";
window.doGet = doGet;
window.doPost = doPost;
window.doPut = doPut;
window.getFormattedDate = getFormattedDate;
window.animateCSS = animateCSS;

import EditableTextArea from "./vue/common/EditableTextArea.vue";
Vue.component("EditableTextArea", EditableTextArea);

import SelectValue from "./vue/common/SelectValue.vue";
import "vue-multiselect/dist/vue-multiselect.min.css";
Vue.component("SelectValue", SelectValue);

import SearchResult from "./vue/search/SearchResult.vue";
Vue.component("SearchResult", SearchResult);

import TopSearch from "./vue/search/TopSearch.vue";
Vue.component("TopSearch", TopSearch);

import OverdueTasks from "./vue/todo/OverdueTasks.vue";
Vue.component("OverdueTasks", OverdueTasks);

import vSelect from "vue-select";
import "vue-select/dist/vue-select.css";
Vue.component("v-select", vSelect);

import TagsInput from "./vue/common/TagsInput.vue";
Vue.component("TagsInput", TagsInput);

import SearchTagsInput from "./vue/common/SearchTagsInput.vue";
Vue.component("SearchTagsInput", SearchTagsInput);

import RelatedTags from "./vue/common/RelatedTags.vue";
Vue.component("RelatedTags", RelatedTags);

import Card from "./vue/common/Card.vue";
Vue.component("Card", Card);

import SearchNoResult from "./vue/common/SearchNoResult.vue";
Vue.component("SearchNoResult", SearchNoResult);

import TreeMenu from "./vue/common/TreeMenu.vue";
Vue.component("TreeMenu", TreeMenu);

import RelatedBookmarksList from "./vue/bookmark/RelatedBookmarksList.vue";
Vue.component("RelatedBookmarksList", RelatedBookmarksList);

import RelatedObjects from "./vue/common/RelatedObjects.vue";
Vue.component("RelatedObjects", RelatedObjects);

import DrillTagProgress from "./vue/common/DrillTagProgress.vue";
Vue.component("DrillTagProgress", DrillTagProgress);

import DropDownMenu from "./vue/common/DropDownMenu.vue";
Vue.component("DropDownMenu", DropDownMenu);

import VueSidebarMenu from "vue-sidebar-menu";
Vue.use(VueSidebarMenu);

import AddToPlaylist from "./vue/music/AddToPlaylist.vue";
Vue.component("AddToPlaylist", AddToPlaylist);

import AudioPlayer from "./vue/music/AudioPlayer.vue";
Vue.component("AudioPlayer", AudioPlayer);

import CreateUpdatePlaylist from "./vue/music/CreateUpdatePlaylist.vue";
Vue.component("CreateUpdatePlaylist", CreateUpdatePlaylist);

import BlobDetailCover from "./vue/blob/BlobDetailCover.vue";
Vue.component("BlobDetailCover", BlobDetailCover);

import RecentBlobs from "./vue/blob/RecentBlobs.vue";
Vue.component("RecentBlobs", RecentBlobs);

import CreateUpdateFeed from "./vue/feed/CreateUpdateFeed.vue";
Vue.component("CreateUpdateFeed", CreateUpdateFeed);

import CreateUpdateTodo from "./vue/todo/CreateUpdateTodo.vue";
Vue.component("CreateUpdateTodo", CreateUpdateTodo);

import AddToCollection from "./vue/blob/AddToCollection.vue";
Vue.component("AddToCollection", AddToCollection);

import NodeImage from "./vue/node/NodeImage.vue";
Vue.component("NodeImage", NodeImage);

import NodeImageModal from "./vue/node/NodeImageModal.vue";
Vue.component("NodeImageModal", NodeImageModal);

import NodeQuote from "./vue/node/NodeQuote.vue";
Vue.component("NodeQuote", NodeQuote);

import NodeQuoteModal from "./vue/node/NodeQuoteModal.vue";
Vue.component("NodeQuoteModal", NodeQuoteModal);

import NodeNote from "./vue/node/NodeNote.vue";
Vue.component("NodeNote", NodeNote);

import NodeNoteModal from "./vue/node/NodeNoteModal.vue";
Vue.component("NodeNoteModal", NodeNoteModal);

import NodeTodoList from "./vue/node/NodeTodoList.vue";
Vue.component("NodeTodoList", NodeTodoList);

import NoteModal from "./vue/common/NoteModal.vue";
Vue.component("NoteModal", NoteModal);

import CollectionObjectList from "./vue/collection/CollectionObjectList.vue";
Vue.component("CollectionObjectList", CollectionObjectList);

import CollectionObjectListModal from "./vue/collection/CollectionObjectListModal.vue";
Vue.component("CollectionObjectListModal", CollectionObjectListModal);

import IconButton from "./vue/common/IconButton.vue";
Vue.component("IconButton", IconButton);

import ObjectSelect from "./vue/common/ObjectSelect.vue";
Vue.component("ObjectSelect", ObjectSelect);

import PerfectScrollbar from "perfect-scrollbar";
window.PerfectScrollbar = PerfectScrollbar;

import Pagination from "./vue/common/Pagination.vue";
Vue.component("Pagination", Pagination);

import PythonConsole from "./vue/common/PythonConsole.vue";
Vue.component("PythonConsole", PythonConsole);

import Toast from "./vue/common/Toast.vue";
Vue.component("Toast", Toast);

import {BarController, BarElement, Chart, CategoryScale, LinearScale, Title, Tooltip} from "chart.js";
window.Chart = Chart;
Chart.register(
    BarController,
    BarElement,
    CategoryScale,
    LinearScale,
    Title,
    Tooltip,
);

import Rainbow from "rainbowvis.js";
window.Rainbow = Rainbow;

import Prism from "prismjs";
import {addCopyButton} from "./util.js";
addCopyButton();

import "animate.css";

import hotkeys from "hotkeys-js";

import Oruga from "@oruga-ui/oruga";
import "@oruga-ui/oruga/dist/oruga-full.css";
import "@oruga-ui/oruga/dist/oruga-full-vars.css";

Vue.use(Oruga, {
    iconComponent: "font-awesome-icon",
    iconPack: "fa",
    table: {
        sortIcon: "caret-up",
    },
});

// Wait 10 seconds after selecting a song to play
//  for it to be marked as "listened to".
window.MUSIC_LISTEN_TIMEOUT = 10000;

import VMdEditor from "@kangc/v-md-editor";
import enUS from "@kangc/v-md-editor/lib/lang/en-US";
import "@kangc/v-md-editor/lib/style/base-editor.css";
import prismTheme from "@kangc/v-md-editor/lib/theme/prism.js";
import "@kangc/v-md-editor/lib/theme/style/github.css";

VMdEditor.use(prismTheme, {
    Prism,
});
Vue.use(VMdEditor);
VMdEditor.lang.use("en-US", enUS);
