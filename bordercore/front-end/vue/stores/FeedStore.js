import {defineStore} from "pinia";

export const useFeedStore = defineStore("feedStore", {
    state: () => ({
        currentFeed: {},
    }),
});
