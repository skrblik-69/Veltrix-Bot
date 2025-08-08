import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random
import asyncio
import logging

logger = logging.getLogger(__name__)

class Economy(commands.Cog):
    """Ekonomický systém s měnou, prací a obchodováním"""
    
    def __init__(self, bot):
        self.bot = bot
        self.currency_name = bot.config['currency_name']
        self.currency_symbol = bot.config['currency_symbol']
    
    async def _ensure_user_exists(self, user_id: int, guild_id: int):
        """Zajistí, že uživatel existuje v databázi"""
        await self.bot.db.create_user_economy(user_id, guild_id)
    
    @commands.hybrid_command(name='bilance', aliases=['balance', 'bal'])
    async def balance(self, ctx, uživatel: discord.Member = None):
        """Zobrazí bilanci uživatele"""
        target = uživatel or ctx.author
        
        await self._ensure_user_exists(target.id, ctx.guild.id)
        user_data = await self.bot.db.get_user_economy(target.id, ctx.guild.id)
        
        if not user_data:
            return await ctx.send("❌ **Nastala chyba při načítání dat!**")
        
        embed = discord.Embed(
            title=f"{self.currency_symbol} Bilance",
            color=0x2ecc71,
            timestamp=datetime.utcnow()
        )
        
        embed.set_author(
            name=target.display_name,
            icon_url=target.display_avatar.url
        )
        
        embed.add_field(
            name="💰 Peněženka",
            value=f"**{user_data['balance']:,}** {self.currency_name}",
            inline=True
        )
        
        embed.add_field(
            name="🏦 Banka",
            value=f"**{user_data['bank']:,}** {self.currency_name}",
            inline=True
        )
        
        embed.add_field(
            name="💎 Celkem",
            value=f"**{user_data['balance'] + user_data['bank']:,}** {self.currency_name}",
            inline=True
        )
        
        embed.add_field(
            name="📊 Statistiky",
            value=f"**Level:** {user_data['level']}\n"
                  f"**XP:** {user_data['xp']:,}\n"
                  f"**Varování:** {user_data['warnings']}",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name='denní', aliases=['daily'])
    @commands.cooldown(1, 86400, commands.BucketType.user)  # 24 hodin
    async def daily_reward(self, ctx):
        """Denní odměna"""
        await self._ensure_user_exists(ctx.author.id, ctx.guild.id)
        
        daily_amount = self.bot.config['daily_amount']
        success = await self.bot.db.update_balance(ctx.author.id, ctx.guild.id, daily_amount)
        
        if success:
            embed = discord.Embed(
                title="🎁 Denní odměna",
                description=f"Obdržel jsi **{daily_amount:,}** {self.currency_name}!",
                color=0x2ecc71,
                timestamp=datetime.utcnow()
            )
            
            embed.set_author(
                name=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url
            )
            
            embed.add_field(
                name="💡 Tip",
                value="Vracívej se každý den pro svou denní odměnu!",
                inline=False
            )
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ **Nastala chyba při přidávání denní odměny!**")
    
    @commands.hybrid_command(name='práce', aliases=['work'])
    @commands.cooldown(1, 3600, commands.BucketType.user)  # 1 hodina
    async def work(self, ctx):
        """Práce za odměnu"""
        await self._ensure_user_exists(ctx.author.id, ctx.guild.id)
        
        jobs = [
            "programování", "psaní článků", "grafický design", "překládání",
            "testování aplikací", "správa sociálních sítí", "vytváření obsahu",
            "analýza dat", "zákaznická podpora", "výuka online"
        ]
        
        min_earn = self.bot.config['work_min']
        max_earn = self.bot.config['work_max']
        earned = random.randint(min_earn, max_earn)
        job = random.choice(jobs)
        
        success = await self.bot.db.update_balance(ctx.author.id, ctx.guild.id, earned)
        
        if success:
            embed = discord.Embed(
                title="💼 Práce dokončena",
                description=f"Pracoval jsi jako **{job}** a vydělal jsi **{earned:,}** {self.currency_name}!",
                color=0x3498db,
                timestamp=datetime.utcnow()
            )
            
            embed.set_author(
                name=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.url
            )
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ **Nastala chyba při přidávání odměny za práci!**")
    
    @commands.hybrid_command(name='poslat', aliases=['pay', 'send'])
    async def pay_user(self, ctx, příjemce: discord.Member, částka: int):
        """Pošle peníze jinému uživateli"""
        if příjemce.bot:
            return await ctx.send("❌ **Nemůžeš posílat peníze botům!**")
        
        if příjemce == ctx.author:
            return await ctx.send("❌ **Nemůžeš posílat peníze sám sobě!**")
        
        if částka <= 0:
            return await ctx.send("❌ **Částka musí být větší než 0!**")
        
        await self._ensure_user_exists(ctx.author.id, ctx.guild.id)
        await self._ensure_user_exists(příjemce.id, ctx.guild.id)
        
        sender_data = await self.bot.db.get_user_economy(ctx.author.id, ctx.guild.id)
        
        if sender_data['balance'] < částka:
            return await ctx.send(f"❌ **Nemáš dostatek {self.currency_name}! Máš pouze {sender_data['balance']:,}.**")
        
        # Transakce
        sender_success = await self.bot.db.update_balance(ctx.author.id, ctx.guild.id, -částka)
        receiver_success = await self.bot.db.update_balance(příjemce.id, ctx.guild.id, částka)
        
        if sender_success and receiver_success:
            embed = discord.Embed(
                title="💸 Transakce úspěšná",
                description=f"{ctx.author.mention} poslal **{částka:,}** {self.currency_name} uživateli {příjemce.mention}",
                color=0x2ecc71,
                timestamp=datetime.utcnow()
            )
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ **Nastala chyba při transakci!**")
    
    @commands.hybrid_command(name='vložit', aliases=['deposit'])
    async def deposit(self, ctx, částka):
        """Vloží peníze do banky"""
        await self._ensure_user_exists(ctx.author.id, ctx.guild.id)
        user_data = await self.bot.db.get_user_economy(ctx.author.id, ctx.guild.id)
        
        if částka.lower() == 'vše' or částka.lower() == 'all':
            částka = user_data['balance']
        else:
            try:
                částka = int(částka)
            except ValueError:
                return await ctx.send("❌ **Neplatná částka!**")
        
        if částka <= 0:
            return await ctx.send("❌ **Částka musí být větší než 0!**")
        
        if user_data['balance'] < částka:
            return await ctx.send(f"❌ **Nemáš dostatek {self.currency_name}! Máš pouze {user_data['balance']:,}.**")
        
        # Transakce
        try:
            cursor = self.bot.db._connection.cursor()
            cursor.execute(
                "UPDATE users SET balance = balance - ?, bank = bank + ? WHERE user_id = ? AND guild_id = ?",
                (částka, částka, ctx.author.id, ctx.guild.id)
            )
            self.bot.db._connection.commit()
            
            embed = discord.Embed(
                title="🏦 Vklad úspěšný",
                description=f"Vložil jsi **{částka:,}** {self.currency_name} do banky",
                color=0x2ecc71,
                timestamp=datetime.utcnow()
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Chyba při vkladu: {e}")
            await ctx.send("❌ **Nastala chyba při vkladu!**")
    
    @commands.hybrid_command(name='vybrat', aliases=['withdraw'])
    async def withdraw(self, ctx, částka):
        """Vybere peníze z banky"""
        await self._ensure_user_exists(ctx.author.id, ctx.guild.id)
        user_data = await self.bot.db.get_user_economy(ctx.author.id, ctx.guild.id)
        
        if částka.lower() == 'vše' or částka.lower() == 'all':
            částka = user_data['bank']
        else:
            try:
                částka = int(částka)
            except ValueError:
                return await ctx.send("❌ **Neplatná částka!**")
        
        if částka <= 0:
            return await ctx.send("❌ **Částka musí být větší než 0!**")
        
        if user_data['bank'] < částka:
            return await ctx.send(f"❌ **Nemáš dostatek {self.currency_name} v bance! Máš pouze {user_data['bank']:,}.**")
        
        # Transakce
        try:
            cursor = self.bot.db._connection.cursor()
            cursor.execute(
                "UPDATE users SET balance = balance + ?, bank = bank - ? WHERE user_id = ? AND guild_id = ?",
                (částka, částka, ctx.author.id, ctx.guild.id)
            )
            self.bot.db._connection.commit()
            
            embed = discord.Embed(
                title="🏦 Výběr úspěšný",
                description=f"Vybral jsi **{částka:,}** {self.currency_name} z banky",
                color=0x2ecc71,
                timestamp=datetime.utcnow()
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Chyba při výběru: {e}")
            await ctx.send("❌ **Nastala chyba při výběru!**")
    
    @commands.hybrid_command(name='žebříček', aliases=['leaderboard', 'top'])
    async def leaderboard(self, ctx, typ: str = 'peníze'):
        """Zobrazí žebříček nejbohatších uživatelů"""
        try:
            if typ.lower() in ['peníze', 'money', 'balance']:
                cursor = self.bot.db._connection.cursor()
                cursor.execute(
                    """SELECT user_id, balance + bank as total 
                       FROM users 
                       WHERE guild_id = ? 
                       ORDER BY total DESC 
                       LIMIT 10""",
                    (ctx.guild.id,)
                )
                results = cursor.fetchall()
                title = f"💰 Nejbohatší uživatelé"
                
            elif typ.lower() in ['level', 'xp']:
                cursor = self.bot.db._connection.cursor()
                cursor.execute(
                    """SELECT user_id, level, xp 
                       FROM users 
                       WHERE guild_id = ? 
                       ORDER BY level DESC, xp DESC 
                       LIMIT 10""",
                    (ctx.guild.id,)
                )
                results = cursor.fetchall()
                title = f"📊 Nejvyšší levely"
            else:
                return await ctx.send("❌ **Neplatný typ žebříčku! Použij: peníze/level**")
            
            if not results:
                return await ctx.send("❌ **Žebříček je prázdný!**")
            
            embed = discord.Embed(
                title=title,
                color=0xf1c40f,
                timestamp=datetime.utcnow()
            )
            
            description = ""
            for i, result in enumerate(results, 1):
                try:
                    user = ctx.guild.get_member(result[0])
                    if not user:
                        continue
                    
                    if typ.lower() in ['peníze', 'money', 'balance']:
                        medals = ["🥇", "🥈", "🥉"]
                        medal = medals[i-1] if i <= 3 else f"`{i}.`"
                        description += f"{medal} {user.display_name}: **{result[1]:,}** {self.currency_name}\n"
                    else:
                        medals = ["🥇", "🥈", "🥉"]
                        medal = medals[i-1] if i <= 3 else f"`{i}.`"
                        description += f"{medal} {user.display_name}: Level **{result[1]}** ({result[2]:,} XP)\n"
                        
                except Exception:
                    continue
            
            embed.description = description or "Žádní uživatelé nenalezeni"
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Chyba při zobrazování žebříčku: {e}")
            await ctx.send("❌ **Nastala chyba při načítání žebříčku!**")
    
    # Error handlery pro cooldowny
    @daily_reward.error
    async def daily_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            hours = int(error.retry_after // 3600)
            minutes = int((error.retry_after % 3600) // 60)
            await ctx.send(f"⏰ **Denní odměnu už jsi si dnes vybral!** Zkus to za {hours}h {minutes}m.")
    
    @work.error
    async def work_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            minutes = int(error.retry_after // 60)
            seconds = int(error.retry_after % 60)
            await ctx.send(f"💼 **Právě jsi pracoval!** Zkus to za {minutes}m {seconds}s.")

async def setup(bot):
    await bot.add_cog(Economy(bot))
