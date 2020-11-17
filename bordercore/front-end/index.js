import Vue from "vue";
window.Vue = Vue;

import { AlertPlugin, ToastPlugin, VBHoverPlugin } from "bootstrap-vue"
Vue.use(AlertPlugin)
Vue.use(ToastPlugin)
Vue.use(VBHoverPlugin)

import DropdownMenu from "@innologica/vue-dropdown-menu";
Vue.component("DropdownMenu", DropdownMenu);

import draggable from "vuedraggable";
Vue.component("draggable", draggable);

import Vuex from "vuex";
window.Vuex = Vuex;
Vue.use(Vuex);

import VueTagsInput from "@johmun/vue-tags-input";
Vue.component("vue-tags-input", VueTagsInput);

import Datepicker from "vuejs-datepicker";
Vue.component("vuejs-datepicker", Datepicker);
window.Datepicker = Datepicker;

import axios from "axios";
window.axios = axios;

import $ from "jquery";
import jQuery from "jquery";
window.$ = $;
window.jQuery= jQuery;

import "bootstrap";

import { library } from "@fortawesome/fontawesome-svg-core";
import { faAlignLeft, faBars, faBookmark, faBriefcase, faCalendarAlt, faCopy, faEllipsisV, faHome, faGraduationCap, faMusic, faNewspaper, faPlus, faRunning, faSearch, faStickyNote, faTasks } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
library.add(faAlignLeft);
library.add(faBars);
library.add(faBookmark);
library.add(faBriefcase);
library.add(faCalendarAlt);
library.add(faCopy);
library.add(faEllipsisV);
library.add(faHome);
library.add(faGraduationCap);
library.add(faMusic);
library.add(faNewspaper);
library.add(faPlus);
library.add(faRunning);
library.add(faSearch);
library.add(faStickyNote);
library.add(faTasks);
Vue.component("font-awesome-icon", FontAwesomeIcon);

import { format } from "date-fns";
window.format = format;

import EasyMDE from "easymde";
window.EasyMDE = EasyMDE;

import { doGet, doPost } from "./util.js";
window.doGet = doGet;
window.doPost = doPost;

import SimpleSuggest from "./vue/common/SimpleSuggest.vue";
Vue.component("SimpleSuggest", SimpleSuggest);
window.SimpleSuggest = SimpleSuggest;
