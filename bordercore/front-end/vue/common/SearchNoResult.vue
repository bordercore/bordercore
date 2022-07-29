<template>
    <div class="notice-big alert d-flex">
        <h3>
            <font-awesome-icon icon="search" />
        </h3>
        <div class="message ms-2">
            <h3>
                {{ title }}
            </h3>
            <slot name="message" />
        </div>
    </div>
</template>

<script>

    export default {
        props: {
            title: {
                default: "Nothing found",
                type: String,
            },
        },
    };

</script>
