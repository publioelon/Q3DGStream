# Bounded progressive QUIC receiver (v2)

The second progressive receiver experiment addresses memory use and stage updates over the complete 299-NTC sequence. Rather than rebuilding every dense NTC on the viewer thread, it decodes the current and nearby stages in a CPU worker.

The receiver keeps at most 10 dense NTC states in its CPU cache. Incoming `.qblk` stages are stored compactly, and sparse INT4 decoding is vectorized. A new stage becomes visible only after its CPU parameter buffer has been prepared. The viewer continues to perform CUDA inference and drawing on its existing rendering thread.

The code preserves the original Gaussian attributes and colors.

## Integrating the receiver

Use the integrated Q3DGStream viewer with its progressive hooks in `main.py` and `renderer_cuda.py`. The installer checks those hooks and replaces only the two experimental sidecars.

With the viewer and sender stopped:

```bash
source ~/venvs/qntcstream/bin/activate
cd ~/Q3DGStream/research/quic/progressive_299_v2

python test_quic_v2.py
python test_receiver_state_machine_v2.py
python install_bounded_progressive_v2.py --viewer ~/Q3DGStream
```

Inspect the dry-run output before applying the update:

```bash
python install_bounded_progressive_v2.py --viewer ~/Q3DGStream --apply
```

The installer creates backups ending in `.before_bounded_progressive_v2` and does not change the original scene or NTC checkpoints. If the local viewer already uses the same v2 files, no replacement is needed.

## Playback

A local TLS certificate and key must exist at `/tmp/qntc_progressive.crt` and `/tmp/qntc_progressive.key`. Start the receiver and sender in separate terminals from this directory:

```bash
bash run_receiver.sh
```

```bash
bash run_sender.sh
```

The default sender delay is 45 ms after each priority stage. Four pauses per NTC limit the rate of complete animation updates to approximately 5.5 per second, before transfer and decoding costs. This delay is useful for inspecting intermediate states, not for measuring a 30-update-per-second streaming rate.

For a faster transfer:

```bash
QNTC_STAGE_DELAY=0.008 bash run_sender.sh
```

At short intervals, several stages may arrive between rendered frames, making intermediate reconstruction less visible.

Logs are written to `/tmp/qntc_receiver_v2.log` and `/tmp/qntc_sender_v2.log`. The receiver reports completed CPU stage decodes using messages such as `[QUIC CPU READY] NTC=... stages=1/4`.

## Interpretation

The v2 sender uses the saved binary HashGrid dependency map for NTC 114 together with an interpolated SalFoM timeline. Its ordering is not the full per-frame gradient-based ranking from `research/priority/dynamic_299/`.

The four stages are ordered groups of weight records, not independently decodable geometric regions. The code was checked against synthetic CPU stages and the previous receiver hooks. Live CUDA playback must be checked separately before treating this historical experiment as a performance result.

To restore the previous sidecar versions, stop the processes and run:

```bash
python install_bounded_progressive_v2.py --viewer ~/Q3DGStream --restore --apply
```

This restores only the two sidecars.
