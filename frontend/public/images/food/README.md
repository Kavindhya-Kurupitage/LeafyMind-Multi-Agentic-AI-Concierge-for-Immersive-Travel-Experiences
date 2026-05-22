# Leafy Cave food images

Place dish photos here. Vite serves them at `/images/food/<filename>`.

## How the Food Guide picks an image

1. **Local file** — matched by dish name (case-insensitive), including your filenames below  
2. **Unsplash** — if no local file matches, and `UNSPLASH_ACCESS_KEY` is set in `.env`

After adding or renaming photos, restart the backend (or run Food Guide again; the service rescans the folder each request).

## Your photos → database dish names

| Dish name (database) | Your filename |
|----------------------|---------------|
| Rice and Curry | `Red-Rice-and-Curry.jpg` |
| Hoppers (Appam) | `Hoppers.jpg` |
| Egg Hoppers | `Hoppers.jpg` (shared) |
| Kottu Roti | `Kottu-Roti.jpg` |
| Dhal Curry (Parippu) | `Parippu-Curry.jpg` |
| Fish Ambul Thiyal | `Ambul-Thiyal.jpg` |
| String Hoppers (Idiyappam) | `String-Hoppers.jpg` |
| Watalappan | `Watalappam.jpg` |
| Pol Sambol | `Gotukola-Sambol.jpg` (approximate) |
| Wood Apple Juice | *(no local file — uses Unsplash if configured)* |

Supported extensions: `.jpg`, `.jpeg`, `.png`, `.webp`.

## Unsplash fallback

In the project root `.env`:

```env
UNSPLASH_ACCESS_KEY=your_access_key_from_unsplash.com/developers
```

Then:

```powershell
docker compose restart leafymind-backend
docker exec leafymind-backend python -m scripts.verify_external_services
```

Dishes without a matching local file will load photos from `images.unsplash.com` in the Food Guide cards.
