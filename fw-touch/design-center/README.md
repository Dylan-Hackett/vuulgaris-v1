# CapTIvate Design Center project

Design Center **1.83.00.08 (May 2020)**. Its release notes say to re-create projects made in
earlier versions, so do not carry one forward from an older install.

## Device targeting

Design Center projects target a **specific device**. When moving from the FR2676 eval board
to our own FR2675 board, **regenerate for FR2675 (PT/LQFP-48)**. CAP pin *naming* carries
over; physical pins do not.

## Sensor definition

Four sliders. Each: **4 electrodes**, order `E00 E01 E02 E03` mapped to `RX0 RX1 RX2 RX3`.
Geometry is 5 segments / 4 interpolation zones with **RX0 at both ends as a single net**.

Put each slider's four elements in **one measurement block** so they are measured in
parallel. The part has four blocks, which is exactly one per slider.

## Workflow

1. Define sensors here.
2. **Generate.** Output lands in `../captivate/generated/`.
3. Note the electrode-to-pin assignment. **The PCB is laid out to match this**, not the
   reverse.
4. Connect the CAPTIVATE-PGMR to the target board and open the live data view.
5. Tune against **real hardware in the real enclosure next to the real switching supply.**
   Anything else is not tuning.
6. Log results in `../tuning/`.
