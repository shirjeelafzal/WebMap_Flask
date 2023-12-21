
// Initialize the map
var mapView = new ol.View({
  center: ol.proj.fromLonLat([72.585717, 23.021245]),
  zoom: 2
})
var map = new ol.Map({
  target: 'map',
  view: mapView
})
var somTile = new ol.layer.Tile({
  title: 'Open Street Map',
  visible: true,
  source: new ol.source.OSM()
})

map.addLayer(map)
