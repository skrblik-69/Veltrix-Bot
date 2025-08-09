@bot.event
async def on_member_join(member):
    # ID kanálu pro uvítání (nahraď svým)
    WELCOME_CHANNEL_ID = 1403013049065017355
    
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        member_count = member.guild.member_count
        await channel.send(
            f"Ahoj {member.mention}! 🎉 Vítej na serveru **{member.guild.name}**.\n"
            f"Jsi náš **{member_count}. člen**!"
        )
        