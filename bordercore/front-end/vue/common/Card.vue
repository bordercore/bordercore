<template>
    <div class="card-body">
        <div class="card-title">
        {{ title }}
        </div>
        <slot name="content" class="card-content">
        Insert your content here
        </slot>
    </div>
</template>

<script>

    import Vue from "vue";

    export default {
        props: {
            title: {
                default: "Card Title",
                type: String
            }
        }
    };

</script>
