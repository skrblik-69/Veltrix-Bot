import discord
from discord.ext import commands
import re
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Union, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class TimeParseError(Exception):
    """Výjimka pro chyby při parsování času"""
    pass

class ValidationError(Exception):
    """Výjimka pro validační chyby"""
    pass

def parse_time_string(time_str: str) -> timedelta:
    """
    Parsuje časový řetězec do timedelta objektu
    
    Podporované formáty:
    - 10s, 30sec, 45sekund
    - 5m, 15min, 30minut
    - 2h, 1hour, 3hodin
    - 1d, 7day, 14dní
    - Kombinace: 1h30m, 2d12h30m
    
    Args:
        time_str: Řetězec s časem (např. "1h30m", "45s")
        
    Returns:
        timedelta: Parsovaný čas
        
    Raises:
        TimeParseError: Při neplatném formátu
    """
    if not time_str:
        raise TimeParseError("Časový řetězec nesmí být prázdný")
    
    time_str = time_str.lower().strip()
    
    # Mapování jednotek na sekundy
    time_units = {
        's': 1, 'sec': 1, 'sekund': 1, 'sekunda': 1, 'sekundy': 1,
        'm': 60, 'min': 60, 'minut': 60, 'minuta': 60, 'minuty': 60,
        'h': 3600, 'hour': 3600, 'hodin': 3600, 'hodina': 3600, 'hodiny': 3600,
        'd': 86400, 'day': 86400, 'den': 86400, 'dní': 86400, 'dny': 86400
    }
    
    total_seconds = 0
    
    # Pattern pro nalezení čísel s jednotkami
    pattern = r'(\d+)\s*([a-záčďéěíňóřšťúůýž]+)'
    matches = re.findall(pattern, time_str)
    
    if not matches:
        raise TimeParseError(f"Neplatný formát času: {time_str}")
    
    for amount_str, unit in matches:
        try:
            amount = int(amount_str)
        except ValueError:
            raise TimeParseError(f"Neplatné číslo: {amount_str}")
        
        if unit not in time_units:
            raise TimeParseError(f"Neplatná jednotka času: {unit}")
        
        total_seconds += amount * time_units[unit]
    
    if total_seconds <= 0:
        raise TimeParseError("Čas musí být větší než 0")
    
    return timedelta(seconds=total_seconds)

def format_time_delta(delta: timedelta) -> str:
    """
    Formátuje timedelta do českého čitelného formátu
    
    Args:
        delta: Časový rozdíl
        
    Returns:
        str: Formátovaný čas (např. "2 hodiny 30 minut")
    """
    total_seconds = int(delta.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds} sekund"
    
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    parts = []
    
    if days > 0:
        if days == 1:
            parts.append("1 den")
        elif days < 5:
            parts.append(f"{days} dny")
        else:
            parts.append(f"{days} dní")
    
    if hours > 0:
        if hours == 1:
            parts.append("1 hodina")
        elif hours < 5:
            parts.append(f"{hours} hodiny")
        else:
            parts.append(f"{hours} hodin")
    
    if minutes > 0:
        if minutes == 1:
            parts.append("1 minuta")
        elif minutes < 5:
            parts.append(f"{minutes} minuty")
        else:
            parts.append(f"{minutes} minut")
    
    if seconds > 0 and not parts:  # Zobrazit sekundy pouze pokud nejsou větší jednotky
        if seconds == 1:
            parts.append("1 sekunda")
        elif seconds < 5:
            parts.append(f"{seconds} sekundy")
        else:
            parts.append(f"{seconds} sekund")
    
    return " ".join(parts[:2])  # Maximálně 2 jednotky

def format_number(number: int, currency_name: str = None) -> str:
    """
    Formátuje číslo s mezerami jako oddělovači tisíců
    
    Args:
        number: Číslo k formátování
        currency_name: Název měny (volitelné)
        
    Returns:
        str: Formátované číslo
    """
    formatted = f"{number:,}".replace(",", " ")
    
    if currency_name:
        return f"{formatted} {currency_name}"
    
    return formatted

def validate_user_input(input_str: str, max_length: int = 2000, 
                       min_length: int = 1, allow_mentions: bool = True) -> str:
    """
    Validuje uživatelský vstup
    
    Args:
        input_str: Vstupní řetězec
        max_length: Maximální délka
        min_length: Minimální délka
        allow_mentions: Zda povolit zmínky (@everyone, @here)
        
    Returns:
        str: Validovaný vstup
        
    Raises:
        ValidationError: Při neplatném vstupu
    """
    if not input_str:
        raise ValidationError("Vstup nesmí být prázdný")
    
    input_str = input_str.strip()
    
    if len(input_str) < min_length:
        raise ValidationError(f"Vstup musí mít alespoň {min_length} znaků")
    
    if len(input_str) > max_length:
        raise ValidationError(f"Vstup nesmí být delší než {max_length} znaků")
    
    if not allow_mentions:
        if "@everyone" in input_str.lower() or "@here" in input_str.lower():
            raise ValidationError("Zmínky @everyone a @here nejsou povoleny")
    
    return input_str

def create_embed(title: str, description: str = None, color: int = 0x3498db,
                timestamp: bool = True, **kwargs) -> discord.Embed:
    """
    Vytvoří standardizovaný embed
    
    Args:
        title: Titulek embedu
        description: Popis embedu
        color: Barva embedu
        timestamp: Zda přidat časové razítko
        **kwargs: Další argumenty pro embed
        
    Returns:
        discord.Embed: Vytvořený embed
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        **kwargs
    )
    
    if timestamp:
        embed.timestamp = datetime.utcnow()
    
    return embed

def create_error_embed(message: str, title: str = "❌ Chyba") -> discord.Embed:
    """
    Vytvoří error embed s jednotným stylem
    
    Args:
        message: Chybová zpráva
        title: Titulek chyby
        
    Returns:
        discord.Embed: Error embed
    """
    return create_embed(
        title=title,
        description=message,
        color=0xe74c3c
    )

def create_success_embed(message: str, title: str = "✅ Úspěch") -> discord.Embed:
    """
    Vytvoří success embed s jednotným stylem
    
    Args:
        message: Zpráva o úspěchu
        title: Titulek úspěchu
        
    Returns:
        discord.Embed: Success embed
    """
    return create_embed(
        title=title,
        description=message,
        color=0x2ecc71
    )

def create_warning_embed(message: str, title: str = "⚠️ Varování") -> discord.Embed:
    """
    Vytvoří warning embed s jednotným stylem
    
    Args:
        message: Varovná zpráva
        title: Titulek varování
        
    Returns:
        discord.Embed: Warning embed
    """
    return create_embed(
        title=title,
        description=message,
        color=0xf39c12
    )

def check_permissions(member: discord.Member, required_perms: List[str]) -> Dict[str, bool]:
    """
    Zkontroluje oprávnění člena
    
    Args:
        member: Člen k kontrole
        required_perms: Seznam požadovaných oprávnění
        
    Returns:
        dict: Slovník s výsledky kontroly
    """
    results = {}
    perms = member.guild_permissions
    
    perm_mapping = {
        'administrator': perms.administrator,
        'manage_guild': perms.manage_guild,
        'manage_channels': perms.manage_channels,
        'manage_messages': perms.manage_messages,
        'manage_roles': perms.manage_roles,
        'kick_members': perms.kick_members,
        'ban_members': perms.ban_members,
        'mute_members': perms.mute_members,
        'deafen_members': perms.deafen_members,
        'move_members': perms.move_members,
        'view_audit_log': perms.view_audit_log
    }
    
    for perm in required_perms:
        results[perm] = perm_mapping.get(perm, False)
    
    return results

def has_higher_role(user1: discord.Member, user2: discord.Member) -> bool:
    """
    Zkontroluje, zda má user1 vyšší roli než user2
    
    Args:
        user1: První uživatel
        user2: Druhý uživatel
        
    Returns:
        bool: True pokud má user1 vyšší roli
    """
    return user1.top_role > user2.top_role

def clean_text(text: str, remove_mentions: bool = True, 
               remove_links: bool = False, max_length: int = None) -> str:
    """
    Vyčistí text od nežádoucích elementů
    
    Args:
        text: Text k vyčištění
        remove_mentions: Zda odstranit zmínky
        remove_links: Zda odstranit odkazy
        max_length: Maximální délka (ořízne a přidá ...)
        
    Returns:
        str: Vyčištěný text
    """
    if not text:
        return ""
    
    cleaned = text.strip()
    
    if remove_mentions:
        # Odstranění Discord zmínek
        cleaned = re.sub(r'<@!?\d+>', '[uživatel]', cleaned)
        cleaned = re.sub(r'<@&\d+>', '[role]', cleaned)
        cleaned = re.sub(r'<#\d+>', '[kanál]', cleaned)
    
    if remove_links:
        # Odstranění HTTP/HTTPS odkazů
        cleaned = re.sub(r'https?://\S+', '[odkaz]', cleaned)
    
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length-3] + "..."
    
    return cleaned

def get_user_status_emoji(status: discord.Status) -> str:
    """
    Získá emoji pro status uživatele
    
    Args:
        status: Discord status
        
    Returns:
        str: Emoji reprezentující status
    """
    status_map = {
        discord.Status.online: "🟢",
        discord.Status.idle: "🟡",
        discord.Status.dnd: "🔴",
        discord.Status.offline: "⚫",
        discord.Status.invisible: "⚫"
    }
    
    return status_map.get(status, "❓")

def get_activity_text(member: discord.Member) -> str:
    """
    Získá text reprezentující aktivitu uživatele
    
    Args:
        member: Discord člen
        
    Returns:
        str: Text aktivity
    """
    if not member.activities:
        return "Žádná aktivita"
    
    activity = member.activities[0]
    
    if isinstance(activity, discord.Game):
        return f"🎮 Hraje {activity.name}"
    elif isinstance(activity, discord.Streaming):
        return f"📺 Streamuje {activity.name}"
    elif isinstance(activity, discord.Activity):
        if activity.type == discord.ActivityType.listening:
            return f"🎵 Poslouchá {activity.name}"
        elif activity.type == discord.ActivityType.watching:
            return f"📺 Sleduje {activity.name}"
        else:
            return f"🎯 {activity.name}"
    elif isinstance(activity, discord.CustomActivity):
        if activity.name:
            return f"💭 {activity.name}"
    
    return "Žádná aktivita"

async def safe_send(channel, *args, **kwargs) -> Optional[discord.Message]:
    """
    Bezpečně pošle zprávu do kanálu s error handlingem
    
    Args:
        channel: Kanál kam poslat zprávu
        *args: Argumenty pro send
        **kwargs: Keyword argumenty pro send
        
    Returns:
        discord.Message nebo None při chybě
    """
    try:
        return await channel.send(*args, **kwargs)
    except discord.Forbidden:
        logger.warning(f"Nemám oprávnění poslat zprávu do {channel}")
    except discord.HTTPException as e:
        logger.error(f"HTTP chyba při odesílání zprávy: {e}")
    except Exception as e:
        logger.error(f"Neočekávaná chyba při odesílání zprávy: {e}")
    
    return None

async def safe_edit(message: discord.Message, *args, **kwargs) -> bool:
    """
    Bezpečně upraví zprávu s error handlingem
    
    Args:
        message: Zpráva k úpravě
        *args: Argumenty pro edit
        **kwargs: Keyword argumenty pro edit
        
    Returns:
        bool: True při úspěchu, False při chybě
    """
    try:
        await message.edit(*args, **kwargs)
        return True
    except discord.NotFound:
        logger.warning("Zpráva k úpravě nebyla nalezena")
    except discord.Forbidden:
        logger.warning("Nemám oprávnění upravit zprávu")
    except discord.HTTPException as e:
        logger.error(f"HTTP chyba při úpravě zprávy: {e}")
    except Exception as e:
        logger.error(f"Neočekávaná chyba při úpravě zprávy: {e}")
    
    return False

async def safe_delete(message: discord.Message, delay: float = None) -> bool:
    """
    Bezpečně smaže zprávu s error handlingem
    
    Args:
        message: Zpráva ke smazání
        delay: Zpoždění před smazáním (volitelné)
        
    Returns:
        bool: True při úspěchu, False při chybě
    """
    try:
        if delay:
            await asyncio.sleep(delay)
        await message.delete()
        return True
    except discord.NotFound:
        logger.debug("Zpráva ke smazání nebyla nalezena")
    except discord.Forbidden:
        logger.warning("Nemám oprávnění smazat zprávu")
    except discord.HTTPException as e:
        logger.error(f"HTTP chyba při mazání zprávy: {e}")
    except Exception as e:
        logger.error(f"Neočekávaná chyba při mazání zprávy: {e}")
    
    return False

def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Ořízne řetězec na maximální délku a přidá suffix
    
    Args:
        text: Text k oříznutí
        max_length: Maximální délka
        suffix: Text přidaný na konec při oříznutí
        
    Returns:
        str: Oříznutý text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def create_progress_bar(current: int, maximum: int, length: int = 10, 
                       fill_char: str = "█", empty_char: str = "░") -> str:
    """
    Vytvoří progress bar v textové podobě
    
    Args:
        current: Aktuální hodnota
        maximum: Maximální hodnota
        length: Délka progress baru
        fill_char: Znak pro vyplněnou část
        empty_char: Znak pro prázdnou část
        
    Returns:
        str: Progress bar
    """
    if maximum <= 0:
        return empty_char * length
    
    percentage = min(current / maximum, 1.0)
    filled_length = int(length * percentage)
    
    bar = fill_char * filled_length + empty_char * (length - filled_length)
    return f"`{bar}` {percentage:.1%}"

def get_guild_icon_or_default(guild: discord.Guild) -> str:
    """
    Získá ikonu guildy nebo defaultní URL
    
    Args:
        guild: Discord guild
        
    Returns:
        str: URL ikony
    """
    if guild.icon:
        return guild.icon.url
    
    # Defaultní Discord ikona
    return "https://cdn.discordapp.com/embed/avatars/0.png"

def chunks(lst: List, n: int) -> List[List]:
    """
    Rozdělí seznam na chunky o velikosti n
    
    Args:
        lst: Seznam k rozdělení
        n: Velikost chunku
        
    Returns:
        List[List]: Seznam chunků
    """
    return [lst[i:i + n] for i in range(0, len(lst), n)]

def ordinal_czech(number: int) -> str:
    """
    Převede číslo na řadovou číslovku v češtině
    
    Args:
        number: Číslo
        
    Returns:
        str: Řadová číslovka
    """
    if number == 1:
        return "1."
    elif number == 2:
        return "2."
    elif number == 3:
        return "3."
    else:
        return f"{number}."

async def confirm_action(ctx, message: str, timeout: int = 30) -> Optional[bool]:
    """
    Vyžádá potvrzení akce od uživatele
    
    Args:
        ctx: Command context
        message: Zpráva s potvrzením
        timeout: Timeout pro odpověď
        
    Returns:
        bool nebo None: True pro potvrzení, False pro zamítnutí, None pro timeout
    """
    embed = create_warning_embed(
        f"{message}\n\nReaguj ✅ pro potvrzení nebo ❌ pro zrušení."
    )
    
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    
    def check(reaction, user):
        return (user == ctx.author and 
                reaction.message.id == msg.id and 
                str(reaction.emoji) in ["✅", "❌"])
    
    try:
        reaction, user = await ctx.bot.wait_for("reaction_add", timeout=timeout, check=check)
        
        if str(reaction.emoji) == "✅":
            return True
        elif str(reaction.emoji) == "❌":
            return False
    except asyncio.TimeoutError:
        pass
    finally:
        await safe_delete(msg)
    
    return None
