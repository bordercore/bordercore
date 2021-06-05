<template>
    <div class="card-body" :class="className">
        <slot name="title-slot">
            <div class="card-title" v-if="title">
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

    export default {
        props: {
            title: {
                default: "Card Title",
                type: String,
            },
            className: {
                default: "",
                type: String,
            },
        },
    };

</script>
