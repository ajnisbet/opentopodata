# Storing Datasets in the Cloud

You may want to store your elevation datasets on a cloud storage provider (like AWS S3, Google Cloud Storage, or Azure Storage) instead of on a persistent local disk. This configuration can be cheaper than provisioning a server with a lot of disk space, and plays nicely with containerised workflows where services are expected to spin up quickly on standard machine types.

Accessing datasets over http will add latency compared reading from a local disk. 

Open Topo Data doesn't currently have specific support for cloud storage, but there are a few different ways to set this up.

Regardless of the approach you take, you probably want to convert your dataset to [cloud optimised geotiffs](https://gdal.org/drivers/raster/cog.html) for best performance.




## Mounting on the host

Tools like [gcsfuse](https://github.com/GoogleCloudPlatform/gcsfuse), [s3fuse](https://github.com/s3fs-fuse/s3fs-fuse), and [rclone](https://rclone.org/commands/rclone_mount/) let you mount cloud storage buckets, folders, and files in your local filesystem. You can then point Open Topo Data at the mounted path.

For example, you could mount a GCS bucket like 

```bash
mkdir /mnt/otd-cloud-datasets/
gcsfuse www-opentopodata-org-public /mnt/otd-cloud-datasets/
```

set up the dataset in `config.yaml`:

```yaml
datasets:
- name: srtm-gcloud-subset
  path: data/test-srtm90m-subset/
```


then when running the docker image, include the mounted bucket as a volume:

```bash
docker run --rm -it --volume /mnt/otd-cloud-datasets/:/app/data:ro -p 5000:5000 opentopodata
```



This is the simplest set and forget way to point Open Topo Data at a dataset living in the cloud. But it requires a long-running host, and access to the host.



## Mounting inside docker


You could do the mounting above inside the docker container, for example by building on the Open Topo Data docker image to add e.g. rclone as a dependency and do the actual mounting.

This lets you mount your cloud dataset without modifying the host. However, getting fuse to work inside a docker container can be [tricky](https://stackoverflow.com/questions/48402218/fuse-inside-docker), and you may not have permissions to do this on some platforms (though it seems [possible on GCE](https://mtlynch.io/retrofit-docker-gcs/)).


## Building a VRT

VRT files are a container format for geospatial rasters, and they support cloud storage through special file paths: for example the path `/vsigs/www-opentopodata-org-public/test-srtm90m-subset/N00E010.hgt` references the file  `/test-srtm90m-subset/N00E010.hgt` in the `www-opentopodata-org-public` bucket on Google Cloud Storage. There's a complete list of the special paths in the [GDAL docs](https://gdal.org/user/virtual_file_systems.html#network-based-file-systems).

Because Open Topo Data understands VRT files, we can build a VRT file wrapping all of the cloud files:

<pre style="white-space : pre-wrap; padding: .525rem .6rem;">
gdalbuildvrt data/gcloud/dataset.vrt /vsigs/www-opentopodata-org-public/test-srtm90m-subset/N00E010.hgt /vsigs/www-opentopodata-org-public/test-srtm90m-subset/N00E011.hgt.zip
</pre>

and load this in Open Topo Data as a single file dataset:

```yaml
datasets:
- name: srtm-gcloud-subset
  path: data/gcloud/
```

finally, you'll need to pass credentials to the docker container:

<pre style="white-space : pre-wrap; padding: .525rem .6rem;">
docker run -it -v /home/XXX/opentopodata/data:/app/data:ro -p 5000:5000 -e GS_SECRET_ACCESS_KEY=XXX -e GS_ACCESS_KEY_ID=XXX opentopodata
</pre>

Again the [GDAL docs](https://gdal.org/user/virtual_file_systems.html#network-based-file-systems) have the format for the credential environment variables.








