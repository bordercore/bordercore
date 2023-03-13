<template>
    <li :class="{'hide-list-element': depth == 0}">
        <div v-if="depth > 0"
             class="text-break"
             :class="{'tree-folder': isFolder}"
             @click="toggle"
             @dblclick="makeFolder"
        >
            <a :href="'#section_' + item.id">{{ item.label }}</a>
            <!-- <span v-if="isFolder">[{{ isOpen ? '-' : '+' }}]</span> -->
        </div>
        <ul v-show="isOpen" v-if="isFolder" class="mb-0 ms-2">
            <tree-menu
                v-for="(child, index) in item.nodes"
                :key="index"
                class="item"
                :initial-open="depth < 0 ? true : false"
                :item="child"
                :depth="depth + 1"
                @make-folder="$emit('make-folder', $event)"
                @add-item="$emit('add-item', $event)"
            />
        </ul>
    </li>
</template>

<script>

    export default {
        props: {
            item: {
                default: function() {
                },
                type: Object,
            },
            depth: {
                default: 1,
                type: Number,
            },
            initialOpen: {
                default: true,
                type: Boolean,
            },
        },
        emits: ["make-folder"],
        setup(props, ctx) {
            const isOpen = ref(props.initialOpen);

            function makeFolder() {
                if (!isFolder) {
                    ctx.emit("make-folder", props.item);
                    isOpen.value = true;
                }
            };

            function toggle() {
                if (isFolder) {
                    isOpen.value = !isOpen.value;
                }
            };

            const isFolder = computed(() => {
                return props.item.nodes && props.item.nodes.length;
            });

            return {
                isFolder,
                isOpen,
                makeFolder,
                toggle,
            };
        },
    };

    </script>
