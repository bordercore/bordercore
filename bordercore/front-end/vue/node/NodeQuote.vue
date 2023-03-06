<template>
    <div class="hover-target" @mouseover="hover = true" @mouseleave="hover = false">
        <card class="backdrop-filter" :class="cardClass" title="">
            <template #title-slot>
                <div v-if="nodeQuoteInitial.format !== 'minimal'" class="dropdown-height d-flex">
                    <div v-cloak class="card-title d-flex">
                        <div>
                            <font-awesome-icon icon="quote-left" class="text-primary me-3" />
                            Quote
                        </div>
                    </div>
                    <div class="dropdown-menu-container ms-auto">
                        <drop-down-menu :show-on-hover="true">
                            <template #dropdown>
                                <li>
                                    <a class="dropdown-item" href="#" @click.prevent="onUpdateQuote()">
                                        <span>
                                            <font-awesome-icon icon="pencil-alt" class="text-primary me-3" />
                                        </span>
                                        Update quote
                                    </a>
                                </li>
                                <li>
                                    <a class="dropdown-item" href="#" @click.prevent="onRemoveQuote">
                                        <span>
                                            <font-awesome-icon icon="plus" class="text-primary me-3" />
                                        </span>
                                        Remove quote
                                    </a>
                                </li>
                            </template>
                        </drop-down-menu>
                    </div>
                </div>
            </template>
            <template #content>
                <hr class="divider">
                <Transition enter-active-class="animate__animated animate__zoomIn">
                    <div v-if="quote" :key="quote.uuid">
                        <div>
                            {{ quote.quote }}
                        </div>
                        <div class="text-primary text-smaller">
                            <strong>{{ quote.source }}</strong>
                        </div>
                    </div>
                </Transition>
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
            nodeQuoteInitial: {
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
            removeQuoteUrl: {
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
                hover: false,
                rotateInterval: null,
                nodeQuote: {},
                quote: {},
            };
        },
        computed: {
            cardClass() {
                return `node-color-${this.nodeQuote.color}`;
            },
        },
        mounted() {
            this.nodeQuote = this.nodeQuoteInitial;

            this.getQuote();

            if (this.nodeQuote.rotate !== null && this.nodeQuote.rotate !== -1) {
                this.setTimer();
            }

            const self = this;

            hotkeys("right,u", function(event, handler) {
                switch (handler.key) {
                    case "right":
                        if (self.hover) {
                            self.getRandomQuote();
                        }
                        break;
                    case "u":
                        self.onUpdateQuote();
                        break;
                }
            });
        },
        methods: {
            getQuote() {
                doGet(
                    this.getQuoteUrl.replace("00000000-0000-0000-0000-000000000000", this.nodeQuote.uuid),
                    (response) => {
                        this.quote = response.data;
                    },
                    "Error getting quote",
                );
            },
            getRandomQuote() {
                doPost(
                    this.getAndSetQuoteUrl,
                    {
                        "node_uuid": this.nodeUuid,
                        "favorites_only": this.nodeQuote.favorites_only,
                    },
                    (response) => {
                        this.quote = response.data.quote;
                    },
                    "",
                    "",
                );
            },
            onRemoveQuote() {
                doPost(
                    this.removeQuoteUrl,
                    {
                        "node_uuid": this.nodeUuid,
                        "node_quote_uuid": this.nodeQuote.node_quote_uuid,
                    },
                    (response) => {
                        this.$emit("updateLayout", response.data.layout);
                    },
                    "Quote removed",
                );
            },
            onUpdateQuote() {
                this.$emit("openModalQuoteUpdate", this.updateQuote, this.nodeQuote);
            },
            setTimer() {
                if (!this.nodeQuote.rotate || this.nodeQuote.rotate === -1) {
                    return;
                }
                clearInterval(this.rotateInterval);
                this.rotateInterval = setInterval( () => {
                    this.getRandomQuote();
                }, this.nodeQuote.rotate * 1000 * 60);
            },
            updateQuote(quote) {
                doPost(
                    this.updateQuoteUrl,
                    {
                        "node_uuid": this.nodeUuid,
                        "node_quote_uuid": quote.node_quote_uuid,
                        "color": quote.color,
                        "format": quote.format,
                        "rotate": quote.rotate,
                        "favorites_only": quote.favorites_only,
                    },
                    (response) => {
                        this.nodeQuote.color = quote.color;
                        this.nodeQuote.rotate = quote.rotate;
                        this.setTimer();
                    },
                    "",
                    "",
                );
            },
        },
    };

</script>
