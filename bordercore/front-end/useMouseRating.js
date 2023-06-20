export default function() {
    function handleRatingMouseLeave() {
        const els = document.querySelectorAll(".rating, .rating-no-hover");
        for (const el of els) {
            el.classList.remove("rating-star-hovered");
        }
    };

    function handleRatingMouseOver(event, rating) {
        // The event is triggered on an individual star. Go
        // up to the parent and select all stars for the row.
        const els = event.currentTarget.parentElement.querySelectorAll(".rating, .rating-no-hover");
        // Loop over each star rating. Add the "hovered" class if:
        //  1) The rating is > the currently selected rating
        //  2) The rating is < the currently "hovered" rating
        for (const el of els) {
            if (!el.classList.contains("rating-star-selected") &&
                parseInt(el.getAttribute("data-rating"), 10) < rating + 1) {
                el.classList.add("rating-star-hovered");
            } else {
                el.classList.remove("rating-star-hovered");
            }
        }
    };

    function setRating(evt, row, rating, url, songList) {
        const els = evt.currentTarget.parentElement.querySelectorAll(".rating");
        for (const el of els) {
            el.classList.remove("rating-star-hovered");
            if (parseInt(el.getAttribute("data-rating", 10)) < rating + 1) {
                el.classList.add("rating-star-selected");
            } else {
                el.classList.remove("rating-star-selected");
            }
        }
        rating = rating + 1;
        if (rating === parseInt(row.rating, 10)) {
            // If we've selected the current rating, treat it
            // as if we've de-selected a rating entirely
            // and remove it.
            rating = "";
        }
        nextTick(() => {
            animateCSS(evt.currentTarget, "heartBeat");
        });
        if (url) {
            doPost(
                url,
                {
                    "song_uuid": row.uuid,
                    "rating": rating,
                },
                () => {
                    for (const song of songList) {
                        if (song.uuid === row.uuid) {
                            song.rating = rating;
                        }
                    }
                },
            );
        }
    };

    function handleRowMouseLeave(event) {
        for (const el of event.currentTarget.querySelectorAll(".rating")) {
            el.classList.remove("rating-star-hovered");
        }
    };

    function handleRowMouseOver(event) {
        for (const el of event.currentTarget.querySelectorAll(".rating")) {
            if (!el.classList.contains("rating-star-selected")) {
                el.classList.add("rating-star-hovered");
            }
        }
    };

    onMounted(() => {
        for (const el of document.getElementsByClassName("song")) {
            el.addEventListener("mouseover", handleRowMouseOver);
            el.addEventListener("mouseleave", handleRowMouseLeave);
        }
    });


    return {
        handleRatingMouseOver,
        handleRatingMouseLeave,
        setRating,
    };
}
