// Returns longitude in pixels at a certain zoom level
function lngToX($lon, $zoom) {
  $offset = 256 << ($zoom-1);
  return $offset + ($offset * $lon / 180);
}
// Returns latitude in pixels at a certain zoom level
function latToY($lat, $zoom) {
  $offset = 256 << ($zoom-1);
  return $offset - $offset/Math.PI * Math.log((1 + Math.sin($lat * Math.PI / 180)) / (1 - Math.sin($lat * Math.PI / 180))) / 2;
}

/*
 * Draws points on a map image whereby points is an array of:
 *
 *   point:
 *      lng - longitude of the point
 *      lat - latitude of the point
 *      size - the size of the marker for the point (default 5)
 *      click - function to run when clicked
 */
function drawPointsOnMap(id, img, origWidth, lat, lng, zoom, points, strokeStyle, fillStyle) {
    var canvas = document.getElementById(id);
    if (canvas && canvas.getContext){
    var pen = canvas.getContext("2d");
    var map = new Image();
    map.src = img;

    canvas.width = map.width;
    canvas.height = map.height;
    canvas.points = points;
    pen.drawImage(map, 0, 0, map.width, map.height);

    var ratio = map.width / (origWidth*1.0);

    var left = lngToX(lng, zoom);
    var top = latToY(lat, zoom);
    var registerClicks = false;

    for (var idx in points) {
      var point = points[idx];
      var x = lngToX(point.lng, zoom) - left;
      var y = latToY(point.lat, zoom) - top;

      // console.log("X: " + x);
      // console.log("Y: " + y);

      x *= ratio;
      y *= ratio;

      point.x = x;
      point.y = y;

      pen.strokeStyle = strokeStyle;
      pen.fillStyle = fillStyle;
      pen.beginPath();
      pen.arc(x,y,point.size,0,Math.PI*2,true);
      pen.closePath();
      pen.stroke();
      pen.fill();

      if (point.click) {
	registerClicks = true;
      }

    }

    if (registerClicks) {
      canvas.addEventListener("click", function(e) {
	for (idx in points) {
	  var point = points[idx];

	  var buffer = 5;
	  var clickX = (e.offsetX) + buffer;
	  var clickY = (e.offsetY) + buffer;
	  if (clickX > point.x && clickX < point.x + point.size + (buffer * 2)
	      && clickY > point.y && clickY < point.y + point.size + (buffer * 2)) {
	    point.click();
	    return;
	  }
	}
      }, true);

      canvas.style.cursor = "pointer";	    

    }

  } else {
  }
}

function drawPointOnMapWithColor(id, img, origWidth, lat, lng, zoom, ptLat, ptLng, size, click, strokeStyle, fillStyle){
    var point = {};
    point.lng = ptLng;
    point.lat = ptLat;
    point.size = size;
    point.click = click;

    drawPointsOnMap(id, img, origWidth, lat, lng, zoom, Array(point), strokeStyle, fillStyle);
}

/*
 * Draws a point on a map image. 
 *         id: the id of the canvas object to draw to
 *        img: the image to draw a point on
 *  origWidth: the original width of the image 
 *        lat: the top most lat coordinate of the map image
 *        lng: the left most lng coordinate of the map image
 *       zoom: the zoom factor of the original image
 *      ptLat: the lat coordinate of the point you want to draw
 *      ptLng: the lng coordinate of the point you want to draw
 *       size: the size of the point to draw
 */
function drawPointOnMap(id, img, origWidth, lat, lng, zoom, ptLat, ptLng, size, click){
    drawPointOnMapWithColor(id, img, origWidth, lat, lng, zoom, ptLat, ptLng, size, click, "#c5aa73", "#c12337")
}
