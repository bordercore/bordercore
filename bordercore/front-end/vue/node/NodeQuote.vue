<template>
    <div class="hover-target" @mouseover="hover = true" @mouseleave="hover = false">
        <card class="backdrop-filter hover-1" :class="`node-note-color-${color}`">
            <template #title-slot>
                <div class="dropdown-height d-flex">
                    <div v-cloak class="card-title d-flex">
                        <div>
                            <font-awesome-icon icon="quote-left" class="text-primary me-3" />
                            Quote
                        </div>
                    </div>
                    <div class="ms-auto">
                        <drop-down-menu :show-on-hover="true">
                            <div slot="dropdown">
                                <a class="dropdown-item" href="#" @click.prevent="onUpdateQuote()">
                                    <span>
                                        <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />
                                    </span>
                                    Update quote
                                </a>
                                <a class="dropdown-item" href="#" @click.prevent="onRemoveQuote">
                                    <span>
                                        <font-awesome-icon icon="plus" class="text-primary me-3" />
                                    </span>
                                    Remove quote
                                </a>
                            </div>
                        </drop-down-menu>
                    </div>
                </div>
            </template>
            <template #content>
                <hr class="filter-divider mt-0">
                <div v-if="quoteList.length > 0">
                    <div>
                        {{ quoteList[currentQuote].quote }}
                    </div>
                    <div class="text-primary text-smaller">
                        {{ quoteList[currentQuote].source }}
                    </div>
                </div>
            </template>
        </card>
    </div>
</template>

<script>

    export default {

        name: "NodeQuote",
        props: {
            quoteColor: {
                type: Number,
                default: 1,
            },
            nodeUuid: {
                type: String,
                default: "",
            },
            getQuoteListUrl: {
                type: String,
                default: "",
            },
            setQuoteColorUrl: {
                type: String,
                default: "",
            },
        },
        data() {
            return {
                color: null,
                currentQuote: null,
                hover: false,
                quoteList: [],
            };
        },
        mounted() {
            this.getQuoteList();

            this.color = this.quoteColor;

            const self = this;

            hotkeys("left,right", function(event, handler) {
                switch (handler.key) {
                    case "left":
                        if (self.hover) {
                            self.previousQuote();
                        }
                        break;
                    case "right":
                        if (self.hover) {
                            self.nextQuote();
                        }
                        break;
                }
            });
        },
        methods: {
            getQuoteList() {
                doGet(
                    this,
                    this.getQuoteListUrl,
                    (response) => {
                        this.quoteList = response.data.results;
                        this.currentQuote = Math.floor(Math.random() * this.quoteList.length);
                    },
                    "Error getting quotes",
                );
            },
            nextQuote() {
                if (this.currentQuote == this.quoteList.length - 1) {
                    this.currentQuote = 0;
                } else {
                    this.currentQuote += 1;
                }
            },
            onRemoveQuote() {
                this.$emit("remove-quote");
            },
            onUpdateQuote() {
                this.$emit("open-modal-quote-update", this.updateQuote, {"note": this.note, "color": this.color});
            },
            previousQuote() {
                if (this.currentQuote == 0) {
                    this.currentQuote = this.quoteList.length - 1;
                } else {
                    this.currentQuote -= 1;
                }
            },
            updateQuote(color) {
                if (color !== this.color) {
                    doPost(
                        this,
                        this.setQuoteColorUrl,
                        {
                            "node_uuid": this.$store.state.nodeUuid,
                            "color": color,
                        },
                        (response) => {
                            this.color = color;
                        },
                        "",
                        "",
                    );
                }
            },
        },
    };

</script>
