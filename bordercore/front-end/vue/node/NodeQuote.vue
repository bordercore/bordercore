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
                                    <a class="dropdown-item" href="#" @click.prevent="handleQuoteRemove">
                                        <span>
                                            <font-awesome-icon icon="plus" class="text-primary me-3" />
                                        </span>
                                        Remove quote
                                    </a>
                                </li>
                            </template>
                        </drop-down-menu>
                    </div>
                    <hr class="divider">
                </div>
            </template>
            <template #content>
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
        emits: ["open-quote-update-modal", "update-layout"],
        setup(props, ctx) {
            const hover = ref(false);
            const quote = ref(null);

            const nodeQuote = ref({});
            let rotateInterval = null;

            function getQuote() {
                doGet(
                    props.getQuoteUrl.replace("00000000-0000-0000-0000-000000000000", nodeQuote.value.uuid),
                    (response) => {
                        quote.value = response.data;
                    },
                    "Error getting quote",
                );
            };


            function getRandomQuote() {
                doPost(
                    props.getAndSetQuoteUrl,
                    {
                        "node_uuid": props.nodeUuid,
                        "favorites_only": nodeQuote.value.favorites_only,
                    },
                    (response) => {
                        quote.value = response.data.quote;
                    },
                );
            };

            function handleQuoteRemove() {
                doPost(
                    props.removeQuoteUrl,
                    {
                        "node_uuid": props.nodeUuid,
                        "node_quote_uuid": nodeQuote.value.node_quote_uuid,
                    },
                    (response) => {
                        ctx.emit("update-layout", response.data.layout);
                    },
                    "Quote removed",
                );
            };

            function updateQuote(quote) {
                doPost(
                    props.updateQuoteUrl,
                    {
                        "node_uuid": props.nodeUuid,
                        "node_quote_uuid": quote.node_quote_uuid,
                        "color": quote.color,
                        "format": quote.format,
                        "rotate": quote.rotate,
                        "favorites_only": quote.favorites_only,
                    },
                    (response) => {
                        nodeQuote.value.color = quote.color;
                        nodeQuote.value.rotate = quote.rotate;
                        setTimer();
                    },
                );
            };

            function onUpdateQuote() {
                ctx.emit("open-quote-update-modal", updateQuote, nodeQuote.value);
            };

            function setTimer() {
                if (!nodeQuote.value.rotate || nodeQuote.value.rotate === -1) {
                    return;
                }
                clearInterval(rotateInterval);
                rotateInterval = setInterval( () => {
                    getRandomQuote();
                }, nodeQuote.value.rotate * 1000 * 60);
            };

            onMounted(() => {
                nodeQuote.value = props.nodeQuoteInitial;

                getQuote();

                if (nodeQuote.value.rotate !== null && nodeQuote.value.rotate !== -1) {
                    setTimer();
                }

                hotkeys("right,u", function(event, handler) {
                    switch (handler.key) {
                    case "right":
                        if (hover.value) {
                            getRandomQuote();
                        }
                        break;
                    case "u":
                        onUpdateQuote();
                        break;
                    }
                });
            });

            const cardClass = computed(() => {
                return `node-color-${nodeQuote.value.color}`;
            });

            return {
                cardClass,
                handleQuoteRemove,
                onUpdateQuote,
                hover,
                quote,
            };
        },
    };

</script>
