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
                <div v-if="quote">
                    <div>
                        {{ quote.quote }}
                    </div>
                    <div class="text-primary text-smaller">
                        {{ quote.source }}
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
            nodeUuid: {
                type: String,
                default: "",
            },
            nodeQuoteObj: {
                type: Object,
                default: function() {},
            },
            getAndSetQuoteUrl: {
                type: String,
                default: "",
            },
            getQuoteUrl: {
                type: String,
                default: "",
            },
            updateQuoteUrl: {
                type: String,
                default: "",
            },
        },
        data() {
            return {
                color: null,
                hover: false,
                interval: null,
                quote: null,
                quoteUuid: null,
                rotate: null,
            };
        },
        mounted() {
            this.color = this.nodeQuoteObj.color;
            this.quoteUuid = this.nodeQuoteObj.uuid;
            this.rotate = this.nodeQuoteObj.rotate;

            this.getQuote();

            if (this.rotate !== null && this.rotate !== -1) {
                this.setTimer();
            }

            const self = this;

            hotkeys("right", function(event, handler) {
                switch (handler.key) {
                    case "right":
                        if (self.hover) {
                            self.getRandomQuote();
                        }
                        break;
                }
            });
        },
        methods: {
            getQuote() {
                doGet(
                    this,
                    this.getQuoteUrl.replace("00000000-0000-0000-0000-000000000000", this.quoteUuid),
                    (response) => {
                        this.quote = response.data;
                    },
                    "Error getting quote",
                );
            },
            getRandomQuote() {
                doPost(
                    this,
                    this.getAndSetQuoteUrl,
                    {
                        "node_uuid": this.$store.state.nodeUuid,
                    },
                    (response) => {
                        this.quote = response.data.quote;
                    },
                    "",
                    "",
                );
            },
            onRemoveQuote() {
                this.$emit("remove-quote");
            },
            onUpdateQuote() {
                this.$emit("open-modal-quote-update", this.updateQuote, {"color": this.color, "rotate": this.rotate});
            },
            setTimer() {
                clearInterval(this.interval);
                this.interval = setInterval( () => {
                    this.getRandomQuote();
                }, this.rotate * 1000 * 60);
            },
            updateQuote(color, rotate) {
                if (color !== this.color || this.rotate !== rotate) {
                    doPost(
                        this,
                        this.updateQuoteUrl,
                        {
                            "node_uuid": this.$store.state.nodeUuid,
                            "color": color,
                            "rotate": rotate,
                        },
                        (response) => {
                            this.color = color;
                            if (this.rotate !== rotate) {
                                this.rotate = rotate;
                                this.setTimer();
                            }
                        },
                        "",
                        "",
                    );
                }
            },
        },
    };

</script>
