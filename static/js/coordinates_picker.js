var map_marker = null;
var map = null;

function setLatLng(lat, lng){
    var lat = Math.round(lat*1000000)/1000000;
    var lng = Math.round(lng*1000000)/1000000;

    $("#coordinates_value").text(lat + ", " + lng);
    $("#lat").attr("value", lat);
    $("#lng").attr("value", lng);

    if (map_marker){
        map_marker.setMap(null);
    }

    latLng = new google.maps.LatLng(lat, lng);

    map_marker = new google.maps.Marker({
        position: latLng,
        draggable: true,
        map: map
    });

    map.panTo(latLng);
}

$(document).ready(function(){
    var lat = $("#map_lat").attr("value");
    var lng = $("#map_lng").attr("value");
    var zoom = $("#map_zoom").attr("value");

    var latlng = new google.maps.LatLng(5.015359, 36.60866);
    if (lat && lng){
        latlng = new google.maps.LatLng(lat, lng);
    } 

    if (!zoom){
        zoom = 5;
    } else {
        zoom = parseInt(zoom);
    }

    var options = {
        zoom: zoom,
        center: latlng,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        disableDoubleClickZoom: true
    };
    map = new google.maps.Map(document.getElementById("coordinates_picker"), options);

    function selectPoint(event){
        setLatLng(event.latLng.lat(), event.latLng.lng())
    }
    google.maps.event.addListener(map, 'dblclick', selectPoint);

    // set our initial position if we have one
    var lat = $("#lat").attr("value");
    var lng = $("#lng").attr("value");

    // set our initial marker
    if (lat && lng){
        latLng = new google.maps.LatLng(lat, lng);
        map_marker = new google.maps.Marker({
            position: latLng,
            draggable: true,
            map: map
        });

        if (!map.getBounds().contains(latLng)){
            map.panTo(latLng);
        }
    }
});

