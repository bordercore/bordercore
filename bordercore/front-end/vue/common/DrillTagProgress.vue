<template>
    <div class="me-0 text-center">
        <slot name="title-slot" />
        <div class="progress-circle">
            <svg width="120" height="120" viewBox="0 0 120 120">
                <circle class="circle-full" cx="60" cy="60" :r="circleRadius" fill="none" stroke-width="12" />
                <circle class="circle-partial" cx="60" cy="60" :r="circleRadius" fill="none" stroke-width="12" :stroke-dasharray="strokeDashArray" :stroke-dashoffset="getDashOffset()" />
                <text x="50%" y="50%" text-anchor="middle" dy=".3em" font-size="30px">{{ getProgress() }}%</text>
            </svg>
        </div>
        <span class="text-primary mt-2">{{ count }} {{ getPluralized }}</span>
    </div>
</template>

<script>

    export default {
        props: {
            count: {
                default: 0,
                type: Number,
            },
            progress: {
                default: 0.0,
                type: Number,
            },
        },
        setup(props) {
            const circleRadius = ref(54);

            function getDashOffset() {
                return strokeDashArray.value * (1 - props.progress/100);
            };

            function getProgress() {
                return Math.round(props.progress);
            };

            function getPluralized() {
                return pluralize("question", props.count);
            };

            const strokeDashArray = computed(() => {
                return 2 * 3.14 * circleRadius.value;
            });

            return {
                circleRadius,
                getDashOffset,
                getPluralized,
                getProgress,
                strokeDashArray,
            };
        },
    };

</script>
