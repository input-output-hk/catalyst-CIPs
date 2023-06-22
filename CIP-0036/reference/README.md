# CIP-0036 CDDL Validation and Reference Implementation

This is a simple CDDL validator and Reference implementation for CIP-0036.

It can be used to:

1. Validate the CDDL Document is accurate.
2. Validate independent implementations properly format transaction metadata.
3. Generate the test-vectors.

This tool requires:

1. Docker - <https://docs.docker.com/engine/install/>
2. Earthly - <https://earthly.dev/get-earthly>

## Running the tool

In this directory simply execute:

```sh
earthly +run
```
