// https://davidwalsh.name/javascript-debounce-function
function debounce(func, wait, immediate) {
  var timeout;
  return function() {
    var context = this, args = arguments;
    var later = function() {
      timeout = null;
      if (!immediate) func.apply(context, args);
    };
    var callNow = immediate && !timeout;
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
    if (callNow) func.apply(context, args);
  };
};


// Get the lat,lon string from the form. Returns null for invalid input.
var loadLocation = function() {
  try {
    var lat = document.getElementById("point-form-lat").value.trim();
    var lon = document.getElementById("point-form-lon").value.trim();

    if (lat === '' || lon === '') {
      return null;
    }

    if (!isFinite(lat) || !isFinite(lon)) {
      return null;
    }

    var latLon = lat + ',' + lon;
    return latLon

  } catch (error) {
    return null
  }
}

// API dataset IDs, taken from DOM table.
var validDatasets = function() {
    var resultLinkElements = document.querySelectorAll('[data-dataset-id]');
    return Array.from(resultLinkElements).map(x => x.dataset.datasetId);
}

// Prefetch locations. Cached on the server.
var _prefetch = function() {
  var location = loadLocation();
  if (location == null) {
    return
  }

  var datasetIDs = validDatasets();
  datasetIDs.forEach(function (id, index) {
    var url = "https://api.opentopodata.org/v1/" + id + "?prefetch&demo&locations=" + location;
    console.log(url);
  })
}
var prefetch = debounce(_prefetch, 1000);


var setElevation = function(id, text, link) {
  const selector = '[data-dataset-id="' + id + '"]';
  var e = document.querySelector(selector);

  if (!link) {
    e.innerHTML = '<em>' + text + '</em>';
  }
}

var setAllElevation = function(text) {
  var datasetIDs = validDatasets();
  datasetIDs.forEach(function (id, index) {
    setElevation(id, text);
  });
}

var fetch = function() {
  var location = loadLocation();
  var datasetIDs = validDatasets();

  // Validate locations.
  if (location == null) {
    setAllElevation('Invalid input')
    return
  }

  setAllElevation('Loading...')

  datasetIDs.forEach(function (id, index) {
    let url = "https://api.opentopodata.org/v1/" + id + "?demo&locations=" + location;
    let timeoutTimer = setTimeout(function() {setElevation(id, 'Request timeout')}, 2000);

  })


}

var main = function(){
  // Find elements.
  var form = document.getElementById("point-form");
  var latInput = document.getElementById("point-form-lat");
  var lonInput = document.getElementById("point-form-lon");

  // Register prefetch.
  lonInput.addEventListener("input", function (e) {
    prefetch();
  })

  // Register main fetch.
  form.addEventListener("submit", function(e) {
    e.preventDefault();
    fetch();
  })




  // // Capture form output.


  //   var lat = document.getElementById("point-form-lat").value;
  //   var lon = document.getElementById("point-form-lon").value;
  //   var latlon = lat + ',' + lon;


  //   console.log(latlon);




  // });


};

if (
    document.readyState === "complete" ||
    (document.readyState !== "loading" && !document.documentElement.doScroll)
) {
  main();
} else {
  document.addEventListener("DOMContentLoaded", main);
}