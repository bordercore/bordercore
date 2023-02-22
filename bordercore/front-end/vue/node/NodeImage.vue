<template>
    <div class="hover-target">
        <card class="backdrop-filter node-color-1">
            <template #title-slot>
                <div class="dropdown-height d-flex">
                    <div v-cloak class="card-title d-flex">
                        <div>
                            <font-awesome-icon icon="image" class="text-primary me-3" />
                            {{ imageTitle }}
                        </div>
                    </div>
                    <div class="dropdown-menu-container ms-auto">
                        <drop-down-menu :show-on-hover="true">
                            <template #dropdown>
                                <li>
                                    <a class="dropdown-item" href="#" @click.prevent="onRemoveImage()">
                                        <span>
                                            <font-awesome-icon icon="times" class="text-primary me-3" />
                                        </span>
                                        Remove image
                                    </a>
                                </li>
                            </template>
                        </drop-down-menu>
                    </div>
                </div>
            </template>
            <template #content>
                <img :src="imageUrl" class="mw-100" @click="onClick">
            </template>
        </card>
    </div>
</template>

<script>

    import Card from "/front-end/vue/common/Card.vue";
    import DropDownMenu from "/front-end/vue/common/DropDownMenu.vue";
    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

    export default {
        components: {
            Card,
            DropDownMenu,
            FontAwesomeIcon,
        },
        props: {
            nodeUuid: {
                type: String,
                default: "",
            },
            imageUuid: {
                type: String,
                default: "",
            },
            imageTitle: {
                type: String,
                default: "",
            },
            imageUrl: {
                type: String,
                default: "",
            },
            removeImageUrl: {
                type: String,
                default: "",
            },
        },
        setup(props, ctx) {
            function onClick() {
                ctx.emit("open-modal-note-image", props.imageUrl);
            };

            function onRemoveImage() {
                doPost(
                    null,
                    props.removeImageUrl,
                    {
                        "node_uuid": props.nodeUuid,
                        "image_uuid": props.imageUuid,
                    },
                    (response) => {
                        ctx.emit("updateLayout", response.data.layout);
                    },
                    "Image removed",
                );
            };

            return {
                onClick,
                onRemoveImage,
            };
        },
    };

</script>
