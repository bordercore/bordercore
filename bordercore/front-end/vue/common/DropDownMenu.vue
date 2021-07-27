<template>
    <div class="dropdownmenu" :class="[hide ? 'hidden' : '']">
        <dropdown-menu v-model="showMenu" transition="translate-fade-down" class="text-center" :right="right">
            <font-awesome-icon icon="ellipsis-v" />
            <div slot="dropdown">
                <a v-for="link in links" :key="link.id" :href="link.url" class="dropdown-item" @click="link.clickHandler">{{ link.title }}</a>
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
        },
        data() {
            return {
                showMenu: false,
                hide: true,
            };
        },
        methods: {
            foobar(hovered) {
                this.hide = !hovered;
            },
        },
    };

</script>
