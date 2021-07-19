<template>
    <div class="card-body">
        <slot name="title-slot">
            <div v-if="title" class="card-title">
                {{ title }}
                <slot name="top-right" />
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
        },
    };

</script>
