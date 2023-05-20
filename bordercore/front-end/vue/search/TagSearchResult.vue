<template>
    <div :id="docType" class="tab-pane fade">
        <ul class="list-unstyled" :class="{'d-flex flex-wrap': docType === 'blob' || docType === 'book' || docType === 'album'}">
            <li
                v-for="match in matches"
                :key="match.uuid"
                class="search-result me-3 py-3"
                :class="{'grid': docType === 'blob' || docType === 'book'}"
            >
                <div v-if="docType === 'drill'">
                    <div class="col-lg-12">
                        <a :href="match.object_url">
                            {{ match.question }}
                        </a>
                    </div>
                </div>
                <div v-else-if="docType === 'song'">
                    <div class="col-lg-12">
                        <a :href="match.object_url">
                            {{ match.artist }} = {{ match.title }}
                        </a>
                    </div>
                </div>
                <div v-else-if="docType === 'todo'">
                    <div class="col-lg-12 d-flex flex-column">
                        <div>
                            {{ match.name }}
                        </div>
                        <div class="search-todo-date ms-2">
                            {{ match.date }}
                        </div>
                    </div>
                </div>
                <div v-else-if="docType === 'album'" class="d-flex flex-column">
                    <div>
                        <a :href="match.object_url">
                            <img :src="match.album_artwork_url" height="150" width="150">
                        </a>
                    </div>
                    <div class="mt-1 fw-bold">
                        {{ match.title }}
                    </div>
                    <div class="text-light">
                        <a :href="match.object_url">
                            {{ match.artist }}
                        </a>
                    </div>
                </div>
                <div v-else class="d-flex my-1">
                    <div v-if="docType === 'blob' || docType === 'book'">
                        <img :src="match.cover_url">
                    </div>
                    <div class="d-flex flex-column ms-2">
                        <h4>
                            <font-awesome-icon v-if="match.importance > 1" icon="heart" class="favorite" data-bs-toggle="tooltip" data-placement="bottom" title="Favorite" />
                            <a :href="match.object_url">
                                {{ match.name }}
                            </a>
                        </h4>
                        <div v-if="docType === 'blob' || docType === 'book' || docType === 'note' || docType === 'document'">
                            <h5 v-if="docType === 'note' || docType === 'document'">
                                {{ match.contents }}
                            </h5>
                            <small v-else-if="match.creators">
                                {{ match.creators }}
                            </small>
                            <div v-if="docType !== 'note' && docType !== 'document'" class="search-result-date text-nowrap">
                                {{ match.date }}
                            </div>
                        </div>
                        <div v-if="docType === 'bookmark'" class="d-flex mb-2 align-items-center text-primary">
                            <span v-html="match.favicon_url" />
                            <div class="ms-2">
                                {{ match.url_domain }}
                            </div>
                        </div>
                        <div class="mt-2">
                            <a v-for="tag in match.tags" :key="tag.name" :href="tag.url" class="tag">
                                {{ tag.name }}
                            </a>
                        </div>
                    </div>
                    <div
                        v-if="docType === 'bookmark' || docType === 'note' || docType === 'document'"
                        class="search-result-date text-nowrap ms-auto ps-4"
                    >
                        {{ match.date }}
                    </div>
                </div>
            </li>
        </ul>
    </div>
</template>

<script>

    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";

    export default {
        components: {
            FontAwesomeIcon,
        },
        props: {
            docType: {
                default: "",
                type: String,
            },
            matches: {
                default: () => [],
                type: Array,
            },
        },
    };

</script>
