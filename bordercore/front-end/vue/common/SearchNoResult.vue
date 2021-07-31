<template>
    <div class="notice-big alert alert-info">
        <h3>
            <font-awesome-icon icon="search" />
            <span class="ml-2">{{ title }}</span>
        </h3>
        <div class="message">
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
