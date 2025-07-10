import nextcord
from datetime import datetime
from typing import Optional, Union, List, Dict

def make_embed(
    title: Optional[str] = None,
    desc: Optional[str] = None,
    color: Union[int, nextcord.Color] = nextcord.Color.default(),
    url: Optional[str] = None,
    footer: Optional[str] = None,
    footer_icon: Optional[str] = None,
    author: Optional[str] = None,
    author_icon: Optional[str] = None,
    thumbnail: Optional[str] = None,
    image: Optional[str] = None,
    fields: Optional[List[Dict[str, Union[str, bool]]]] = None,
    timestamp: Optional[datetime] = None
) -> nextcord.Embed:
    # Convert int to nextcord.Color
    if isinstance(color, int):
        color = nextcord.Color(value=color)

    # Convert nextcord.Color to raw int if needed
    try:
        raw_color = color.value
    except AttributeError:
        raw_color = 0x2F3136  # fallback

    em = nextcord.Embed(title=title, description=desc, color=raw_color, url=url)

    if footer:
        em.set_footer(text=footer, icon_url=footer_icon) if footer_icon else em.set_footer(text=footer)
    if author:
        em.set_author(name=author, icon_url=author_icon) if author_icon else em.set_author(name=author)
    if thumbnail:
        em.set_thumbnail(url=thumbnail)
    if image:
        em.set_image(url=image)
    if fields:
        for field in fields:
            em.add_field(
                name=field.get("name", "—"),
                value=field.get("value", "Không có nội dung"),
                inline=field.get("inline", False)
            )
    if timestamp:
        em.timestamp = timestamp

    return em