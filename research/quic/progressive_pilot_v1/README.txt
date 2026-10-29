Progressive QUIC pilot (v1)
===========================

This is the first progressive INT4 NTC transmission experiment. Its purpose
was to display normally shaded Flame Steak Gaussians while real QUIC streams
delivered successive parameter stages of the current NTC.

The sender transmits four indexed INT4 record groups for each step. The
receiver rebuilds the available weights, predicts Gaussian motion again,
and keeps the existing spherical harmonics colors. This is application-level
ordering of reliable QUIC file streams, not QUIC-internal prioritization.

Priority is estimated using the NTC 114 HashGrid support map and the saved
SalFoM timeline. It is not the same ranking used by the later per-NTC
gradient experiment. The P0 to P3 labels refer to delivery order, not
separately rendered Gaussian tiles.

This historical pilot deliberately inserts noticeable delays between
stages so that intermediate motion can be inspected. It is not intended
as a real-time throughput measurement.

Running the original pilot
--------------------------

The source is in:
    ~/Q3DGStream/research/quic/progressive_pilot_v1

With the viewer stopped, first review the installation changes:

    source ~/venvs/qntcstream/bin/activate
    cd ~/Q3DGStream/research/quic/progressive_pilot_v1
    python install_progressive_quic.py --viewer ~/Q3DGStream

Only apply the changes if the compatibility checks pass and an earlier
working viewer has been preserved:

    python install_progressive_quic.py --viewer ~/Q3DGStream --apply

Create a local QUIC certificate if one is not already available:

    openssl req -x509 -newkey rsa:2048 -nodes -days 1 \
      -subj '/CN=localhost' \
      -keyout /tmp/qntc_progressive.key \
      -out /tmp/qntc_progressive.crt

In the first terminal, run the viewer from ~/Q3DGStream with
QNTC_PROGRESSIVE_QUIC=1 and the receiver's --quic_listen 5002 options.
In the second terminal, launch qntc_progressive_send.py with
--start 0 --end 19 --order saliency --stage-delay 0.65.

This experiment sends the first 20 updates for visual inspection. To
compare the original record order, restart the receiver and change the
sender argument to --order original.

Current recommendations
-----------------------

For the full 299-update CPU-worker receiver, consult the neighboring
progressive_299_v2 directory. For the later independently ranked
299-NTC schedules and Gaussian additions, use dynamic_priority_adapter.
The current documented GPU validation procedure is in docs/GPU_VALIDATION.md.

Do not install this early receiver over an already working v2 receiver:
the v1 installer rewrites experimental source hooks. The viewer, original
NTC checkpoints, and scene data should be backed up before repeating
historical experiments.

The pilot's measured scope is local QUIC delivery with deliberately
delayed stages. It does not establish end-to-end frame rate, image-quality
gains, or native QUIC stream scheduling.
