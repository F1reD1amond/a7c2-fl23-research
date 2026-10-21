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

This branch has an offline planner only. It has no camera executor for these
additions, no AP portrait-reference patch, and no GUI activation. Static Fn
and frame references have been located; shared gauge selection still needs
tracing. A device implementation must finish and read back appended data
before relocating the donor pointer, and must preserve the old payload until
its replacement pointer is durable. Interruption/resume behavior and actual
C2 display placement remain to be implemented and tested.
