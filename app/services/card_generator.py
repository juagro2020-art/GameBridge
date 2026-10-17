import io
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, List, Dict, Any

def generate_player_share_card(
    display_name: str,
    public_id: str,
    city: str,
    tier: str,
    elo: float,
    matches_played: int,
    wins: int,
    verified_accounts: List[str],
    draws: int = 0
) -> bytes:
    """
    Generates a shareable PNG Gamer Passport card (800x450) using Pillow.
    """
    width, height = 800, 450
    # Background: dark modern slate gradient / solid
    bg_color = (11, 14, 13)
    card_bg = (20, 26, 23)
    gold_accent = (200, 243, 107)
    green_accent = (102, 213, 162)
    text_white = (242, 245, 241)
    text_gray = (155, 167, 159)

    image = Image.new("RGBA", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    # Inner card frame
    margin = 25
    draw.rounded_rectangle(
        [(margin, margin), (width - margin, height - margin)],
        radius=16,
        fill=card_bg,
        outline=(67, 80, 71),
        width=2
    )

    # Header banner
    draw.rectangle([(margin, margin), (width - margin, margin + 60)], fill=(16, 21, 18))
    
    # Try loading system font, fallback to default
    try:
        font_title = ImageFont.truetype("arial.ttf", 26)
        font_header = ImageFont.truetype("arial.ttf", 18)
        font_large = ImageFont.truetype("arial.ttf", 36)
        font_body = ImageFont.truetype("arial.ttf", 16)
        font_small = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        font_title = ImageFont.load_default()
        font_header = font_title
        font_large = font_title
        font_body = font_title
        font_small = font_title

    # Brand Title
    draw.text((margin + 20, margin + 15), "GAMEBRIDGE ETHIOPIA", fill=gold_accent, font=font_header)
    draw.text((width - margin - 180, margin + 15), "GAMER PASSPORT", fill=text_gray, font=font_header)

    # Player Display Name & Public ID
    draw.text((margin + 30, margin + 90), display_name, fill=text_white, font=font_large)
    draw.text((margin + 30, margin + 140), f"ID: {public_id}  |  City: {city}", fill=text_gray, font=font_body)

    # Badges / Verified game accounts
    acc_text = "Verified: " + (", ".join(verified_accounts) if verified_accounts else "None")
    draw.text((margin + 30, margin + 175), acc_text, fill=green_accent, font=font_body)

    # Horizontal Divider
    draw.line([(margin + 30, margin + 215), (width - margin - 30, margin + 215)], fill=(51, 65, 85), width=1)

    # Stats Columns
    # 1. Platform Elo & Tier
    col1_x = margin + 40
    draw.text((col1_x, margin + 240), "PLATFORM RATING", fill=text_gray, font=font_small)
    draw.text((col1_x, margin + 265), f"{int(elo)} Elo", fill=gold_accent, font=font_title)
    draw.text((col1_x, margin + 305), f"Tier: {tier}", fill=text_white, font=font_body)

    # 2. Match Win/Loss Record
    col2_x = margin + 280
    losses = max(matches_played - wins - draws, 0)
    record = f"{wins}W - {losses}L" + (f" - {draws}D" if draws else "")
    win_rate = round((wins / matches_played * 100), 1) if matches_played > 0 else 0.0
    draw.text((col2_x, margin + 240), "COMPETITIVE RECORD", fill=text_gray, font=font_small)
    draw.text((col2_x, margin + 265), record, fill=text_white, font=font_title)
    draw.text((col2_x, margin + 305), f"Win Rate: {win_rate}%", fill=text_gray, font=font_body)

    # 3. Grassroots Standing
    col3_x = margin + 520
    draw.text((col3_x, margin + 240), "COMPETITIVE PATHWAY", fill=text_gray, font=font_small)
    draw.text((col3_x, margin + 265), "City Ladder", fill=green_accent, font=font_title)
    draw.text((col3_x, margin + 305), "GameBridge Profile", fill=text_white, font=font_body)

    # Footer note
    draw.text(
        (margin + 30, height - margin - 30),
        "Official Ethiopian Esports Competitor Profile  |  gamebridge.et",
        fill=text_gray,
        font=font_small
    )

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
