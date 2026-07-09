# MoneyPrinterTurbo 💸

[![Stargazers](https://img.shields.io/github/stars/harry0703/MoneyPrinterTurbo.svg?style=for-the-badge)](https://github.com/harry0703/MoneyPrinterTurbo/stargazers)
[![Issues](https://img.shields.io/github/issues/harry0703/MoneyPrinterTurbo.svg?style=for-the-badge)](https://github.com/harry0703/MoneyPrinterTurbo/issues)
[![Forks](https://img.shields.io/github/forks/harry0703/MoneyPrinterTurbo.svg?style=for-the-badge)](https://github.com/harry0703/MoneyPrinterTurbo/network/members)
[![License](https://img.shields.io/github/license/harry0703/MoneyPrinterTurbo.svg?style=for-the-badge)](https://github.com/harry0703/MoneyPrinterTurbo/blob/main/LICENSE)

[简体中文](README.md) | [English](README-en.md) | Español | [العربية](README-ar.md)

[![MoneyPrinterTurbo en Trendshift](https://trendshift.io/api/badge/repositories/8731)](https://trendshift.io/repositories/8731)

Solo necesitas proporcionar un **tema** o una **palabra clave** para un video, y el sistema genera automáticamente el guion, los materiales, los subtítulos y la música de fondo para luego sintetizar un video corto en alta definición.

## WebUI

![Captura de pantalla de la WebUI](docs/webui.jpg)

## Interfaz API

![Captura de pantalla de la interfaz API](docs/api.jpg)

## Cómo se usa

1. Copia `config.example.toml` a `config.toml`.
2. Configura al menos un proveedor de material y el proveedor de IA.
3. Abre la WebUI y escribe un tema o palabra clave.
4. Genera el guion, revisa los materiales sugeridos y exporta el video.

## Instalación

### Opción recomendada: Docker

```bash
docker compose -f docker-compose.release.yml up
```

Luego abre la WebUI en:

- `http://127.0.0.1:8501`

Y la documentación de la API en:

- `http://127.0.0.1:8080/docs`

## Idioma

- La WebUI ya incluye español latino en `webui/i18n/es.json`.
- El generador de guiones responde en el mismo idioma del tema.
- Para obtener contenido en español latino, escribe el tema, el guion y los prompts en español latino.
- La variante predeterminada es español latino; el selector de variante permite cambiar a español de España si alguna vez lo necesitas.
- Los términos de búsqueda de material siguen funcionando mejor en inglés.

## Ejemplos de prompts

### Guion

- `Escribe un guion de 6 párrafos sobre cómo ahorrar dinero sin perder calidad de vida.`
- `Genera un guion para TikTok sobre productividad para emprendedores jóvenes.`

### Prompt personalizado

```text
Escribe en español latino claro, natural y persuasivo. Mantén un tono cercano, directo y útil.
Evita tecnicismos innecesarios y termina cada párrafo con una idea visual clara.
```

### Metadatos sociales

- `Crea un título atractivo y una descripción breve para publicar este video en Instagram.`
- `Genera hashtags relevantes en español latino para un video sobre crecimiento personal.`

## Guía rápida de prompts

### TikTok

- `Escribe un guion corto, directo y con ritmo rápido sobre hábitos financieros para TikTok, en español latino.`
- `Genera un texto con gancho inicial fuerte y cierre con llamada a la acción.`

### YouTube Shorts

- `Crea un guion informativo y claro para YouTube Shorts sobre productividad personal, en español latino.`
- `Usa un tono didáctico, con frases simples y una estructura fácil de seguir.`

### Instagram Reels

- `Redacta un guion aspiracional y visual para Instagram Reels sobre emprendimiento, en español latino.`
- `Incluye una descripción breve, elegante y orientada a interacción.`

## Ejecución rápida

### Docker

```bash
docker compose -f docker-compose.release.yml up
```

### Local

```bash
uv python install 3.11
uv sync --frozen
uv run streamlit run ./webui/Main.py --browser.gatherUsageStats=False --server.showEmailPrompt=False
```

### API

```bash
uv run python main.py
```

### CLI

```bash
uv run python cli.py --video-subject "El papel del dinero"
```
