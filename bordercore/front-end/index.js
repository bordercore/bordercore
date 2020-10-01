import Vue from "vue";
window.Vue = Vue;

import { ToastPlugin, VBHoverPlugin } from "bootstrap-vue"
Vue.use(ToastPlugin)
Vue.use(VBHoverPlugin)

import DropdownMenu from "@innologica/vue-dropdown-menu";
Vue.component("DropdownMenu", DropdownMenu);

import draggable from "vuedraggable";
Vue.component("draggable", draggable);

import Vuex from "vuex";
window.Vuex = Vuex;
Vue.use(Vuex);

import VueSimpleSuggest from "vue-simple-suggest";
Vue.component("vue-simple-suggest", VueSimpleSuggest);

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

import "@fortawesome/fontawesome-free/js/fontawesome"
import "@fortawesome/fontawesome-free/js/solid"

import { format } from "date-fns";
window.format = format;

import EasyMDE from "easymde";
window.EasyMDE = EasyMDE;
