<template>
    <div class="d-flex my-1">
        <div class="search-result-icon">
            <font-awesome-icon :icon="icon" class="fa-lg text-light" />
        </div>
        <slot name="image" />
        <div class="d-flex flex-column ms-2">
            <h4 class="d-flex align-items-center">
                <a class="truncate-text" :href="url" v-html="title" />
                <font-awesome-icon v-if="importance > 1" icon="heart" class="favorite ms-2" data-bs-toggle="tooltip" data-placement="bottom" title="Favorite" />
            </h4>
            <slot name="extra" />
            <div>
                <a v-for="tag in tags" :key="tag" :href="tagUrl.replace('666', tag)" class="tag">
                    {{ tag }}
                </a>
            </div>
        </div>
    </div>
</template>

<script>

    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

    export default {
        components: {
            FontAwesomeIcon,
        },
        props: {
            icon: {
                default: "",
                type: String,
            },
            importance: {
                default: 1,
                type: Number,
            },
            tags: {
                default: () => [],
                type: Array,
            },
            tagUrl: {
                default: "",
                type: String,
            },
            title: {
                default: "",
                type: String,
            },
            url: {
                default: "",
                type: String,
            },
        },
    };

</script>
