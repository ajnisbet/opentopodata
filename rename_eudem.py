from glob import glob
import os
import re

old_pattern = './data/eudem/eu_dem_v11_E*N*.TIF'
old_paths = list(glob(old_pattern))
print('Found {} files'.format(len(old_paths)))

for old_path in old_paths:
    folder = os.path.dirname(old_path)
    old_filename = os.path.basename(old_path)

    # Extract north and east coords, pad with zeroes.
    res = re.search(r'(E\d\d)(N\d\d)', old_filename)
    easting, northing = res.groups()
    northing = northing + '00000'
    easting = easting + '00000'

    # Rename in place.
    new_filename = '{}{}.tif'.format(northing, easting)
    new_path = os.path.join(folder, new_filename)
    os.rename(old_path, new_path)
