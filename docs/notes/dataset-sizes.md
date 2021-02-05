# Dataset sizes

The table below lists the file sizes of the datasets on the public APIs server.

In most cases I converted the source files to compressed geotiffs, and the sizes given are after that conversion. A freshly downloaded dataset could be much larger depending on the format, but compressing with [gdal](https://gdal.org/programs/gdal_translate.html) should result in a size similar to what I ended up with.





<table>
	<thead>
		<tr>
			<th>API id</th>
			<th>Dataset</th>
			<th>Compressed File Size</th>
			<th>Notes</th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td><a href="/datasets/bkg/">bkg200</a></td>
			<td>BKG 200m, Germany</td>
			<td>32&nbsp;MB</td>
			<td></td>
		</tr>
		<tr>
			<td><a href="/datasets/etopo1/">etopo1</a></td>
			<td>ETOPO 1 arcminute land and bathymetry</td>
			<td>1&nbsp;GB</td>
			<td></td>
		</tr>
		<tr>
			<td><a href="/datasets/gebco2020/">gebco2020</a></td>
			<td>GEBCO global bathymetry (2020)</td>
			<td>3&nbsp;GB</td>
			<td></td>
		</tr>
		<tr>
			<td><a href="/datasets/emod2018/">emod2018</a></td>
			<td>EMOD Europe bathymetry (2018)</td>
			<td>3&nbsp;GB</td>
			<td>After conversion from <code>.asc</code> to compressed <code>.geotiff</code>.</td>
		</tr>
		<tr>
			<td><a href="/datasets/nzdem/">nzdem8m</a></td>
			<td>New Zealand 8m DEM</td>
			<td>9&nbsp;GB</td>
			<td></td>
		</tr>
		<tr>
			<td><a href="/datasets/srtm/">srtm90m</a></td>
			<td>SRTM ~90m</td>
			<td>12&nbsp;GB</td>
			<td>After conversion from <code>.hgt</code> to compressed <code>.geotiff</code>.</td>
		<tr>
			<td><a href="/datasets/eudem/">eudem25m</a></td>
			<td>Europe 25m DEM</td>
			<td>22&nbsp;GB</td>
			<td></td>
		</tr>
		<tr>
			<td><a href="/datasets/srtm/">srtm30m</a></td>
			<td>SRTM ~30m</td>
			<td>73&nbsp;GB</td>
			<td></td>
		</tr>
		<tr>
			<td><a href="/datasets/mapzen/">mapzen</a></td>
			<td>Mapzen ~30m</td>
			<td>142&nbsp;GB</td>
			<td>After conversion from <code>.hgt</code> format to compressed <code>.geotiff</code>. The source files are 100s of GB larger.</td>
		</tr>
		<tr>
			<td><a href="/datasets/aster/">aster30m</a></td>
			<td>ASTER ~30m</td>
			<td>151&nbsp;GB</td>
			<td></td>
		</tr>
		</tr>
		<tr>
			<td><a href="/datasets/ned/">ned10m</a></td>
			<td>US National Elevation Dataset (1/3 arcsecond)</td>
			<td>260&nbsp;GB</td>
			<td></td>
		</tr>
	</tbody>
</table>
