<template>
    <span class="mx-2" data-bs-toggle="tooltip" data-placement="bottom" title="Recent Blobs">

        <drop-down-menu :show-target="false">

            <template #icon>
                <font-awesome-icon class="glow" icon="object-group" />
            </template>

            <template #dropdown class="recent-blobs px-2">
                <div class="search-splitter">
                    Recent Blobs
                </div>
                <ul class="ps-0">
                    <li v-for="link in blobListInfo.blobList" :key="link.id" class="search-suggestion ms-0 px-0">
                        <a :href="link.url" class="dropdown-item d-flex align-items-center" v-on="link.clickHandler ? { click: link.clickHandler } : {}">
                            <span class="icon d-flex justify-content-center align-items-center">
                                <img v-if="link.doctype === 'image'" :src="link.cover_url_small" class="mw-100 mh-100">
                                <img v-else-if="link.doctype === 'video'" :src="link.cover_url_small" class="mw-100 mh-100">
                                <span v-else>
                                    <font-awesome-icon icon="file-alt" class="fa-3x" />
                                </span>
                            </span>
                            <span class="ms-2">
                                {{ link.name }}
                            </span>
                        </a>
                    </li>
                </ul>
                <div v-if="blobListInfo.message" class="text-nowrap">
                    <strong>Elasticsearch Error</strong>: {{ blobListInfo.message.statusCode }}
                </div>
            </template>
        </drop-down-menu>
    </span>
</template>

<script>

    import DropDownMenu from "../common/DropDownMenu.vue";
    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

    export default {
        components: {
            DropDownMenu,
            FontAwesomeIcon,
        },
        props: {
            blobListInfo: {
                default: function() {},
                type: Object,
            },
            blobDetailUrl: {
                default: "",
                type: String,
            },
        },
        setup(props) {
            const menuItems = computed(() => {
                const items = props.blobListInfo.blobList.map( function(item) {
                    return {
                        id: uuidv4(),
                        title: item.name,
                        url: props.blobDetailUrl.replace(/00000000-0000-0000-0000-000000000000/, item.uuid),
                    };
                });

                return items;
            });

            return {
                menuItems,
            };
        },
    };

</script>
