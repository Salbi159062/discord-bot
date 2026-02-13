import discord
from discord.ext import commands
from logic import DB_Manager
from config import DATABASE, TOKEN

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)
manager = DB_Manager(DATABASE)

# Make sure database tables exist
manager.create_tables()


@bot.event
async def on_ready():
    print(f'Bot hazır! {bot.user} olarak giriş yapıldı.')


# ---------- START COMMAND ----------

@bot.command(name='start')
async def start_command(ctx):
    await ctx.send(
        "Merhaba! Ben bir Destek (Ticket) botuyum 🎫\n"
        "Sorularınızı ve sorunlarınızı ticket açarak iletebilirsiniz!"
    )
    await info(ctx)


# ---------- INFO COMMAND ----------

@bot.command(name='info')
async def info(ctx):
    await ctx.send("""
Kullanabileceğiniz komutlar:

/create_ticket  - Yeni destek talebi oluştur
/my_tickets     - Açık ticketlarını listele
/close_ticket   - Ticketı kapat
/delete_ticket  - Ticketı tamamen sil

Her ticket sizin adınıza kaydedilir ve kolayca yönetilir!
""")


# ---------- CREATE TICKET ----------

@bot.command(name='create_ticket')
async def create_ticket(ctx):
    await ctx.send("Lütfen ticket başlığını yazın:")

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    title = await bot.wait_for('message', check=check)

    await ctx.send("Lütfen sorununuzu veya talebinizi detaylı açıklayın:")

    description = await bot.wait_for('message', check=check)

    # Create private channel name
    channel_name = f"ticket-{ctx.author.name}"

    # Create channel
    guild = ctx.guild
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    channel = await guild.create_text_channel(channel_name, overwrites=overwrites)

    # Save to database
    manager.create_ticket(
        ctx.author.id,
        channel.id,
        title.content,
        description.content
    )

    await ctx.send(f"Ticket başarıyla oluşturuldu! 👉 {channel.mention}")
    await channel.send(
        f"🎫 **Yeni Ticket Açıldı**\n"
        f"👤 Sahibi: {ctx.author.mention}\n"
        f"📝 Başlık: {title.content}\n\n"
        f"{description.content}"
    )


# ---------- LIST USER TICKETS ----------

@bot.command(name='my_tickets')
async def my_tickets(ctx):
    tickets = manager.get_user_tickets(ctx.author.id)

    if tickets:
        text = "Açık ticketlarınız:\n\n"
        for channel_id, title in tickets:
            channel = bot.get_channel(channel_id)
            if channel:
                text += f"🎫 {title} → {channel.mention}\n"

        await ctx.send(text)
    else:
        await ctx.send("Şu anda açık ticketınız bulunmuyor!")


# ---------- CLOSE TICKET ----------

@bot.command(name='close_ticket')
async def close_ticket(ctx):
    channel_id = ctx.channel.id

    ticket = manager.get_ticket_by_channel(channel_id)

    if not ticket:
        await ctx.send("Bu kanal bir ticket kanalı değil!")
        return

    manager.close_ticket(channel_id)

    await ctx.send("Ticket kapatıldı ✅\nBu kanal artık arşivlenebilir.")


# ---------- DELETE TICKET ----------

@bot.command(name='delete_ticket')
async def delete_ticket(ctx):
    channel_id = ctx.channel.id

    ticket = manager.get_ticket_by_channel(channel_id)

    if not ticket:
        await ctx.send("Bu kanal bir ticket kanalı değil!")
        return

    manager.delete_ticket(channel_id)

    await ctx.send("Ticket siliniyor... 🗑️")

    await ctx.channel.delete()


# ---------- RUN BOT ----------

bot.run(TOKEN)
