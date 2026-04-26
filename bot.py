import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os

# ─────────────────────────────────────────────
#  Konfiguracja
# ─────────────────────────────────────────────
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True          # wymagane do pobierania członków serwera
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ─────────────────────────────────────────────
#  Zdarzenie: bot gotowy
# ─────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅  Zalogowano jako {bot.user} (ID: {bot.user.id})")
    try:
        guild = discord.Object(id=1477414207766003814)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"🔄  Zsynchronizowano {len(synced)} komend slash.")
    except Exception as e:
        print(f"❌  Błąd synchronizacji: {e}")


# ─────────────────────────────────────────────
#  Komenda slash: /dm_rola
# ─────────────────────────────────────────────
@bot.tree.command(
    name="dm",
    description="Wyślij wiadomość prywatną do wszystkich użytkowników z wybraną rolą."
)
@app_commands.describe(
    rola="Rola, do której członków zostanie wysłana wiadomość",
    wiadomosc="Treść wiadomości prywatnej"
)
@app_commands.checks.has_permissions(administrator=True)   # tylko administratorzy
async def dm_rola(
    interaction: discord.Interaction,
    rola: discord.Role,
    wiadomosc: str
):
    # Natychmiastowe potwierdzenie (Discord wymaga odpowiedzi w ciągu 3 s)
    await interaction.response.defer(ephemeral=True)

    members = [m for m in rola.members if not m.bot]

    if not members:
        await interaction.followup.send(
            f"⚠️  Rola **{rola.name}** nie ma żadnych (nie-botowych) członków.",
            ephemeral=True
        )
        return

    sukces, blad = 0, 0
    blad_lista = []

    # Embed wysyłany użytkownikom
    embed = discord.Embed(
        title="⚜️ Wiadomość z partii Centrum Narodu Polskiego ⚜️",
        description=wiadomosc,
        color=rola.color if rola.color.value else discord.Color.blurple()
    )
    embed.set_footer(text=f"Serwer: {interaction.guild.name}")
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)

    for member in members:
        try:
            await member.send(embed=embed)
            sukces += 1
            await asyncio.sleep(0.5)   # ograniczenie rate-limit
        except discord.Forbidden:
            blad += 1
            blad_lista.append(f"`{member.display_name}` — brak zgody na DM")
        except discord.HTTPException as e:
            blad += 1
            blad_lista.append(f"`{member.display_name}` — błąd HTTP: {e.status}")

    # Raport dla administratora
    raport = discord.Embed(
        title="📊  Raport wysyłania DM",
        color=discord.Color.green() if blad == 0 else discord.Color.orange()
    )
    raport.add_field(name="Rola", value=rola.mention, inline=True)
    raport.add_field(name="✅ Wysłano", value=str(sukces), inline=True)
    raport.add_field(name="❌ Błędów", value=str(blad), inline=True)

    if blad_lista:
        raport.add_field(
            name="Nie udało się wysłać do:",
            value="\n".join(blad_lista[:10]) + ("\n…i więcej" if len(blad_lista) > 10 else ""),
            inline=False
        )

    await interaction.followup.send(embed=raport, ephemeral=True)


# ─────────────────────────────────────────────
#  Obsługa błędów komendy
# ─────────────────────────────────────────────
@dm_rola.error
async def dm_rola_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "🚫  Nie masz uprawnień administratora, aby używać tej komendy.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"❌  Wystąpił błąd: `{error}`",
            ephemeral=True
        )


# ─────────────────────────────────────────────
#  Uruchomienie bota
# ─────────────────────────────────────────────
if __name__ == "__main__":
    bot.run(TOKEN)
