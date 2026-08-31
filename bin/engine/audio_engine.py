import threading
import random
import time
from io import BytesIO

import numpy as np
import sounddevice as sd
import soundfile as sf


# Максимальный размер файла, который постоянно хранится в RAM.
# Например:
# 5 * 1024 * 1024 = 5 MB
MAX_SIZE = 5 * 1024 * 1024


class AudioEngine:

    def __init__(self, sounds, archive):
        self.active_sounds = []
        self.active_loops = {}

        self.sounds_config = sounds
        self.archive = archive

        self.sounds = {}

        self.lock = threading.Lock()

        # Звуки, которые в данный момент загружаются
        # из архива в отдельном потоке.
        self.loading_sounds = set()

        # Audio device
        device_info = sd.query_devices(kind="output")

        self.sample_rate = int(device_info["default_samplerate"])
        print(f"Output sample rate: {self.sample_rate}")

        self.load_all_sounds()

        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            callback=self.callback
        )

        self.stream.start()

        # --------------------------------------------------
        # Loop worker
        # --------------------------------------------------

        self.loop_thread = threading.Thread(
            target=self.loop_worker,
            daemon=True
        )

        self.loop_thread.start()


    def _load_audio(self, path):
        total_start = time.perf_counter()

        start = time.perf_counter()

        with self.archive.open(path) as file:
            open_time = (time.perf_counter() - start)
            print(f"[Audio] archive.open(): "f"{open_time * 1000:.2f} ms")

            start = time.perf_counter()
            data = file.read()

            read_time = (time.perf_counter() - start)

        print(
            f"[Audio] file.read(): "
            f"{path} | "
            f"{read_time * 1000:.2f} ms "
            f"({len(data) / 1024 / 1024:.2f} MB)"
        )


        start = time.perf_counter()

        samples, sr = sf.read(
            BytesIO(data),
            dtype="float32"
        )

        decode_time = (time.perf_counter() - start)

        print(
            f"[Audio] sf.read(): "
            f"{path} | "
            f"{decode_time * 1000:.2f} ms"
        )

        # Stereo → Mono
        start = time.perf_counter()

        if samples.ndim > 1:
            samples = samples.mean(axis=1)

        samples = np.asarray(
            samples,
            dtype=np.float32
        )

        mono_time = (time.perf_counter() - start)

        print(
            f"[Audio] Mono conversion: "
            f"{path} | "
            f"{mono_time * 1000:.2f} ms"
        )

        # Sample-rate conversion
        resample_time = 0.0

        if sr != self.sample_rate:

            start = time.perf_counter()

            ratio = (self.sample_rate / sr)

            old = np.arange(len(samples), dtype=np.float32)

            new = np.arange(
                0,
                len(samples),
                1 / ratio,
                dtype=np.float32
            )

            samples = np.interp(
                new,
                old,
                samples
            ).astype(np.float32)

            resample_time = (time.perf_counter() - start)

            print(f"[Audio] Sample-rate conversion: "f"{resample_time * 1000:.2f} ms")

        total_time = (time.perf_counter() -total_start)

        print(
            f"[Audio] _load_audio() total: "
            f"{path} | "
            f"{total_time * 1000:.2f} ms"
        )

        return samples

    def load_all_sounds(self):

        for sound_name, cfg in (self.sounds_config.items()):

            # Проверяем вероятности вариантов
            probability_sum = sum(
                probability
                for _, probability
                in cfg["variants"]
            )

            if not np.isclose(
                probability_sum,
                1.0,
                atol=1e-6
            ):

                raise ValueError(f"{sound_name} probabilities must sum to 1.0")

            loaded_variants = []

            # Загружаем варианты
            for filename, probability in (cfg["variants"]):

                path = (f"assets/sounds/{filename}")

                file_info = (
                    self.archive.getinfo(path)
                )

                file_size = file_info.file_size

                # --------------------------------------------------
                # Маленький файл
                # --------------------------------------------------

                if file_size <= MAX_SIZE:

                    samples = self._load_audio(
                        path
                    )

                    loaded_variants.append({
                        "type": "memory",
                        "samples": samples,
                        "probability": probability
                    })

                    print(
                        f"[Audio] Loaded into RAM: "
                        f"{filename} "
                        f"({file_size / 1024:.1f} KB)"
                    )

                # --------------------------------------------------
                # Большой файл
                # --------------------------------------------------

                else:

                    loaded_variants.append({
                        "type": "archive",
                        "path": path,
                        "filename": filename,
                        "probability": probability
                    })

                    print(
                        f"[Audio] Stored in archive: "
                        f"{filename} "
                        f"({file_size / 1024 / 1024:.2f} MB)"
                    )

            self.sounds[sound_name] = (
                cfg |
                {
                    "variants": loaded_variants
                }
            )

    # ======================================================
    # Variant selection
    # ======================================================

    def choose_variant(self, sound_name):

        variants = (
            self.sounds[sound_name]["variants"]
        )

        r = random.random()
        acc = 0.0

        for variant in variants:

            acc += variant["probability"]

            if r <= acc:
                return variant

        return variants[-1]

    # ======================================================
    # Parameters
    # ======================================================

    def _calculate_parameters(self, cfg, volume, speed):
        # Volume
        base_volume = cfg["volume"]
        volume_variance = cfg.get("volume_variance",  0.0)

        if volume is not None:
            base_volume *= volume

        final_volume = (base_volume * (1 + random.uniform(-volume_variance, volume_variance)))

        # Speed
        base_speed = cfg.get("speed", 1.0)
        speed_variance = cfg.get("speed_variance", 0.0)

        if speed is not None:
            base_speed *= speed

        final_speed = (base_speed * (1 + random.uniform(-speed_variance, speed_variance)))

        return (final_volume, final_speed)


    def _change_speed(self, samples, speed):
        if speed == 1.0:
            return samples

        positions = np.arange(
            0,
            len(samples),
            speed,
            dtype=np.float32
        )

        indices = np.arange(
            len(samples),
            dtype=np.float32
        )

        return np.interp(
            positions,
            indices,
            samples
        ).astype(np.float32)

    def _add_active_sound(
        self,
        sound_name,
        samples,
        volume
    ):

        with self.lock:

            self.active_sounds.append({
                "name": sound_name,
                "samples": samples,
                "position": 0,
                "volume": volume
            })

    def _play_instance(
        self,
        sound_name,
        volume=None,
        speed=None
    ):

        cfg = self.sounds[
            sound_name
        ]

        variant = self.choose_variant(
            sound_name
        )

        final_volume, final_speed = (
            self._calculate_parameters(
                cfg,
                volume,
                speed
            )
        )

        # --------------------------------------------------
        # Маленький звук
        # --------------------------------------------------

        if variant["type"] == "memory":

            samples = variant["samples"]

            # Если скорость отличается от 1,
            # сначала полностью подготавливаем
            # изменённую версию.
            if final_speed != 1.0:

                samples = self._change_speed(
                    samples,
                    final_speed
                )

            self._add_active_sound(
                sound_name,
                samples,
                final_volume
            )

            return

        # --------------------------------------------------
        # Большой звук
        # --------------------------------------------------

        with self.lock:

            # Если этот звук уже загружается,
            # второй поток не создаём.
            if sound_name in self.loading_sounds:
                return

            self.loading_sounds.add(
                sound_name
            )

        thread = threading.Thread(
            target=self._load_large_sound_async,
            args=(
                sound_name,
                variant,
                final_volume,
                final_speed
            ),
            daemon=True
        )

        thread.start()

    def _load_large_sound_async(
        self,
        sound_name,
        variant,
        volume,
        speed
    ):
        start_time = time.perf_counter()

        try:

            print(
                f"[Audio] Loading large sound: "
                f"name={sound_name}, "
                f"file={variant['path']}"
            )

            # --------------------------------------------
            # Загрузка и декодирование WAV
            # --------------------------------------------

            load_start = time.perf_counter()

            samples = self._load_audio(
                variant["path"]
            )

            load_time = (
                time.perf_counter() -
                load_start
            )

            # --------------------------------------------
            # Изменение скорости
            # --------------------------------------------

            speed_time = 0.0

            if speed != 1.0:

                speed_start = time.perf_counter()

                samples = self._change_speed(
                    samples,
                    speed
                )

                speed_time = (
                    time.perf_counter() -
                    speed_start
                )

            # --------------------------------------------
            # Добавляем готовый звук
            # --------------------------------------------

            self._add_active_sound(
                sound_name,
                samples,
                volume
            )

            total_time = (
                time.perf_counter() -
                start_time
            )

            print(
                f"[Audio] Ready: "
                f"{variant['filename']} "
                f"in {total_time * 1000:.2f} ms"
            )

            print(
                f"[Audio]   Load:  "
                f"{load_time * 1000:.2f} ms"
            )

            if speed != 1.0:
                print(
                    f"[Audio]   Speed: "
                    f"{speed_time * 1000:.2f} ms"
                )

        except Exception as e:

            print(
                f"[Audio] Failed to load "
                f"{variant['filename']}: {e}"
            )

        finally:

            with self.lock:

                self.loading_sounds.discard(
                    sound_name
                )

    # public methods
    def play(self, sound_name, volume=None, speed=None):

        cfg = self.sounds[sound_name]

        if cfg.get("loop", False):
            with self.lock:

                if sound_name in (self.active_loops):
                    return

                self.active_loops[sound_name] = {
                    "volume": volume,
                    "speed": speed,
                    "next_play": time.perf_counter()
                }

            return

        # Normal sound
        self._play_instance(
            sound_name,
            volume,
            speed
        )

    def stop(self, sound_name):
        with self.lock:
            self.active_loops.pop(sound_name, None)

    def kill(self, sound_name):
        with self.lock:
            self.active_sounds = [
                sound
                for sound in self.active_sounds
                if sound["name"] != sound_name
            ]

            self.active_loops.pop(sound_name, None)

    def loop_worker(self):
        while True:
            now = time.perf_counter()

            to_play = []

            with self.lock:

                for (sound_name, loop_data) in list(self.active_loops.items()):

                    if now >= loop_data["next_play"]:

                        cfg = self.sounds[sound_name]

                        base_delay = cfg.get("loop_delay", 0.0)
                        variance = cfg.get("loop_delay_variance", 0.0)

                        factor = (1 + random.uniform(-variance, variance))
                        delay = (base_delay * factor)
                        delay = max(0.0, delay)

                        loop_data["next_play"] = now + delay

                        to_play.append((
                            sound_name,
                            loop_data["volume"],
                            loop_data["speed"]
                        ))

            for (sound_name, volume, speed) in to_play:
                self._play_instance(
                    sound_name,
                    volume,
                    speed
                )

            time.sleep(0.005)

    # Audio callback
    def callback(self, outdata, frames, time_info, status):

        mix = np.zeros(frames, dtype=np.float32)

        with self.lock:

            alive = []

            for sound in self.active_sounds:

                samples = sound["samples"]
                position = sound["position"]

                # Берём только нужный кусок готового массива.
                #
                # Здесь НЕТ:
                # - np.interp
                # - ресемплинга
                # - чтения файлов
                # - изменения speed

                end = min(
                    position + frames,
                    len(samples)
                )

                if position >= end:
                    continue

                chunk = samples[position:end]

                # Volume control
                mix[:len(chunk)] += (chunk * sound["volume"])

                sound["position"] = end

                if end < len(samples):
                    alive.append(sound)

            self.active_sounds = alive

        # Prevent clipping
        np.clip(mix, -1.0, 1.0, out=mix)

        outdata[:, 0] = mix