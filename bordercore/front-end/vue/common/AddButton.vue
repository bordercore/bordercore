<template>
    <a @click="clickHandler">
        <div class="button-add">
            <font-awesome-icon icon="plus" />
        </div>
    </a>
</template>

<script>

    export default {
        props: {
            clickHandler: {
                default: () => {},
                type: Function,
            },
        },
    };

</script>
