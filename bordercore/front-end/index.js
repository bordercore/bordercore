import {plugin as Slicksort} from "vue-slicksort";
window.Slicksort = Slicksort;
import {SlickList, SlickItem} from "vue-slicksort";
window.SlickList = SlickList;
window.SlickItem = SlickItem;

import {computed, createApp, h, nextTick, onMounted, reactive, ref, watch} from "vue";
window.computed = computed;
window.createApp = createApp;
window.h = h;
window.nextTick = nextTick;
window.onMounted = onMounted;
window.reactive = reactive;
window.ref = ref;
window.watch = watch;

// Vue composables
import mouseRating from "./useMouseRating.js";
window.mouseRating = mouseRating;

// Use the tiny-emitter package as an event bus
import emitter from "tiny-emitter/instance";

const EventBus = {
  $on: (...args) => emitter.on(...args),
  $once: (...args) => emitter.once(...args),
  $off: (...args) => emitter.off(...args),
    $emit: (...args) => emitter.emit(...args),
};
window.EventBus = EventBus;

import draggable from "vuedraggable";
window.draggable = draggable;

import Sortable from "sortablejs";
window.Sortable = Sortable;

import {defineStore} from "pinia";
window.defineStore = defineStore;

import {createStore, useStore} from "vuex";
window.createStore = createStore;
window.useStore = useStore;

import Datepicker from "vue3-datepicker";
window.Datepicker = Datepicker;

import FloatingVue from "floating-vue";
// Allow the user to hover over the tooltip content
FloatingVue.options.popperTriggers = ["hover"];
window.FloatingVue = FloatingVue;

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
import {faAlignLeft, faAngleDown, faAngleRight, faArrowsAltH, faExchangeAlt, faBars, faBook, faBookmark, faBox, faBriefcase, faCalendarAlt, faCaretUp, faChartBar, faCheck, faChevronLeft, faChevronRight, faChevronUp, faClone, faCopy, faDownload, faEllipsisV, faExclamationTriangle, faFileAlt, faFileImport, faGripHorizontal, faHeart, faHome, faImage, faImages, faInfo, faGraduationCap, faLink, faList, faLock, faMusic, faNewspaper, faObjectGroup, faPencilAlt, faPlus, faQuestion, faQuoteLeft, faRandom, faRunning, faSearch, faSignOutAlt, faSplotch, faSquareRootAlt, faStar, faStickyNote, faTags, faTasks, faThumbtack, faTimes, faTimesCircle, faTrashAlt, faUser} from "@fortawesome/free-solid-svg-icons";
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
library.add(faGripHorizontal);
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
library.add(faUser);
window.FontAwesomeIcon = FontAwesomeIcon;

import {format} from "date-fns";
window.format = format;

import {cloneDeep, isEqual} from "lodash";
window.cloneDeep = cloneDeep;
window.isEqual = isEqual;

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
window.EditableTextArea= EditableTextArea;

import SelectValue from "./vue/common/SelectValue.vue";
import "vue-multiselect/dist/vue-multiselect.css";
window.SelectValue = SelectValue;

import SearchResult from "./vue/search/SearchResult.vue";
window.SearchResult = SearchResult;

import TagSearchResult from "./vue/search/TagSearchResult.vue";
window.TagSearchResult = TagSearchResult;

import TopSearch from "./vue/search/TopSearch.vue";
window.TopSearch = TopSearch;

import OverdueTasks from "./vue/todo/OverdueTasks.vue";
window.OverdueTasks = OverdueTasks;

import vSelect from "vue-select";
import "vue-select/dist/vue-select.css";

import TagsInput from "./vue/common/TagsInput.vue";
window.TagsInput = TagsInput;

import RelatedTags from "./vue/common/RelatedTags.vue";
window.RelatedTags = RelatedTags;

import BackReferences from "./vue/common/BackReferences.vue";
window.BackReferences = BackReferences;

import Card from "./vue/common/Card.vue";
window.Card = Card;

import SearchNoResult from "./vue/common/SearchNoResult.vue";
window.SearchNoResult = SearchNoResult;

import TreeMenu from "./vue/common/TreeMenu.vue";
window.TreeMenu = TreeMenu;

import PinnedTags from "./vue/bookmark/PinnedTags.vue";
window.PinnedTags = PinnedTags;

import RelatedObjects from "./vue/common/RelatedObjects.vue";
window.RelatedObjects = RelatedObjects;

import DrillTagProgress from "./vue/common/DrillTagProgress.vue";
window.DrillTagProgress = DrillTagProgress;
import drillStore from "./vue/drill/store.js";
window.drillStore = drillStore;

import DropDownMenu from "./vue/common/DropDownMenu.vue";
window.DropDownMenu = DropDownMenu;

import {RouterLink} from "vue-router";
window.RouterLink = RouterLink;

import {SidebarMenu} from "vue-sidebar-menu";
import "vue-sidebar-menu/dist/vue-sidebar-menu.css";
window.SidebarMenu = SidebarMenu;

import AddToPlaylist from "./vue/music/AddToPlaylist.vue";
window.AddToPlaylist = AddToPlaylist;

import AudioPlayer from "./vue/music/AudioPlayer.vue";
window.AudioPlayer = AudioPlayer;

import CreateUpdatePlaylist from "./vue/music/CreateUpdatePlaylist.vue";
window.CreateUpdatePlaylist = CreateUpdatePlaylist;

import BlobDetailCover from "./vue/blob/BlobDetailCover.vue";
window.BlobDetailCover = BlobDetailCover;

import RecentBlobs from "./vue/blob/RecentBlobs.vue";
window.RecentBlobs = RecentBlobs;

import CreateUpdateFeed from "./vue/feed/CreateUpdateFeed.vue";
window.CreateUpdateFeed = CreateUpdateFeed;
import FeedInfo from "./vue/feed/FeedInfo.vue";
window.FeedInfo = FeedInfo;
import FeedItemList from "./vue/feed/FeedItemList.vue";
window.FeedItemList = FeedItemList;
import FeedList from "./vue/feed/FeedList.vue";
window.FeedList = FeedList;
import feedStore from "./vue/feed/store.js";
window.feedStore = feedStore;

import CreateUpdateTodo from "./vue/todo/CreateUpdateTodo.vue";
window.CreateUpdateTodo = CreateUpdateTodo;

import AddToCollection from "./vue/blob/AddToCollection.vue";
window.AddToCollection = AddToCollection;

import NodeImage from "./vue/node/NodeImage.vue";
window.NodeImage = NodeImage;

import NodeImageModal from "./vue/node/NodeImageModal.vue";
window.NodeImageModal = NodeImageModal;

import NodeQuote from "./vue/node/NodeQuote.vue";
window.NodeQuote = NodeQuote;

import NodeQuoteModal from "./vue/node/NodeQuoteModal.vue";
window.NodeQuoteModal = NodeQuoteModal;

import NodeNote from "./vue/node/NodeNote.vue";
window.NodeNote = NodeNote;

import NodeNoteModal from "./vue/node/NodeNoteModal.vue";
window.NodeNoteModal = NodeNoteModal;

import NodeTodoList from "./vue/node/NodeTodoList.vue";
window.NodeTodoList = NodeTodoList;

import CollectionObjectList from "./vue/collection/CollectionObjectList.vue";
window.CollectionObjectList = CollectionObjectList;

import CollectionObjectListModal from "./vue/collection/CollectionObjectListModal.vue";
window.CollectionObjectListModal = CollectionObjectListModal;

import IconButton from "./vue/common/IconButton.vue";
window.IconButton = IconButton;

import ObjectSelect from "./vue/common/ObjectSelect.vue";
window.ObjectSelect = ObjectSelect;

import PerfectScrollbar from "perfect-scrollbar";
window.PerfectScrollbar = PerfectScrollbar;

import Pagination from "./vue/common/Pagination.vue";
window.Pagination = Pagination;

import PythonConsole from "./vue/common/PythonConsole.vue";
window.PythonConsole = PythonConsole;

import AddWorkoutForm from "./vue/fitness/AddWorkoutForm.vue";
window.AddWorkoutForm = AddWorkoutForm;
import WorkoutGraph from "./vue/fitness/WorkoutGraph.vue";
window.WorkoutGraph = WorkoutGraph;

import Toast from "./vue/common/Toast.vue";
window.Toast = Toast;

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

import Oruga from "@oruga-ui/oruga-next";
import "@oruga-ui/oruga-next/dist/oruga-full.css";
import "@oruga-ui/oruga-next/dist/oruga-full-vars.css";
window.Oruga = Oruga;

// Wait 10 seconds after selecting a song to play
//  for it to be marked as "listened to".
window.MUSIC_LISTEN_TIMEOUT = 10000;

import VueMarkdownEditor from "@kangc/v-md-editor";
import enUS from "@kangc/v-md-editor/lib/lang/en-US";
import "@kangc/v-md-editor/lib/style/base-editor.css";
import vuepressTheme from "@kangc/v-md-editor/lib/theme/vuepress.js";
import "@kangc/v-md-editor/lib/theme/style/vuepress.css";
VueMarkdownEditor.use(vuepressTheme, {
    Prism,
});
VueMarkdownEditor.lang.use("en-US", enUS);
window.VueMarkdownEditor = VueMarkdownEditor;
