# simple-cities-digital-twins
Input: 
* polygonal geojson files for roads, sidewalks, parking lots, water, and buildings in the WGS84 projection.
* DEM geotiff file in the UTM zone the city lies in

Output:
* The input geojsons get mapped into 1000m x 1000m tiles.
* Each tile contains an SVG and JPG of the texture for the terrain.
* An OBJ/MTL file gets created for each tile.
* Then you can combine the OBJs for different tiles together.

Here are some screenshots:

Ithaca, NY

<img src="https://github.com/marcus-elia/simple-cities-digital-twins/assets/54640981/ba6e009b-149c-47e8-949a-b874f9d06de5" width="500" height="300" />

Paris, France

<img src="https://github.com/marcus-elia/simple-cities-digital-twins/assets/54640981/a1cd5602-9ff0-4bb9-a32b-d4b2494a555c" width="500" height="300" />

Washington, DC

<img src="https://github.com/marcus-elia/simple-cities-digital-twins/assets/54640981/8c669ebc-f7b0-412b-b8c4-c4a4727cf4ed" width="300" height="300" />
