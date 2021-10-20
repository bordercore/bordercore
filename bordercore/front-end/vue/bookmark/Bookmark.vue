<template>
    <div class="d-flex my-1">
        <div class="mr-2 mt-1">
            <font-awesome-icon icon="bookmark" class="text-light" />
        </div>
        <div class="d-flex flex-column">
            <h4>
                <font-awesome-icon v-if="importance > 1" icon="heart" class="favorite" data-toggle="tooltip" data-placement="bottom" title="Favorite" />
                <a :href="bookmark.url">{{ bookmark.name }}</a>
            </h4>
            <div class="d-flex mb-2 align-items-center text-primary">
                <img :src="'https://www.bordercore.com/favicons/' + getDomain + '.ico'" width="32" height="32">
                <div class="ml-2">
                    {{ getDomain }}
                </div>
            </div>
            <div>
                <a v-for="tag in bookmark.tags" :key="tag" :href="tagUrl.replace('666', tag)" class="tag">
                    {{ tag }}
                </a>
            </div>
        </div>
    </div>
</template>

<script>

    export default {
        props: {
            bookmark: {
                default: function() {
                },
                type: Object,
            },
            importance: {
                default: 1,
                type: Number,
            },
            tagUrl: {
                default: "",
                type: String,
            },
        },
        computed: {
            getDomain() {
                const {hostname} = new URL(this.bookmark.url);
                return hostname;
            },
        },
    };

</script>
