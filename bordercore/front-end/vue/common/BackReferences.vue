<template>
    <card title="Back references">
        <template #content>
            <hr class="divider">
            <ul class="list-group interior-borders cursor-pointer text-truncate">
                <li v-for="node in backReferences" :key="node.uuid" class="hoverable px-0 list-group-item list-group-item-secondary text-primary">
                    <div v-if="node.type === 'question'" class="d-flex">
                        <div class="mt-1 me-2">
                            <font-awesome-icon icon="question" class="text-success" />
                        </div>
                        <div>
                            <div class="back-reference " @click="handleNodeClick(node.url)" v-html="getMarkdown(node.question)" />
                            <div class="pt-2">
                                <span v-for="tag in node.tags" :key="tag" class="tag me-2">
                                    {{ tag }}
                                </span>
                            </div>
                        </div>
                    </div>
                    <div v-if="node.type === 'blob'" class="d-flex">
                        <div class="mt-1 me-2">
                            <font-awesome-icon icon="copy" class="text-success" />
                        </div>
                        <div class="text-truncate">
                            <img :src="node.cover_url" class="mw-100">
                            <div class="text-truncate" @click="handleNodeClick(node.url)" v-html="node.name" />
                            <div class="pt-2">
                                <span v-for="tag in node.tags" :key="tag" class="tag me-2">
                                    {{ tag }}
                                </span>
                            </div>
                        </div>
                    </div>
                </li>
            </ul>
        </template>
    </card>
</template>

<script>

    import Card from "/front-end/vue/common/Card.vue";
    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";
    import markdownit from "markdown-it";

    export default {
        components: {
            Card,
            FontAwesomeIcon,
        },
        props: {
            backReferences: {
                default: () => [],
                type: Array,
            },
        },
        setup(props) {
            const markdown = markdownit();

            function getMarkdown(content) {
                return markdown.render(content);
            };

            function handleNodeClick(url) {
                window.location = url;
            };

            return {
                getMarkdown,
                handleNodeClick,
            };
        },
    };

</script>
