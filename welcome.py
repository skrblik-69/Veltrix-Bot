@bot.event
async def on_member_join(member):
    # ID kanálu pro uvítání
    'WELCOME_CHANNEL_ID' = 1403013049065017355
    
    print(f"{member.name} se připojil k serveru.")  # Debug výstup
    
    channel = bot.get_channel('WELCOME_CHANNEL_ID')
    if channel:
        print(f"Posílám uvítací zprávu do kanálu: {channel.name}")  # Debug výstup
        member_count = member.guild.member_count
        await channel.send(
            f"Ahoj {member.mention}! 🎉 Vítej na serveru **{member.guild.name}**.\n"
            f"Jsi náš **{member_count}. člen**!"
        )
    else:
        print("Kanál pro uvítání nebyl nalezen. Ujisti se, že je správné ID kanálu.")