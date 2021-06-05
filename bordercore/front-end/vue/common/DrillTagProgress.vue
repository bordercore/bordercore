<template>
    <div class="mr-5 text-center">
        <slot name="title-slot">
        </slot>
    <div class="progress-circle">
      <svg width="120" height="120" viewBox="0 0 120 120">
        <circle cx="60" cy="60" :r="circleRadius" fill="none" stroke-width="12" />
        <circle cx="60" cy="60" :r="circleRadius" fill="none" stroke="#7fffd4" stroke-width="12" :stroke-dasharray="strokeDashArray" :stroke-dashoffset="getDashOffset()" />
        <text x="50%" y="50%" text-anchor="middle" dy=".3em" font-size="30px">{{ getProgress() }}%</text>
      </svg>
    </div>
    <span class="text-primary mt-2">{{ count }} {{ getPluralized() }}</span>
  </div>
</template>

<script>

    export default {
        props: {
            count: {
                default: 0,
            },
            progress: {
                default: 0.0,
            },
        },
        data() {
            return {
                circleRadius: 54,
            };
        },
        computed: {
            strokeDashArray: function() {
                return 2 * 3.14 * this.circleRadius;
            },
        },
        methods: {
            getDashOffset(progress) {
                return this.strokeDashArray * (1 - this.progress/100);
            },
            getProgress: function() {
                return Math.round(this.progress);
            },
            getPluralized: function() {
                return pluralize("question", this.count);
            },
        },
    };

</script>
