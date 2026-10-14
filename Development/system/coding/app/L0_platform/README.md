# L0 Platform

Intentionally empty. L0 is Zephyr itself: its drivers, DMA/interrupt handling and the
devicetree board overlay in `../boards/`. L1 adapters call Zephyr driver APIs directly,
so there is no own driver or HAL layer here.
