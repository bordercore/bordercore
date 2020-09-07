
import DropdownMenu from "@innologica/vue-dropdown-menu"

import draggable from "vuedraggable"

import Vuex from "vuex"
window.Vuex = Vuex
Vue.use(Vuex)

import VueSimpleSuggest from "vue-simple-suggest/dist/es6"
Vue.component("vue-simple-suggest", VueSimpleSuggest)

// Should we use export?
// export { capitalize, unique, longestDistinctSubstring };

// export default {
//     components: {
//         Vuex,
//         // DropdownMenu
//     }
// }
