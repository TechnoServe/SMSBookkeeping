var map = null;

function setBounds(){
    var lat = map.center.lat();
    var lng = map.center.lng();
    var zoom = map.zoom;

    lat = Math.round(lat*1000000)/1000000;
    lng = Math.round(lng*1000000)/1000000;

    $("#bounds_value").text("Zoom: " + zoom + " Center: " + lat + ", " + lng);

    $("#bounds_zoom").attr("value", zoom);
    $("#bounds_lat").attr("value", lat);
    $("#bounds_lng").attr("value", lng);

    latLng = new google.maps.LatLng(lat, lng);
    map.panTo(latLng);
}

$(document).ready(function(){
    var lat = $("#bounds_lat").attr("value");
    var lng = $("#bounds_lng").attr("value");
    var zoom = $("#bounds_zoom").attr("value");

    var latlng = new google.maps.LatLng(5.015359, 36.60866);
    if (lat && lng && zoom){
        latlng = new google.maps.LatLng(lat, lng);
        zoom = parseInt(zoom);
    } else {
        zoom = 5;
    }

    var options = {
        zoom: zoom,
        center: latlng,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        disableDoubleClickZoom: true
    };
    map = new google.maps.Map(document.getElementById("bounds_map"), options);
    google.maps.event.addListener(map, 'dblclick', setBounds);
});

