<template>
    <li :class="{'hide-list-element': depth == 0}">
        <div v-if="depth > 0"
             class="text-break"
             :class="{bold: isFolder}"
             @click="toggle"
             @dblclick="makeFolder">
            <a :href="getId(item.id)">{{ item.label }}</a>
            <!-- <span v-if="isFolder">[{{ isOpen ? '-' : '+' }}]</span> -->
        </div>
        <ul v-show="isOpen" v-if="isFolder">
            <tree-menu
                class="item"
                v-for="(child, index) in item.nodes"
                :key="index"
                :item="child"
                :depth="depth + 1"
                @make-folder="$emit('make-folder', $event)"
                @add-item="$emit('add-item', $event)"
            ></tree-menu>
        </ul>
    </li>
</template>

<script>

    import Vue from "vue";

    export default {
        props: {
            item: Object,
            depth: Number
        },
        data: function() {
            return {
                isOpen: true,
            };
        },
        computed: {
            isFolder: function() {
                return this.item.nodes && this.item.nodes.length;
            }
        },
        methods: {
            getId(id) {
                return "#section_" + id
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
            }
        }
    }

    </script>
