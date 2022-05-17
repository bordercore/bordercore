<template>
    <li :class="{'hide-list-element': depth == 0}">
        <div v-if="depth > 0"
             class="text-break"
             :class="{'tree-folder': isFolder}"
             @click="toggle"
             @dblclick="makeFolder"
        >
            <a :href="getId(item.id)">{{ item.label }}</a>
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
        data: function() {
            return {
                isOpen: this.initialOpen,
            };
        },
        computed: {
            isFolder: function() {
                return this.item.nodes && this.item.nodes.length;
            },
        },
        methods: {
            getId(id) {
                return "#section_" + id;
            },
            toggle: function() {
                if (this.isFolder) {
                    this.isOpen = !this.isOpen;
                }
            },
            makeFolder: function() {
                if (!this.isFolder) {
                    this.$emit("make-folder", this.item);
                    this.isOpen = true;
                }
            },
        },
    };

    </script>
