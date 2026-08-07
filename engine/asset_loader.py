import sys, os, random, time, math
from PySide6.QtGui import QPainter, QPixmap, QPen, QColor

import zipfile

from OpenGL.GL import * #type: ignore

class AssetLoader:

    @staticmethod
    def load_QPixmap_frames(archive: zipfile.ZipFile, folder):  # function for loading frames, recieves a string path to a folder, returns a list of png files( converted to PixMap ) in name order
        """
        Returns a list of QPixmap files taken from .png files from the provided folder.
        
        :param folder: Path to the folder. (not from base)
        """
        frames = []

        files = sorted(
            name for name in archive.namelist()
            if name.startswith(folder + "/")
            and name.lower().endswith((".png", ".webp"))
        )

        for filename in files:
            data = archive.read(filename)
            pix = QPixmap()
            # print("appending image file", filename)

            if not pix.loadFromData(data):
                raise ValueError(f"Could not load {filename}")

            frames.append(pix)

        return frames
    

    @staticmethod
    def load_openGL_texture(archive: zipfile.ZipFile, path):
        """
        Returns a openGL texture file taken from a path.
        
        :param folder: Path to the texture(inside archive)
        """
        from PIL import Image
        import os

        with archive.open(path) as f:
            img = Image.open(f).convert("RGBA")
            img_data = img.tobytes("raw", "RGBA", 0, -1)

        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            img.width,
            img.height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            img_data
        )

        glBindTexture(GL_TEXTURE_2D, 0)

        return tex_id