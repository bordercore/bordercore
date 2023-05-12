<template>
    <span class="mx-2" data-bs-toggle="tooltip" data-placement="bottom" title="Recent Blobs">
        <drop-down-menu :show-target="false">
            <template #icon>
                <font-awesome-icon class="glow" icon="object-group" />
            </template>
            <template #dropdown>
                <div class="recent-blobs px-2">
                    <div class="search-splitter">
                        Recently Viewed
                    </div>
                    <ul v-if="recentlyViewed.blobList.length > 0" class="interior-borders list-group ps-0">
                        <li v-for="link in recentlyViewed.blobList" :key="link.uuid" class="list-group-item ms-0 px-0">
                            <a :href="link.url" class="dropdown-item d-flex align-items-center" v-on="link.clickHandler ? { click: link.clickHandler } : {}">
                                <div :class="'recent-doctype-' + link.doctype.toLowerCase()">
                                    {{ link.doctype }}
                                </div>
                                <div class="text-truncate">
                                    {{ link.name }}
                                </div>
                            </a>
                        </li>
                    </ul>
                    <div v-else class="text-warning ms-2 mb-1">
                        <hr class="divider mb-1">
                        Nothing recently viewed
                    </div>
                    <div v-if="blobListInfo.message" class="text-nowrap">
                        <strong>Elasticsearch Error</strong>: {{ blobListInfo.message.statusCode }}
                    </div>
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
            recentlyViewed: {
                default: function() {},
                type: Object,
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
