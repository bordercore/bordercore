import {createStore} from "vuex";

const drillStore = createStore({
    state: {
        showPythonConsole: false,
    },
    mutations: {
        updateShowPythonConsole(state, value) {
            state.showPythonConsole = value;
        },
    },
});

export default drillStore;
