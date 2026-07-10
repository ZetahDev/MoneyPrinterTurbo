import json
import locale
import os
import re
import shutil
from functools import lru_cache
from pathlib import Path
import threading
from typing import Any
from uuid import uuid4

from loguru import logger

from app.models import const


def get_response(status: int, data: Any = None, message: str = ""):
    obj = {
        "status": status,
    }
    if data:
        obj["data"] = data
    if message:
        obj["message"] = message
    return obj


def to_json(obj):
    try:
        # Define a helper function to handle different types of objects
        def serialize(o):
            # If the object is a serializable type, return it directly
            if isinstance(o, (int, float, bool, str)) or o is None:
                return o
            # If the object is binary data, convert it to a base64-encoded string
            elif isinstance(o, bytes):
                return "*** binary data ***"
            # If the object is a dictionary, recursively process each key-value pair
            elif isinstance(o, dict):
                return {k: serialize(v) for k, v in o.items()}
            # If the object is a list or tuple, recursively process each element
            elif isinstance(o, (list, tuple)):
                return [serialize(item) for item in o]
            # If the object is a custom type, attempt to return its __dict__ attribute
            elif hasattr(o, "__dict__"):
                return serialize(o.__dict__)
            # Return None for other cases (or choose to raise an exception)
            else:
                return None

        # Use the serialize function to process the input object
        serialized_obj = serialize(obj)

        # Serialize the processed object into a JSON string
        return json.dumps(serialized_obj, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"failed to serialize object to json: {str(e)}")
        return None


def get_uuid(remove_hyphen: bool = False):
    u = str(uuid4())
    if remove_hyphen:
        u = u.replace("-", "")
    return u


def root_dir():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


def storage_dir(sub_dir: str = "", create: bool = False):
    d = os.path.join(root_dir(), "storage")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if create and not os.path.exists(d):
        os.makedirs(d)

    return d


def resource_dir(sub_dir: str = ""):
    d = os.path.join(root_dir(), "resource")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    return d


def task_dir(sub_dir: str = ""):
    d = os.path.join(storage_dir(), "tasks")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def font_dir(sub_dir: str = ""):
    d = resource_dir("fonts")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def system_font_dirs() -> list[str]:
    # macOS usually stores user fonts in ~/Library/Fonts and system fonts in
    # /Library/Fonts or /System/Library/Fonts. Keep the list conservative and
    # only include common readable locations.
    home_fonts = os.path.join(Path.home(), "Library", "Fonts")
    return [
        home_fonts,
        "/Library/Fonts",
        "/System/Library/Fonts",
    ]


def get_available_fonts() -> list[dict]:
    """
    Return font candidates from the bundled resource folder and the system fonts.

    Each item has:
        - label: display label for the UI
        - path: absolute font path used by PIL/MoviePy
        - source: resource|system
    """
    candidates: list[dict] = []
    seen = set()

    def add_font(font_path: str, source: str):
        real = os.path.realpath(font_path)
        if real in seen:
            return
        if not os.path.isfile(real):
            return
        seen.add(real)
        candidates.append(
            {
                "label": os.path.basename(real),
                "path": real,
                "source": source,
            }
        )

    resource_fonts = font_dir()
    if os.path.isdir(resource_fonts):
        for entry in sorted(os.listdir(resource_fonts)):
            if entry.lower().endswith((".ttf", ".ttc", ".otf")):
                add_font(os.path.join(resource_fonts, entry), "resource")

    for font_root in system_font_dirs():
        if not os.path.isdir(font_root):
            continue
        for root, _, files in os.walk(font_root):
            for entry in files:
                if entry.lower().endswith((".ttf", ".ttc", ".otf")):
                    add_font(os.path.join(root, entry), "system")

    candidates.sort(key=lambda item: (item["label"].lower(), item["path"]))
    return candidates


def resolve_font_path(font_name_or_path: str) -> str:
    value = (font_name_or_path or "").strip()
    if not value:
        return ""
    if os.path.isabs(value) and os.path.isfile(value):
        return os.path.realpath(value)

    resource_candidate = os.path.join(font_dir(), value)
    if os.path.isfile(resource_candidate):
        return os.path.realpath(resource_candidate)

    for candidate in get_available_fonts():
        if candidate["label"] == value:
            return candidate["path"]

    return value


def song_dir(sub_dir: str = ""):
    d = resource_dir("songs")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def public_dir(sub_dir: str = ""):
    d = resource_dir("public")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def get_ffmpeg_binary() -> str:
    """
    Resuelve el ejecutable de FFmpeg que debe usar el proceso actual.

    Motivo de esta función centralizada:
    1. La codificación de video, la generación de audio silencioso y la transcodificación
       de audio con pydub dependen de FFmpeg;
    2. Los paquetes portables de Windows, Docker y los directorios de instalación
       personalizados frecuentemente causan inconsistencias en el PATH;
    3. Al centralizar la resolución, todos los llamadores usan la misma prioridad,
       reduciendo situaciones donde una ruta funciona pero otra no encuentra FFmpeg.

    Orden de prioridad:
    1. IMAGEIO_FFMPEG_EXE: configuración explícita según la convención de MoviePy/imageio;
    2. ffmpeg en el PATH del sistema;
    3. binario integrado provisto por la dependencia imageio-ffmpeg;
    4. la cadena "ffmpeg" como último recurso, dejando que subprocess exponga un error
       más específico en tiempo de ejecución.
    """
    configured_ffmpeg = os.environ.get("IMAGEIO_FFMPEG_EXE")
    if configured_ffmpeg:
        return configured_ffmpeg

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    try:
        import imageio_ffmpeg

        bundled_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled_ffmpeg:
            return bundled_ffmpeg
    except Exception as exc:
        logger.warning(f"failed to resolve bundled ffmpeg binary: {str(exc)}")

    return "ffmpeg"


def run_in_background(func, *args, **kwargs):
    def run():
        try:
            func(*args, **kwargs)
        except Exception as e:
            logger.error(f"run_in_background error: {e}", exc_info=True)

    thread = threading.Thread(target=run, daemon=False)
    thread.start()
    return thread


def time_convert_seconds_to_hmsm(seconds) -> str:
    hours = int(seconds // 3600)
    seconds = seconds % 3600
    minutes = int(seconds // 60)
    milliseconds = int(seconds * 1000) % 1000
    seconds = int(seconds % 60)
    return "{:02d}:{:02d}:{:02d},{:03d}".format(hours, minutes, seconds, milliseconds)


def text_to_srt(idx: int, msg: str, start_time: float, end_time: float) -> str:
    start_time = time_convert_seconds_to_hmsm(start_time)
    end_time = time_convert_seconds_to_hmsm(end_time)
    srt = """%d
%s --> %s
%s
        """ % (
        idx,
        start_time,
        end_time,
        msg,
    )
    return srt


def str_contains_punctuation(word):
    for p in const.PUNCTUATIONS:
        if p in word:
            return True
    return False


def split_string_by_punctuations(s):
    result = []
    txt = ""

    previous_char = ""
    next_char = ""
    for i in range(len(s)):
        char = s[i]
        if char == "\n":
            result.append(txt.strip())
            txt = ""
            continue

        if i > 0:
            previous_char = s[i - 1]
        if i < len(s) - 1:
            next_char = s[i + 1]

        if char == "." and previous_char.isdigit() and next_char.isdigit():
            # # In the case of "withdraw 10,000, charged at 2.5% fee", the dot in "2.5" should not be treated as a line break marker
            txt += char
            continue

        if char == "," and previous_char.isdigit() and next_char.isdigit():
            # La coma como separador de miles en numeros en ingles no es un delimitador de oraciones, p. ej. "1,000 years".
            # El word boundary de Edge TTS normalmente devuelve ese tipo de numero como contenido continuo;
            # si se divide en "1" y "000 years", la agregacion de subtitulos no podra coincidir con
            # el texto original del guion y retrocederia incorrectamente a Whisper.
            txt += char
            continue

        if char not in const.PUNCTUATIONS:
            txt += char
        else:
            result.append(txt.strip())
            txt = ""
    result.append(txt.strip())
    # filter empty string
    result = list(filter(None, result))
    return result


def normalize_script_for_subtitle_matching(video_script: str) -> str:
    """
    Limpia el texto del guion antes de la coincidencia de subtitulos.

    El usuario puede ingresar manualmente separadores Markdown, enfasis de encabezado
    o simbolos de formato como `_`. Estos caracteres normalmente no aparecen en los
    resultados de TTS/Whisper; si siguen participando en la coincidencia linea a linea,
    el numero de lineas del guion superara el de las lineas de subtitulos, pudiendo
    generar entradas `00:00:00,000 --> 00:00:00,000` que impiden importar el SRT
    en el software de edicion.
    """
    video_script = video_script or ""
    underscore_count = video_script.count("_")
    video_script = video_script.replace("_", "")
    cleaned_lines = []
    removed_separator_lines = 0
    for line in video_script.splitlines():
        line = line.strip()
        # Los separadores o simbolos de enfasis Markdown que aparecen solos en una linea
        # no son leidos por el TTS y deben eliminarse del guion, para evitar que la
        # agregacion de subtitulos quede bloqueada en esas lineas "no pronunciables".
        if re.fullmatch(r"[-*_]{3,}", line):
            removed_separator_lines += 1
            continue
        cleaned_lines.append(line)

    normalized_script = "\n".join(cleaned_lines).strip()
    if underscore_count or removed_separator_lines:
        logger.debug(
            "normalized script for subtitle matching, "
            f"removed underscores: {underscore_count}, "
            f"removed markdown separator lines: {removed_separator_lines}"
        )
    return normalized_script


def md5(text):
    import hashlib

    return hashlib.md5(text.encode("utf-8")).hexdigest()


def get_system_locale():
    try:
        loc = locale.getdefaultlocale()
        # zh_CN, zh_TW return zh
        # en_US, en_GB return en
        language_code = loc[0].split("_")[0]
        return language_code
    except Exception:
        return "en"


@lru_cache(maxsize=None)
def load_locales(i18n_dir):
    # Cada interaccion en el WebUI provoca que Streamlit re-ejecute el script;
    # los archivos de idioma no cambian en tiempo de ejecucion, por lo que se
    # almacena en cache el resultado del analisis para evitar releer y parsear
    # todos los archivos JSON de i18n repetidamente.
    _locales = {}
    for root, dirs, files in os.walk(i18n_dir):
        for file in files:
            if file.endswith(".json"):
                lang = file.split(".")[0]
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    _locales[lang] = json.loads(f.read())
    return _locales


def parse_extension(filename):
    return Path(filename).suffix.lower().lstrip('.')
