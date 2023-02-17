<template>
    <card title="" class="flex-grow-0 me-2 pt-3 backdrop-filter">
        <template #content>
            <div class="d-flex">
                <div>
                    <div class="btn-group" role="group" aria-label="Basic example">
                        <button type="button" class="btn btn-primary" :class="{'active': currentPlotType === 'reps' }" @click="switchPlot('reps')">
                            Reps
                        </button>
                        <button v-if="Object.keys(plotdata).includes('weight')" type="button" class="btn btn-primary" :class="{'active': currentPlotType === 'weight' }" @click="switchPlot('weight')">
                            Weight
                        </button>
                        <button v-if="Object.keys(plotdata).includes('duration')" type="button" class="btn btn-primary" :class="{'active': currentPlotType === 'duration' }" @click="switchPlot('duration')">
                            Duration
                        </button>
                    </div>
                </div>
                <h5 class="ms-auto">
                    <a v-if="paginator.has_previous" href="#" @click.prevent="paginate('prev')">
                        <font-awesome-icon icon="chevron-left" class="text-emphasis glow icon-hover" />
                    </a>
                    <span v-else>
                        <font-awesome-icon icon="chevron-left" class="text-emphasis icon-disabled" />
                    </span>
                    <a v-if="paginator.has_next" href="#" class="ms-1" @click.prevent="paginate('next')">
                        <font-awesome-icon icon="chevron-right" class="text-emphasis glow icon-hover" />
                    </a>
                    <span v-else>
                        <font-awesome-icon icon="chevron-right" class="text-emphasis icon-disabled" />
                    </span>
                </h5>
            </div>
            <canvas id="exercise-detail-chart" class="w-100" />
            <div v-if="hasNote" id="fitness-has-note">
                * workout note
            </div>
        </template>
    </card>
</template>

<script>

    import {capitalizeFirstLetter} from "/front-end/util.js";
    import Card from "/front-end/vue/common/Card.vue";
    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

    export default {
        components: {
            Card,
            FontAwesomeIcon,
        },
        props: {
            date: {
                default: "",
                type: String,
            },
            latestDuration: {
                default: () => [],
                type: Array,
            },
            latestReps: {
                default: () => [],
                type: Array,
            },
            latestWeight: {
                default: () => [],
                type: Array,
            },
            initialPlotType: {
                default: "",
                type: String,
            },
            notes: {
                default: () => [],
                type: Array,
            },
            initialPaginator: {
                default: function() {},
                type: Object,
            },
            plotdata: {
                default: function() {},
                type: Object,
            },
            labels: {
                default: function() {},
                type: Object,
            },
            getWorkoutDataUrl: {
                default: "",
                type: String,
            },
        },
        setup(props) {
            const currentPlotType = ref(props.initialPlotType);
            const notes = ref(props.notes);
            const paginator = ref(props.initialPaginator);
            const plotdata = ref(props.plotdata);
            const hasNote = computed(() => {
                return notes.value.filter((x) => x !== null).length > 0;
            });

            function paginate(direction) {
                const pageNumber = direction === "prev" ?
                    paginator.value.previous_page_number :
                    paginator.value.next_page_number;

                doGet(
                    null,
                    props.getWorkoutDataUrl + pageNumber,
                    (response) => {
                        plotdata.value = JSON.parse(response.data.workout_data.plotdata);
                        notes.value = JSON.parse(response.data.workout_data.notes);
                        myChart.data.labels = JSON.parse(response.data.workout_data.labels);
                        myChart.data.datasets[0].data = JSON.parse(response.data.workout_data.plotdata)[currentPlotType.value].map(firstSet);
                        myChart.update();
                        paginator.value = JSON.parse(response.data.workout_data.paginator);
                    },
                    "Error getting workout data",
                );
            };

            function switchPlot(dataset) {
                currentPlotType.value = dataset;
                myChart.data.datasets[0].data = plotdata.value[dataset].map(firstSet);
                myChart.options.scales.y.title.text = capitalizeFirstLetter(dataset);
                myChart.update();
            };

            let myChart = null;

            onMounted(() => {
                const scaleYText = capitalizeFirstLetter(currentPlotType.value);
                const styles = getComputedStyle(document.body);
                const ctx = document.getElementById("exercise-detail-chart").getContext("2d");

                myChart = new Chart(ctx, {
                    type: "bar",
                    data: {
                        labels: props.labels,
                        datasets: [
                            {
                                data: plotdata.value[currentPlotType.value].map(firstSet),
                                barThickness: 40,
                                backgroundColor: function(context) {
                                    const chart = context.chart;
                                    const {ctx, chartArea} = chart;

                                    if (!chartArea) {
                                        // This case happens on initial chart load
                                        return;
                                    }
                                    return getGradient(plotdata.value[currentPlotType.value].length);
                                },
                            },
                        ],
                    },
                    options: {
                        borderRadius: "10",
                        animation: {
                            onProgress: function(chartInstance) {
                                const ctx = this.ctx;
                                ctx.textAlign = "center";
                                ctx.textBaseline = "bottom";
                                ctx.fillStyle = styles.getPropertyValue("--chart-fill-color");
                                ctx.font="bold 18px Arial";

                                this.data.datasets.forEach(function(dataset, i) {
                                    const meta = chartInstance.chart.getDatasetMeta(i);
                                    meta.data.forEach(function(bar, index) {
                                        const data = dataset.data[index];
                                        const note = notes[index];
                                        ctx.fillText(data + (note ? "\n*" : ""), bar.x, bar.y + 30);
                                    });
                                });
                            },
                        },
                        plugins: {
                            title: {
                                display: true,
                                text: "Workout Data",
                                color: styles.getPropertyValue("--chart-title-color"),
                                font: {
                                    family: "Lato",
                                    size: 48,
                                    weight: "normal",
                                },
                            },
                            legend: {
                                display: false,
                            },
                            tooltip: {
                                callbacks: {
                                    label(tooltipItem) {
                                        return null;
                                    },
                                    title(tooltipItem) {
                                        const data = plotdata.value[currentPlotType.value][tooltipItem[0].dataIndex];
                                        const note = notes[tooltipItem[0].dataIndex];
                                        return `${capitalizeFirstLetter(currentPlotType.value)}: ${data}` + (note ? `\nNote: ${note}` : "");
                                    },
                                },
                                titleMarginBottom: 0,
                                titleFont: {
                                    size: 18,
                                },
                            },
                        },
                        scales: {
                            x: {
                                grid: {
                                    color: "#21295c",
                                },
                                ticks: {
                                    color: styles.getPropertyValue("--chart-tick-color"),
                                    font: {
                                        family: "Poppins",
                                        size: 16,
                                    },
                                },
                            },
                            y: {
                                grid: {
                                    color: "#21295c",
                                },
                                title: {
                                    display: true,
                                    text: scaleYText,
                                    color: styles.getPropertyValue("--chart-title-color"),
                                    font: {
                                        family: "Poppins",
                                        size: 24,
                                    },
                                },
                                ticks: {
                                    color: styles.getPropertyValue("--chart-tick-color"),
                                    font: {
                                        family: "Poppins",
                                        size: 16,
                                    },
                                },
                            },
                        },
                        font: {
                            size: 14,
                        },
                    },
                });

                const sets = Array.apply(0, Array(props.latestWeight.length)).map(function(_, b) {
                    return b + 1;
                });
                const labels = sets.map((x) => `Set ${x}`);

                const ctxLastWorkout = document.getElementById("last_workout_weights").getContext("2d");
                new Chart(ctxLastWorkout, {
                    type: "bar",
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                backgroundColor: styles.getPropertyValue("--chart-bg"),
                                data: props.latestWeight,
                                label: "Weight",
                            },
                        ],
                    },
                    options: getRecentWorkoutGraphOptions("Weight"),
                });

                const ctxLastWorkoutReps = document.getElementById("last_workout_reps").getContext("2d");
                new Chart(ctxLastWorkoutReps, {
                    type: "bar",
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                backgroundColor: styles.getPropertyValue("--chart-bg"),
                                data: props.latestReps,
                                label: "Reps",
                            },
                        ],
                    },
                    options: getRecentWorkoutGraphOptions("Reps"),

                });

                const ctxLastWorkoutDuration = document.getElementById("last_workout_duration").getContext("2d");
                new Chart(ctxLastWorkoutDuration, {
                    type: "bar",
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                backgroundColor: styles.getPropertyValue("--chart-bg"),
                                data: props.latestDuration,
                                label: "Duration",
                            },
                        ],
                    },
                    options: getRecentWorkoutGraphOptions("Duration"),
                });
            });

            return {
                currentPlotType,
                hasNote,
                paginate,
                paginator,
                switchPlot,
            };
        },
    };

</script>
