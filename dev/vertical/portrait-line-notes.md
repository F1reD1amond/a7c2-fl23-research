# Portrait line work in progress

The stock C2 2.01 image banks have no exact matches for the seven corrected
portrait rasters. AP contains separate 480 x 640 and 640 x 480 layout records,
and both layouts reference some of the same original line image IDs. The
three horizontal gauge rasters also have a shared class-level definition;
changing that definition globally would affect landscape gauges.

A1 II 4.00 supplies complete `_23` image banks alongside `_32`, keeping image
IDs while supplying different artwork. C2 currently uses three symlinks from
`_23` to its original `_32` files.

`portraitlines.py` draws the seven corrected images. Their decoded payloads
were compared byte-for-byte with the corresponding private A1 II source
records. The drawing commands retain RGB in transparent pixels. A match with
reference image data does not establish correct C2 placement or physical
rendering; any effect of transparent RGB on C2 interpolation is unverified.

`imagebank.py` plans additional image records in unused indices without
copying complete banks on the camera. One small existing payload is relocated
to EOF, freeing its former byte range for new metadata. Its original image ID
still resolves to its exact original encoded data. New pixels are appended;
new indices are published last. The plan includes all changed bytes and an
exact offline inverse.

On private C2 stock banks, the seven additions require 18,460 appended bytes
and 162 changed bytes across banks 0 and 1. All 7,346 pre-existing encoded
images remain byte-identical through their original IDs. Bank 2 is untouched.

## Manual-test candidate: preview.10.25-portrait.1

The two GUI operations combine saved portrait state, frame resources and
portrait-only AP data references. Enable appends four images, verifies their
bytes, publishes their indices and then edits 15 four-byte references. The
three shared gauge images remain unchanged. Executable code is unchanged.
On stock C2 banks this needs 15,676 appended bytes including recovery footers,
96 changed bank metadata bytes and 60 AP reference bytes. All 7,346 original
encoded images remain unchanged. The native ELF is 29,144 bytes.

Disable saves OFF, switches the running display OFF, restores AP references
and bank metadata, then removes the portrait aliases. This is one operation
without an intermediate reboot or second button. If running mappings still
refer to appended image data, retain that small inert tail rather than
truncate it under the current UI. A later normal disable/reset can reclaim it
once original loaded references are present; functional disable does not
require this optional space reclamation.

The native worker preserves current private mapped pages before editing
file-backed bytes. It publishes indices only after appended data and donor
relocation are durable. Partial append/metadata writes can be replanned from
current bytes and the on-camera footer without replaying a host job. It does
not perform a production image-size query or require another reload before
writing. Full byte readback remains part of each write operation.

101 offline regression cases passed, including the actual native AArch64
worker under emulation, short I/O, interrupted writes, repeated operations,
close ordering and combined installation. A development mode-0 probe on the
owner's camera performed no firmware, resource or setting writes. It checked
the native reader on original IDs; it did not validate recognition or
rendering of the newly appended IDs. Physical layout/navigation acceptance
is pending the owner's manual test.
