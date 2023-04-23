import {defineStore} from "pinia";

export const useBaseStore = defineStore("baseStore", {
    state: () => ({
        sidebarCollapsed: true,
    }),
});
