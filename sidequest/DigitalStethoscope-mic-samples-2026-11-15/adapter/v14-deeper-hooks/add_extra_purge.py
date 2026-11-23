"""Add an extra hot purge to the start of a sliced Bambu job, after the standard purge at 250 °C.

Usage: add_extra_purge.py <job.gcode.3mf> <extra millimetres of filament>
The standard start of a single-filament job pushes 105 mm of filament through the nozzle into the chute after the
AMS has loaded it. When the previous job used another material, more is needed to push out what is left of it.
"""
import hashlib
import sys
import zipfile
from pathlib import Path

FILAMENT_AREA = 2.405
GCODE = "Metadata/plate_1.gcode"
ANCHOR = "M109 S250 ;set nozzle to common flush temp\nM106 P1 S0\nG92 E0\n"
MARKER = "; extra purge: clears the previous job's material\n"

job = Path(sys.argv[1])
extra = float(sys.argv[2])
with zipfile.ZipFile(job) as archive:
    entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
contents = {info.filename: data for info, data in entries}
gcode = contents[GCODE].decode("utf-8")
if MARKER in gcode:
    raise SystemExit("job already has the extra purge")
start = gcode.index(ANCHOR) + len(ANCHOR)
first_purge = "G1 E50 F200\nM400\n"
position = gcode.index(first_purge, start) + len(first_purge)
gcode = gcode[:position] + MARKER + f"G92 E0\nG1 E{extra:g} F200\nM400\n" + gcode[position:]
contents[GCODE] = gcode.encode("utf-8")
contents[GCODE + ".md5"] = hashlib.md5(contents[GCODE]).hexdigest().upper().encode()
temporary = job.with_suffix(".tmp")
with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
    for info, _ in entries:
        archive.writestr(info, contents[info.filename])
temporary.replace(job)
total = 105 + extra
print(f"purge after loading: {total:g} mm of filament, about {total * FILAMENT_AREA:.0f} mm3 "
      f"(standard 105 mm, about {105 * FILAMENT_AREA:.0f} mm3)")
