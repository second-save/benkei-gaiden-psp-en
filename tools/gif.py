"""Animated GIF from PNG frames (README media): gif.py OUT.gif MS_PER_FRAME FRAME.png..."""
import sys
from PIL import Image

out, ms, paths = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
frames = [Image.open(p).convert("RGB").quantize(64, dither=Image.Dither.NONE) for p in paths]
frames[0].save(out, save_all=True, append_images=frames[1:], duration=ms, loop=0, optimize=True)
print(f"{out}: {len(frames)} frames")
