<template>
    <div class="dropdown ms-auto d-flex align-items-center justify-content-center">
        <div
            class="cursor-pointer"
            :class="{'dropdownmenu': showTarget, 'd-none': showOnHover}"
        >
            <div class="d-flex align-items-center justify-content-center h-100 w-100" :class="direction" data-bs-toggle="dropdown" data-bs-auto-close="true" data-bs-offset="0,-15">
                <slot name="icon">
                    <font-awesome-icon icon="ellipsis-v" />
                </slot>
            </div>
            <ul class="dropdown-menu">
                <slot name="dropdown">
                    <li v-for="link in links" :key="link.id">
                        <a :href="link.url" class="dropdown-item" v-on="link.clickHandler ? { click: link.clickHandler } : {}">
                            <span class="me-2">
                                <font-awesome-icon v-if="link.icon" :icon="link.icon" class="text-primary" />
                            </span>
                            {{ link.title }}
                            <span v-if="link.extra" class="dropdown-item-extra">
                                {{ link.extra }}
                            </span>
                        </a>
                    </li>
                </slot>
            </ul>
        </div>
    </div>
</template>

<script>

    export default {
        props: {
            links: {
                type: Array,
                default: () => [],
            },
            direction: {
                type: String,
                default: "dropend",
            },
            showTarget: {
                type: Boolean,
                default: true,
            },
            showOnHover: {
                type: Boolean,
                default: false,
            },
        },
    };

</script>
