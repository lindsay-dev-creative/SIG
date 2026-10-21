# Product Showcase Video — Reusable Prompt

Copy everything inside the box below into a new Claude Code session that has the Magnific connector enabled. Fill in the `[brackets]` and attach 6–15 product photos showing every side, any engravings or logos, and any moving parts.

---

```
I want to use Magnific to create an AI product showcase video of hands handling [PRODUCT NAME].

PRODUCT
- What it is: [e.g. "a compact women's razor"]
- Key details that must stay accurate: [e.g. "tortoiseshell back, chrome body, script engraving 'the Heirloom', key logo on the cap"]
- Moving parts / interactions: [e.g. "cap slides off to reveal the blade head" — or "none"]
- Reference photos: attached ([number] images)

CREATIVE
- Setting: [e.g. "one or multiple luxury bathrooms, dark wood features"]
- Lighting: [e.g. "moody, but light enough to see the product clearly"]
- Hands: [e.g. "feminine, refined: nude manicure, thin gold ring, ivory silk sleeve"]
- Actions: [e.g. "reveal / pick up, open or remove part, hold in palm, set down for a hero close"]
- Camera: subtle but engaging (slow push-ins, gentle light sweeps)
- Duration: [30–60] seconds
- Audio: [silent / ambient sound effects only / sound effects + music]

DELIVERY
- Where it plays: [e.g. "a tablet held either way"]
- Aspect ratios: [e.g. "4:3 and 3:4"]
- Credit budget: [e.g. "stay under 8,000 credits"]
- Save files to: [folder path]
- Magnific project name: [e.g. "Product Name – Hands Showcase Video"]

HOW TO WORK (lessons from the last project; follow these)
1. Check my credit balance and use simulate_cost before anything that spends credits. Show me a short cost table before committing to a video model.
2. Upload my photos to a new Magnific project. Then generate START FRAMES first, with Nano Banana Pro (imagen-nano-banana-2) at 2k, 2 options per shot, using 3–4 relevant product photos as references for each shot. Show me the best pick for each shot and wait for my approval before making any video.
3. Default video model: Kling 2.5 at 1080p (about 65 credits per second). It accepts 4:3 and 3:4 when the start frame has that shape. Clips are 5s or 10s only, so plan the shot list around that.
4. Keep the motion simple, because the product warps when it's flipped, rotated or orbited:
   - Hands lift, slide, open or set down, keeping the product level. Never flip it.
   - Show movement through light sweeping across the product or a slow camera push-in, not by spinning the product.
   - Every video prompt says the product is "a rigid object that keeps its exact shape" and restates its key details.
5. For the second aspect ratio, DON'T outpaint (it adds junk like signs, keyboards and fake UI). Regenerate each frame natively in the new ratio, using the approved frame as the first reference: "Recreate the first reference image as a vertical portrait composition…"
6. Review every clip by pulling 5 frames into a contact sheet with ffmpeg before accepting it. Redo any clip where the product changes shape, count of parts or materials. If a "nearly still" shot keeps glitching, build it from the start frame with an ffmpeg zoompan push-in instead.
7. Cut the final film with crossfades, a fade in and out, and a 1.5s hold on the last frame for a logo. You can reuse /Users/lindsaydev/Github/SIG/heirloom-video/assemble.sh (expects shot1.mp4 … shot5.mp4 in a folder).
8. Ask me questions whenever a decision is mine to make.
```

---

## Default shot list (adapt per product)

| # | Shot | Length | Motion |
|---|------|--------|--------|
| 1 | Product alone in the setting | 5s | Slow push-in, atmosphere (steam, dust in the light) |
| 2 | Hand reaches in and lifts it | 5s | Lift a few cm, stays level, subtle push-in |
| 3 | Held in the palm, detail side up | 5s | Static camera, light sweeps over it |
| 4 | Signature interaction (open, remove, twist…) | 10s | Slow, precise, push-in on the reveal |
| 5 | Hero close, back in the setting | 10s | Very slow push-in, ends still, room for a logo |

## Prompt templates for doing it by hand in Magnific

**Start frame (Nano Banana Pro, 2k):**
> Photorealistic cinematic [close-up / product still]. [Hand description] [action] the exact product from the reference photos — "[PRODUCT NAME]", [one-line physical description with key details] — [placement] in [setting]. Moody low-key [warm window / sconce] light, deep shadows, but the product is clearly lit with crisp highlights. Natural hand anatomy, exactly five fingers. 85mm lens, shallow depth of field. Keep the product's shape, proportions, engravings and materials identical to the references. No text overlays.

**Video clip (Kling 2.5, 1080p, start frame attached):**
> Luxury product film. [One simple action, e.g. "The hand slowly lifts the product a few centimeters, keeping it level; she does not flip or rotate it."] [Light behavior, e.g. "Warm light glides across the surface."] Camera: [very subtle slow push-in / locked-off]. The product is a rigid object that keeps its exact shape, [key details], the whole time. Moody low-key lighting, [setting], shallow depth of field, cinematic. No text.
