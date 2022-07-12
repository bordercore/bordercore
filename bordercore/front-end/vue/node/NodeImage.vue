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
                            <div slot="dropdown">
                                <a class="dropdown-item" href="#" @click.prevent="onRemoveImage()">
                                    <span>
                                        <font-awesome-icon icon="times" class="text-primary me-3" />
                                    </span>
                                    Remove image
                                </a>
                            </div>
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

    export default {

        name: "NodeImage",
        props: {
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
        },
        methods: {
            onClick() {
                this.$emit("open-modal-note-image", this.imageUrl);
            },
            onRemoveImage() {
                this.$emit("remove-image", this.imageUuid);
            },
        },
    };

</script>
