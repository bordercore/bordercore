<template>
    <div class="pagination-container">
        <nav v-if="numObjects > 0 && paginator.num_pages > 1" class="mb-5 navigation">
            <ul class="pagination justify-content-center">
                <li class="page-item" :class="{'disabled': !hasPrevious()}">
                    <a class="page-link" :href="previousPage()">
                        <font-awesome-icon icon="chevron-left" class="text-emphasis" />
                    </a>
                </li>
                <li class="pagination-divider">
                    <div class="w-100 h-75" />
                </li>

                <li v-for="page in paginator.range" :key="page" class="page-item" :class="{'disabled': paginator.page_number === page}">
                    <a class="page-link" :href="pageLink(page)">
                        {{ page }}
                    </a>
                </li>

                <li class="pagination-divider">
                    <div class="w-100 h-75" />
                </li>

                <li class="page-item" :class="{'disabled': !hasNext()}">
                    <a class="page-link" :href="nextPage()">
                        <font-awesome-icon icon="chevron-right" class="text-emphasis" />
                    </a>
                </li>
            </ul>
        </nav>
    </div>
</template>

<script>

    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

    export default {
        components: {
            FontAwesomeIcon,
        },
        props: {
            paginator: {
                type: Object,
                default: function() {},
            },
            numObjects: {
                type: Number,
                default: 0,
            },
        },
        computed: {
            pageRange() {
                return this.paginator.range;
                return this.paginator.range.filter((page) => page != this.paginator.previous_page_number);
            },
        },
        methods: {
            getSearchArgs() {
                const urlSearchParams = new URLSearchParams(window.location.search);

                // The Pagination Vue component will add the "page" searcharg, so we
                //  need to delete it first.
                urlSearchParams.delete("page");

                return "&" + urlSearchParams;
            },
            hasNext() {
                return this.paginator.has_next;
            },
            hasPrevious() {
                return this.paginator.has_previous;
            },
            pageLink(pageNumber) {
                return "?page=" + pageNumber + this.getSearchArgs();
            },
            nextPage() {
                return "?page=" + this.paginator.next_page_number + this.getSearchArgs();
            },
            previousPage() {
                return "?page=" + this.paginator.previous_page_number + this.getSearchArgs();
            },
        },

    };

</script>
