# simple-cities-digital-twins
Input: 
* polygonal geojson files for roads, sidewalks, parking lots, water, and buildings in the WGS84 projection.
* DEM geotiff file in the UTM zone the city lies in

Output:
* The input geojsons get mapped into 1000m x 1000m tiles.
* Each tile contains an SVG and JPG of the texture for the terrain.
* An OBJ/MTL file gets created for each tile.
* Then you can combine the OBJs for different tiles together.

Here is the current state of Ithaca, NY:

<img src="https://github.com/marcus-elia/simple-cities-digital-twins/assets/54640981/776f6cdf-c8f4-44f8-a729-e915e49e8b72" width="300" height="300" />
<img src="https://github.com/marcus-elia/simple-cities-digital-twins/assets/54640981/1924b65e-cf30-48ba-bb6f-92c1ec21df39" width="300" height="300" />
<img src="https://github.com/marcus-elia/simple-cities-digital-twins/assets/54640981/2e713a8a-6c8b-4a1b-a483-2c3e8f3ce6fc" width="300" height="300" />


