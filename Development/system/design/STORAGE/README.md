# STORAGE detailed design

[Record interface](interfaces-and-behavior.md) defines persistence owned by L1_STORAGE. L2_COMMUNICATION decides when Wi-Fi credentials are read, validated and committed.

[Server profile](server-profile.md) defines the deployment file, its validation, the image built from it and the flash command.

## How the server profile reaches the device

1. One [deployment file](server-profile.md#deployment-file) per server deployment holds the server's HTTPS base URL, its keep-alive timeout and its public certificate.
2. The server profile tool on the developer PC validates the file and the certificate and builds the server profile image, protected by a CRC-32 checksum.
3. The [flash command](server-profile.md#commands) writes only that image to the server profile partition at `0xF00000`. The firmware and the settings partition stay unchanged.
4. At boot, L1_STORAGE reads and validates the image once and hands endpoint, keep-alive and certificate to L2_COMMUNICATION. A missing or invalid image leaves secure transport unavailable; Wi-Fi setup and offline listening keep working. The [validation stages](server-profile.md#validation-stages) show which check runs on the PC, at boot and during connection setup.

The [flash layout](interfaces-and-behavior.md#flash-layout) defines the partitions and the image format.
