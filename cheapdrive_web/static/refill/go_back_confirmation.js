
let isNavigatingAway = false;
function showModal() {
    document.getElementById("confirmationModal").style.display = "flex";
}

function hideModal() {
    document.getElementById("confirmationModal").style.display = "none";
}

// Add a fake history entry to detect back button

history.pushState(null, "", location.href);
window.onpopstate = function (event) {
    if (!isNavigatingAway) {
        showModal();
        history.pushState(null, "", location.href); // Push back to prevent actual navigation
    }
    
};
document.addEventListener("submit", function () {
    isNavigatingAway = true;
    window.onbeforeunload = null; // Remove the warning before form submission
});
document.getElementById("confirmBack").addEventListener("click", function () {
    isNavigatingAway = true;

    if (typeof( needsRefill )=== "undefined" || !needsRefill)  {
        window.history.go(-2);  // Go back one page
    } else {
        window.history.go(-4);  // If refill is needed, go back 2 pages ()
    }
    hideModal();
});

document.getElementById("cancelBack").addEventListener("click", function () {
    hideModal();
});

window.onbeforeunload = function (event) {
    if (!isNavigatingAway) {
        return "Are you sure you want to leave this page? Any unsaved data will be lost.";
    }
};