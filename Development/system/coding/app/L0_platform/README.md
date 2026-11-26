# L0 Platform

Layer L0 is Zephyr: its drivers, its DMA and interrupt handling and the devicetree board
overlay in `../boards/`. The modules in `../L1_services/` call the Zephyr driver APIs directly.
The folder contains no code: the firmware has no driver or HAL layer of its own.
