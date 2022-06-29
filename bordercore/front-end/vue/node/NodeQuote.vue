<template>
    <div class="hover-target" @mouseover="hover = true" @mouseleave="hover = false">
        <card class="backdrop-filter hover-1">
            <template #title-slot>
                <div class="dropdown-height d-flex">
                    <div v-cloak class="card-title d-flex">
                        Quote
                    </div>
                    <div class="ms-auto">
                        <drop-down-menu :show-on-hover="true">
                            <div slot="dropdown">
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
            nodeUuid: {
                type: String,
                default: "",
            },
            getQuoteListUrl: {
                type: String,
                default: "",
            },
        },
        data() {
            return {
                currentQuote: null,
                hover: false,
                quoteList: [],
            };
        },
        mounted() {
            this.getQuoteList();

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
            previousQuote() {
                if (this.currentQuote == 0) {
                    this.currentQuote = this.quoteList.length - 1;
                } else {
                    this.currentQuote -= 1;
                }
            },
        },
    };

</script>
