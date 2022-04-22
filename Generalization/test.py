from minio import Minio
from minio.error import S3Error


def main():
    # Create a client with the MinIO server playground, its access key
    # and secret key.
    client = Minio(
        endpoint="47.93.217.159:9000",
        access_key="minioadmin",
        secret_key="juCy3D1Z",
        secure=False
    )
    objects = client.list_objects(
        "simulation-cloud", prefix="批量泛化场景/ACC",
    )

    # Upload '/home/user/Photos/asiaphotos.zip' as object name
    # 'asiaphotos-2015.zip' to bucket 'asiatrip'.
    # found = client.bucket_exists("ACC_1-1")
    # if not found:
    #     client.make_bucket("ACC_1-1")
    # else:
    #     print("Bucket 'asiatrip' already exists")
    result = client.fput_object(
        "simulation-cloud", "批量泛化场景/AEB/ACC_1-1/ACC_1-1_0.xosc", "D:/泛化/trails/simulation_new/ACC_1-1_0/ACC_1-1_0.xosc"
    )
    print(
        "created {0} object; etag: {1}, version-id: {2}".format(
            result.object_name, result.etag, result.version_id,
        ),
    )


if __name__ == "__main__":
    try:
        main()
    except S3Error as exc:
        print("error occurred.", exc)
