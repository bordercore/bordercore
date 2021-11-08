<template>
    <div class="pagination">
        <nav v-if="numObjects > 0 && paginator.num_pages > 1" class="mb-5 navigation">
            <ul class="pagination justify-content-center">
                <li class="page-item" :class="{'disabled': !hasPrevious()}">
                    <a class="page-link" :href="previousPage()">Previous</a>
                </li>
                <li class="page-item disabled">
                    <span class="page-link">
                        Page <strong>{{ paginator.number }}</strong> of <strong>{{ paginator.num_pages }}</strong>
                    </span>
                </li>
                <li class="page-item" :class="{'disabled': !hasNext()}">
                    <a class="page-link" :href="nextPage()">Next</a>
                </li>
            </ul>
        </nav>
    </div>
</template>

<script>

    export default {

        props: {
            paginator: {
                type: Object,
                default: function() {},
            },
            numObjects: {
                type: Number,
                default: 0,
            },
            searchArgs: {
                type: String,
                default: "",
            },
        },
        methods: {
            hasNext() {
                return this.paginator.has_next;
            },
            hasPrevious() {
                return this.paginator.has_previous;
            },
            nextPage() {
                return "?page=" + this.paginator.next_page_number + this.searchArgs;
            },
            previousPage() {
                return "?page=" + this.paginator.previous_page_number + this.searchArgs;
            },
        },

    };

</script>
