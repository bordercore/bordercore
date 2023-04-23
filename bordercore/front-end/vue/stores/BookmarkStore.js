import {defineStore} from "pinia";

export const useBookmarkStore = defineStore("bookmarkStore", {
    state: () => ({
        selectedTagName: null,
    }),
});
