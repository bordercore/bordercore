<template>
    <div :class="[hide ? 'hidden' : '']" class="cursor-pointer">
        <dropdown-menu v-model="showMenu" transition="translate-fade-down" class="text-center" :right="right">
            <slot name="top">
                <font-awesome-icon icon="ellipsis-v" />
            </slot>
            <div slot="dropdown">
                <a v-for="link in links" :key="link.id" :href="link.url" class="dropdown-item" v-on="link.clickHandler ? { click: link.clickHandler } : {}">
                    <font-awesome-icon v-if="link.icon" :icon="link.icon" class="mr-2" />
                    {{ link.title }}
                    <span v-if="link.extra" class="dropdown-item-extra">
                        {{ link.extra }}
                    </span>
                </a>
            </div>
        </dropdown-menu>
    </div>
</template>

<script>

    export default {
        props: {
            links: {
                type: Array,
                default: () => [],
            },
            right: {
                type: Boolean,
                default: true,
            },
            initialHide: {
                type: Boolean,
                default: true,
            },
        },
        data() {
            return {
                showMenu: false,
                hide: this.initialHide
            };
        },
    };

</script>
