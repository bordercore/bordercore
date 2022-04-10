<template>
    <div class="card-body">
        <slot name="title-slot">
            <div v-if="title" class="card-title d-flex">
                {{ title }}
                <div class="ms-auto">
                    <slot name="top-right" />
                </div>
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
