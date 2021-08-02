<template>
    <div class="notice-big alert alert-info d-flex">
        <h3>
            <font-awesome-icon icon="search" />
        </h3>
        <div class="message ml-3">
            <h3>
                <span>{{ title }}</span>
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
