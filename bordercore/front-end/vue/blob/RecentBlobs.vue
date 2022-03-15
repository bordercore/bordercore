<template>
    <span class="ml-2" data-toggle="tooltip" data-placement="bottom" title="Recent Blobs">

        <dropdown-menu v-model="showMenu" transition="translate-fade-down" class="text-center" :right="true">

            <span class="ml-2">
                <font-awesome-icon class="glow" icon="object-group" />
            </span>

            <div slot="dropdown" class="recent-blobs px-2">
                <div class="top-search-splitter">
                    Recent Blobs
                </div>
                <a v-for="link in blobListInfo.blobList[0]" :key="link.id" :href="link.url" class="dropdown-item d-flex align-items-center" v-on="link.clickHandler ? { click: link.clickHandler } : {}">
                    <span class="icon d-flex justify-content-center align-items-center">
                        <img v-if="link.doctype === 'image'" :src="link.cover_url_small" class="mw-100 mh-100">
                        <img v-else-if="link.doctype === 'video'" :src="link.cover_url_small" class="mw-100 mh-100">
                        <span v-else>
                            <font-awesome-icon icon="file-alt" class="fa-3x" />
                        </span>
                    </span>
                    <span class="ml-2">
                        {{ link.name }}
                    </span>
                </a>
                <div v-if="blobListInfo.message" class="text-nowrap">
                    <strong>Elasticsearch Error</strong>: {{ blobListInfo.message.statusCode }}
                </div>
            </div>
        </dropdown-menu>
    </span>
</template>

<script>

    export default {
        props: {
            blobListInfo: {
                default: function() {
                },
                type: Object,
            },
            blobDetailUrl: {
                default: "",
                type: String,
            },
        },
        data() {
            return {
                showMenu: false,
            };
        },
        computed: {
            menuItems: function() {
                const self = this;
                const items = this.blobListInfo.blobList.map( function(item) {
                    return {
                        id: uuidv4(),
                        title: item.name,
                        url: self.blobDetailUrl.replace(/00000000-0000-0000-0000-000000000000/, item.uuid),
                    };
                });

                return items;
            },
        },
        methods: {
            getCoverImage() {
            },
        },
    };

</script>
