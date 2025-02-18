function initAutocomplete() {
    const options = { types: ['address'] };
    const startingAutocomplete = new google.maps.places.Autocomplete(document.getElementById('id_origin_address'), options);
    const finishingAutocomplete = new google.maps.places.Autocomplete(document.getElementById('id_destination_address'), options);
}

google.maps.event.addDomListener(window, 'load', initAutocomplete);
