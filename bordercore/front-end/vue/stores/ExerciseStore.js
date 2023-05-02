import {defineStore} from "pinia";

export const useExerciseStore = defineStore("exerciseStore", {
    state: () => ({
        activityInfo: {},
        relatedExercises: [],
        uuid: null,
    }),
});
