<template>
    <div class="card-body">
        <slot name="title-slot">
            <div class="card-title">
                {{ title }}
                <slot name="top-right">
                </slot>
            </div>
        </slot>
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
