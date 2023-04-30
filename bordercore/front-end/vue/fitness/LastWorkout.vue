<template>
    <div>
        <card title="" class="flex-grow-0 backdrop-filter">
            <template #title-slot>
                <div class="card-title text-primary">
                    Last Workout
                </div>
            </template>
            <template #content>
                <div class="mb-4">
                    <div v-if="date">
                        <strong>
                            {{ date }} - {{ interval }} {{ pluralize("day", interval) }} ago
                        </strong>
                    </div>
                    <div v-else>
                        No previous workout found.
                    </div>
                    <canvas v-show="weight[0] > 0" id="last_workout_weights" class="mt-3" />
                    <canvas v-show="duration[0] > 0" id="last_workout_duration" class="mt-3" />
                    <canvas id="last_workout_reps" class="mt-3" />
                </div>
            </template>
        </card>
        <div class="hover-target flex-grow-1 mb-3">
            <card title="" class="z-index-positive position-relative h-100 backdrop-filter">
                <template #content>
                    <div class="d-flex flex-column">
                        <div class="d-flex flex-column">
                            <div class="d-flex">
                                <div class="card-title text-primary">
                                    Description
                                </div>
                                <drop-down-menu :show-on-hover="true">
                                    <template #dropdown>
                                        <li>
                                            <a class="dropdown-item" href="#" @click.prevent="handleNoteAdd()">
                                                <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />
                                                <span v-html="note ? 'Edit' : 'Add'" /> note
                                            </a>
                                        </li>
                                        <li>
                                            <a v-if="note" class="dropdown-item" href="#" @click.prevent="note=''">
                                                <font-awesome-icon icon="trash-alt" class="text-primary me-3" />
                                                Delete note
                                            </a>
                                        </li>
                                    </template>
                                </drop-down-menu>
                            </div>
                            <div v-html="description" />
                        </div>
                        <hr v-if="description && note" class="m-2">
                        <editable-text-area
                            ref="editableTextArea"
                            v-model="note"
                            extra-class=""
                            :hide-add-button="true"
                        >
                            <template #:title>
                                <div class="card-title text-primary mt-3">
                                    Note
                                </div>
                            </template>
                        </editable-text-area>
                    </div>
                </template>
            </card>
        </div>
    </div>
</template>

<script>

    import Card from "/front-end/vue/common/Card.vue";
    import DropDownMenu from "/front-end/vue/common/DropDownMenu.vue";
    import EditableTextArea from "/front-end/vue/common/EditableTextArea.vue";
    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

    export default {
        components: {
            Card,
            DropDownMenu,
            EditableTextArea,
            FontAwesomeIcon,
        },
        props: {
            date: {
                default: "",
                type: String,
            },
            description: {
                default: "",
                type: String,
            },
            exerciseUuid: {
                default: "",
                type: String,
            },
            initialNote: {
                default: "",
                type: String,
            },
            duration: {
                default: () => [],
                type: Array,
            },
            reps: {
                default: () => [],
                type: Array,
            },
            weight: {
                default: () => [],
                type: Array,
            },
            interval: {
                default: "",
                type: String,
            },
            updateNoteUrl: {
                default: "",
                type: String,
            },
        },
        setup(props) {
            const editableTextArea = ref(null);
            const note = ref(props.initialNote);

            const sets = Array.apply(0, Array(props.weight.length)).map(function(_, b) {
                return b + 1;
            });

            const labels = sets.map((x) => `Set ${x}`);

            function createChart(id, data, label) {
                const styles = getComputedStyle(document.body);
                const context = document.getElementById(id).getContext("2d");
                new Chart(context, {
                    type: "bar",
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                backgroundColor: styles.getPropertyValue("--chart-bg"),
                                data: data,
                                label: label,
                            },
                        ],
                    },
                    options: getRecentWorkoutGraphOptions(label),
                });
            };

            function handleNoteAdd() {
                editableTextArea.value.editNote(!note.value);
            };

            function handleNoteUpdate() {
                doPost(
                    props.updateNoteUrl,
                    {
                        "uuid": props.exerciseUuid,
                        "note": note.value,
                    },
                    () => {},
                );
            };

            watch(note, (newValue) => {
                if (newValue !== null) {
                    handleNoteUpdate();
                }
            });

            onMounted(() => {
                createChart("last_workout_weights", props.weight, "Weight");
                createChart("last_workout_reps", props.reps, "Reps");
                createChart("last_workout_duration", props.duration, "Duration");
            });

            return {
                editableTextArea,
                handleNoteAdd,
                note,
                pluralize,
            };
        },
    };

</script>
