from PIL import Image
from pathlib import Path
import json
import zipfile
from io import BytesIO
import os

from engine.exceptions import AtlasMissingError

INPUT = "assets/particles"

atlas_path = "generated/atlas/atlas.png"
config_path = "generated/atlas/atlas.json"

class AtlasGenerator():
    def __init__(self, ASSETS, archive):
        self.ASSETS = ASSETS
        self.archive = archive


    def atlas_exists(self) -> bool:
        files = self.archive.namelist()

        required_files = [atlas_path, config_path]
        atlas_exists = True

        for filename in required_files:
            if filename not in files:
                print(f"Missing: {filename}")
                atlas_exists = False

        return atlas_exists
    
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
        
    def generate_atlas(self, archive_path):
        """
        Generates a png texture atlas and a config file.
        """
        self.archive = zipfile.ZipFile(archive_path, "r")

        print("  Generating atlas...")

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
        print("  Closing old archive")
        self.archive.close()

        buffer = BytesIO()
        atlas.save(buffer, format="PNG")
        atlas_data = buffer.getvalue()

        print("  Writing new archive")
        temp_path = archive_path + ".tmp"

        with zipfile.ZipFile(archive_path, "r") as old_archive:
            with zipfile.ZipFile(temp_path, "w") as new_archive:
                for item in old_archive.infolist():
                    if not item.filename.startswith("generated/atlas/"):
                        new_archive.writestr(item, old_archive.read(item.filename))

                new_archive.writestr(
                    "generated/atlas/atlas.png",
                    atlas_data
                )

                new_archive.writestr(
                    "generated/atlas/atlas.json",
                    json.dumps(meta, indent=4)
                )

        print("  Replacing files")
        os.replace(temp_path, archive_path)

        print("  Opening new archive")
        new_archive = zipfile.ZipFile(archive_path, "r")

        print("Atlas generated.")

        return new_archive