<template>
    <a :href="getUrl">
        <div class="button-add">
            <font-awesome-icon icon="plus" class="text-emphasis"></font-awesome-icon>
        </div>
    </a>
</template>

<script>

    export default {
        props: {
            url: {
                default: "https://www.bordercore.com",
                type: String,
            },
        },
        computed: {
            getUrl() {
                return this.url;
            },
        },
    };

</script>
