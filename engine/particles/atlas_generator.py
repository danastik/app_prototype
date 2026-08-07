from PIL import Image
from pathlib import Path
import json
import zipfile
from io import BytesIO

# PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT = "assets/particles"

# OUT_DIR = Path(__file__).resolve().parent
# OUT_DIR = OUT_DIR / "atlas" 
# OUT_DIR.mkdir(exist_ok=True)

OUT_DIR = "generated/atlas"

class AtlasGenerator():
    def __init__(self, ASSETS, archive):
        self.ASSETS = ASSETS
        self.archive = archive
        
    def _generate_atlas(self):
        """
        Generates a png texture atlas and a config file.
        """
        atlas_file = OUT_DIR + "/atlas.png"
        config_file = OUT_DIR + "/atlas.json"

        files = self.archive.namelist()

        #check if source pngs have been modified and if not - return
        # if atlas_file.exists() and config_file.exists():
        #     atlas_time = atlas_file.stat().st_mtime

        #     newest_source = max(
        #         f.stat().st_mtime
        #         for folder in INPUT.iterdir()
        #         if folder.is_dir()
        #         for f in folder.glob("*.png")
        #     )

        #     if atlas_time >= newest_source:
        #         print("  Atlas up to date")
        #         return
            
        print("  Generating...")

        # 1. Load assets
        rows = []
        for asset_name, asset_path in self.ASSETS.items():
            folder = f"{INPUT}/{asset_path}"
            print("getting assets from", folder)

            frames = sorted(
                name for name in self.archive.namelist()
                if name.startswith(folder + "/")
                and name.lower().endswith((".png", ".webp"))
            )

            imgs = []

            for filename in frames:
                with self.archive.open(filename) as f:
                    imgs.append(Image.open(f).convert("RGBA"))

            if not imgs:
                continue

            rows.append((asset_name, frames, imgs))
        

        # 2. Compute atlas size
        atlas_w = max(sum(img.width for img in imgs) for _, _, imgs in rows)
        atlas_h = sum(max(img.height for img in imgs) for _, _, imgs in rows)

        atlas = Image.new("RGBA", (atlas_w, atlas_h))

        # whole atlas information
        meta = {
            "atlas_width": atlas_w,
            "atlas_height": atlas_h,
            "assets": {}
        }

        y = 0

        # 3. Build atlas (per particle type information)
        for asset_name, frames, imgs in rows:
            x = 0
            row_h = max(img.height for img in imgs)

            meta["assets"][asset_name] = {
                "y": y,
                "height": row_h,
                "frame_count": len(imgs),
                "aspect_ratio": imgs[0].width / imgs[0].height,
                "frames": []
            }

            for f, img in zip(frames, imgs):
                atlas.paste(img, (x, y))

                meta["assets"][asset_name]["frames"].append({
                    "file": f.rsplit("/", 1)[-1],  # splits the file name "generate/.../filename.png by "/" and returns last segment which is name"

                    "w": img.width,
                    "h": img.height,

                    "u0": x / atlas_w,
                    "u1": (x + img.width) / atlas_w,

                    "v0": 1.0 - ((y + img.height) / atlas_h),
                    "v1": 1.0 - (y / atlas_h),
                })

                x += img.width

            y += row_h

        # 4. Save outputs

        return # BECAUSE WE used "r" when getting archive and it doesnt allow us to write, and if we write it will just create new files without deleting old ones

        # Save atlas.png
        buffer = BytesIO()
        atlas.save(buffer, format="PNG")

        self.archive.writestr(
            "generated/atlas/atlas.png",
            buffer.getvalue()
        )

        # Save atlas.json
        self.archive.writestr(
            "generated/atlas/atlas.json",
            json.dumps(meta, indent=4)
        )

        print("Atlas generated.")