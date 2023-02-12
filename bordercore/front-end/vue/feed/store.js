import {createStore} from "vuex";

const store = createStore({
    state: {
        currentFeed: {},
    },
    mutations: {
        updateCurrentFeed(state, feed) {
            state.currentFeed = feed;
        },
    },
});

export default store;
