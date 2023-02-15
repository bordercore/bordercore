<template>
    <div id="modalCreateUpdate" class="modal fade" tabindex="-1" role="dialog" aria-labelledby="myModalLabel">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 id="myModalLabel" class="modal-title">
                        <span id="action-type" v-html="action" />
                        Playlist
                    </h4>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" />
                </div>
                <div class="modal-body">
                    <div class="row mb-3">
                        <label class="col-lg-4 col-form-label" for="id_name">Name</label>
                        <div class="col-lg-8">
                            <input id="id_name" v-model="name" type="text" name="name" autocomplete="off" maxlength="200" required="required" class="form-control">
                        </div>
                    </div>

                    <div class="row">
                        <label class="col-lg-4 col-form-label" for="id_note">Note</label>
                        <div class="col-lg-8">
                            <textarea id="id_note" v-model="note" name="note" cols="40" rows="3" class="form-control" />
                        </div>
                    </div>

                    <div v-if="action !== 'Update'">
                        <hr class="mb-1">

                        <div class="form-section">
                            Playlist Type
                        </div>

                        <div class="row mt-3">
                            <div class="col-lg-12">
                                <div class="form-check">
                                    <input id="id_type_manual" v-model="smartType" class="form-check-input mt-2" type="radio" name="type" value="manual">
                                    <label class="form-check-label d-flex" for="id_type_manual">
                                        Manually Add Songs
                                    </label>
                                </div>
                            </div>
                        </div>

                        <div class="row mt-3">
                            <div class="col-lg-4">
                                <div class="form-check">
                                    <input id="id_type_tag" v-model="smartType" class="form-check-input mt-2" type="radio" name="type" value="tag">
                                    <label class="form-check-label d-flex" for="id_type_tag">
                                        Tag
                                    </label>
                                </div>
                            </div>
                            <div class="col-lg-8">
                                <tags-input
                                    id="smart-list-tag"
                                    ref="smartListTag"
                                    :search-url="tagSearchUrl + '&query='"
                                    name="tag"
                                    place-holder="Tag name"
                                    :disabled="smartType !== 'tag'"
                                    :max-tags="1"
                                />
                            </div>
                        </div>

                        <div class="row mt-3">
                            <div class="col-lg-12">
                                <div class="form-check">
                                    <input id="id_type_recent" v-model="smartType" class="form-check-input mt-2" type="radio" name="type" value="recent">
                                    <label class="form-check-label d-flex" for="id_type_recent">
                                        Recently Added Songs
                                    </label>
                                </div>
                            </div>
                        </div>

                        <div class="row mt-3">
                            <div class="col-lg-4">
                                <div class="form-check">
                                    <input id="id_type_time" v-model="smartType" type="radio" name="type" class="form-check-input mt-2" value="time">
                                    <label class="from-check-label text-nowrap" for="id_type_time">
                                        Time period
                                    </label>
                                </div>
                            </div>
                            <div class="col-lg-8">
                                <label class="form-check-label d-flex" for="type">
                                    <input v-model="startYear" class="form-control me-1" type="number" name="start_year" size="4" placeholder="Start year" autocomplete="off" :disabled="smartType !== 'time'">
                                    <input v-model="endYear" class="form-control ms-1" type="number" name="end_year" size="4" placeholder="End year" autocomplete="off" :disabled="smartType !== 'time'">
                                </label>
                            </div>
                        </div>

                        <div class="row mt-3">
                            <div class="col-lg-4">
                                <div class="form-check">
                                    <input type="hidden" name="rating" :value="rating">
                                    <input id="id_type_rating" v-model="smartType" type="radio" name="type" class="form-check-input mt-2" value="rating">
                                    <label class="from-check-label text-nowrap" for="id_type_rating">
                                        Rating
                                    </label>
                                </div>
                            </div>
                            <div class="col-lg-8">
                                <label class="form-check-label d-flex">
                                    <div @mouseleave="onMouseLeaveRatingContainer">
                                        <span
                                            v-for="starCount in Array(5).fill().map((x,i)=>i)"
                                            :key="starCount"
                                            class="rating me-1"
                                            :class="getStarClass(starCount)"
                                            :data-rating="starCount"
                                            @click="setRating($event, starCount)"
                                            @mouseover="onMouseOverRating(starCount)"
                                        >
                                            <font-awesome-icon icon="star" />
                                        </span>
                                    </div>
                                </label>
                            </div>
                        </div>
                    </div>

                    <transition name="fade">
                        <div v-if="smartType !== 'manual'">
                            <hr class="mb-1">

                            <div class="form-section">
                                Options
                            </div>

                            <div class="row mt-3">
                                <label class="col-lg-4 col-form-label">Size</label>
                                <div class="col-lg-8">
                                    <select v-model="size" class="form-control form-select" name="size">
                                        <option v-for="option in sizeOptions" :key="option.value" :value="option.value">
                                            {{ option.display }}
                                        </option>
                                    </select>
                                </div>
                            </div>

                            <div class="row mt-3">
                                <label class="col-lg-4 col-form-label">Exclude Recent Listens</label>
                                <div class="col-lg-8">
                                    <select v-model="excludeRecent" class="form-control form-select" name="exclude_recent">
                                        <option v-for="option in excludeRecentOptions" :key="option.value" :value="option.value">
                                            {{ option.display }}
                                        </option>
                                    </select>
                                </div>
                            </div>

                            <div class="row mt-3">
                                <div class="col-lg-12 d-flex align-items-center">
                                    <o-switch v-model="excludeAlbums" name="exclude_albums" :native-value="excludeAlbums" />
                                    <label class="ms-2">
                                        Exclude albums
                                    </label>
                                </div>
                            </div>
                        </div>
                    </transition>
                </div>

                <div class="modal-footer justify-content-end">
                    <input id="btn-action" class="btn btn-primary" type="submit" name="Go" :value="action" :disabled="disabledCreateButton">
                </div>
            </div>
        </div>
    </div>
</template>

<script>

    import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";
    import TagsInput from "/front-end/vue/common/TagsInput.vue";

    export default {
        components: {
            FontAwesomeIcon,
            TagsInput,
        },
        props: {
            tagSearchUrl: {
                default: "",
                type: String,
            },
            action: {
                default: "Create",
                type: String,
            },
            playlist: {
                default: function() {
                },
                type: Object,
            },
        },
        setup(props) {
            const endYear = ref(getAttribute("end_year", undefined));
            const excludeAlbums = ref(getAttribute("exclude_albums", false));
            const excludeRecent = ref(getAttribute("exclude_recent", ""));
            const name = ref(getAttribute("name", ""));
            const note = ref(getAttribute("note", ""));
            const rating = ref(getAttribute("rating", undefined));
            const size = ref(getAttribute("size", 20));
            const smartType = ref(getAttribute("type", "manual"));
            const startYear = ref(getAttribute("start_year", undefined));

            const disabledCreateButton = computed(() => {
                if (smartType === "tag" &&
                    (this.$refs.smartListTag && this.$refs.smartListTag.tags.length === 0)) {
                    return true;
                } else if (smartType === "time" &&
                           (!startYear || !endYear) ||
                           parseInt(endYear) < parseInt(startYear)) {
                    return true;
                }
                return false;
            });

            function getAttribute(attribute, defaultValue) {
                if (props.playlist) {
                    if (attribute in props.playlist) {
                        return props.playlist[attribute];
                    } else if (attribute in props.playlist.parameters ) {
                        return props.playlist.parameters[attribute];
                    }
                }
                return defaultValue;
            }

            function getStarClass(rating) {
                if (rating <= rating - 1) {
                    return "rating-star-selected";
                }
                return "";
            }

            function onClickCreate(evt) {
                const modal = new Modal("#modalAdd");
                modal.show();
                window.setTimeout(() => {
                    document.getElementById("id_name").focus();
                }, 500);
            }

            function onMouseLeaveRatingContainer() {
                const els = document.querySelectorAll(".rating");
                for (const el of els) {
                    el.classList.remove("rating-star-hovered");
                }
            }

            function onMouseOverRating(rating) {
                if (smartType !== "rating") {
                    return;
                }
                const els = document.querySelectorAll(".rating");
                // Loop over each star rating. Add the "hovered" class if:
                //  1) The rating is > the currently selected rating
                //  2) The rating is < the currently "hovered" rating
                for (const el of els) {
                    if (!el.classList.contains("rating-star-selected") &&
                        parseInt(el.getAttribute("data-rating"), 10) < rating + 1 ) {
                        el.classList.add("rating-star-hovered");
                    } else {
                        el.classList.remove("rating-star-hovered");
                    }
                }
            }

            function setRating(evt, ratingParam) {
                if (smartType === "rating") {
                    if (ratingParam + 1 === rating.value) {
                        // If we've selected the current rating, treat it
                        // as if we've de-selected a rating entirely
                        // and remove it.
                        rating.value = "";
                    } else {
                        rating.value = rating.value + 1;
                    }
                    nextTick(() => {
                        animateCSS(evt.currentTarget, "heartBeat");
                    });
                }
            }

            return {
                disabledCreateButton,
                endYear,
                excludeAlbums,
                excludeRecent,
                getAttribute,
                getStarClass,
                name,
                note,
                onClickCreate,
                onMouseLeaveRatingContainer,
                onMouseOverRating,
                rating,
                setRating,
                size,
                smartType,
                startYear,
                fields: [
                    {
                        key: "year",
                    },
                    {
                        key: "artist",
                    },
                    {
                        key: "title",
                    },
                    {
                        key: "length",
                        tdClass: "text-center",
                        thClass: "text-center",
                    },
                ],
                sizeOptions: [
                    {
                        value: "",
                        display: "Unlimited",
                    },
                    {
                        value: 5,
                        display: "5",
                    },
                    {
                        value: 10,
                        display: "10",
                    },
                    {
                        value: 20,
                        display: "20",
                    },
                    {
                        value: 50,
                        display: "50",
                    },
                    {
                        value: 100,
                        display: "100",
                    },
                ],
                excludeRecentOptions: [
                    {
                        value: "",
                        display: "No limit",
                    },
                    {
                        value: 1,
                        display: "Past Day",
                    },
                    {
                        value: 2,
                        display: "Past Two Days",
                    },
                    {
                        value: 3,
                        display: "Past Three Days",
                    },
                    {
                        value: 7,
                        display: "Past Week",
                    },
                    {
                        value: 30,
                        display: "Past Month",
                    },
                    {
                        value: 90,
                        display: "Past 3 Months",
                    },
                ],
            };
        },
    };

</script>
