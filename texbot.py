import discord
from discord.ext import commands

import os
import random
import re
import requests
import signal
import traceback
import urllib.parse
import warnings
warnings.filterwarnings("ignore")

from io import BytesIO
from PIL import Image
from sympy.solvers import solve as compute
from sympy import latex, symbols, sympify, simplify

import dotenv
dotenv.load_dotenv()

bot = commands.Bot(command_prefix="=", case_insensitive = True, intents = discord.Intents.all())
bot.remove_command("help")

def handler(signum, frame):
    raise Exception("overtime")

@bot.event
async def on_ready():
  await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="=help"))
  print(f"Ready: {bot.user}")

@bot.event
async def on_message(message):
  count = message.content.count("$$")
  if message.author.id != bot.user.id and count >= 2:
      latexes = re.findall(r'\$\$(.*?)\$\$', message.content)
      newthing = []
      remaining = message.content.split("$$")
      for i in range(len(remaining)):
          if i % 2 == 0:
            newthing.append(remaining[i])
      for latex, msg in zip(latexes[:5], newthing):
          await tex(message.channel, latex, msg = msg)

      if len(latexes) > 5:
        await message.channel.send("$$".join(message.content.split("$$")[10:]))
      elif len("$$".join(newthing[len(latexes[:5]):])):
        await message.channel.send("$$".join(newthing[len(latexes[:5]):]))
      
  await bot.process_commands(message)

@bot.command()
async def help(ctx, *args):
  await ctx.reply("Source: https://github.com/jbrightuniverse/texbot\n\n**__List of Commands__**\n\n`=tex <expression>`: render LaTeX.\n\ne.g. `=tex \\frac{1}{2}` will output `1/2` in LaTeX.\n\n`=solve <expression>`: evaluates an expression with SymPy.\n\ne.g. `=solve 5*x + 6*x` will output `11x`.\ne.g. `=solve 5*x, x` will output `0`.\nProviding a variable to solve for after a comma will solve the expression set equal to zero.\n\nThe bot also supports **inline latex**. Surround text with `$$` to use it.\n\ne.g. type `this is $$\\frac{1}{2}$$ in LaTeX`.", mention_author = False)

@bot.command()
async def solve(ctx):
    signal.signal(signal.SIGALRM, handler)
    keys = ctx.message.content[7:].replace("`", "").split(",")
    async with ctx.typing():
        signal.alarm(10)
        try:
            equation = simplify(sympify(keys[0]))
            if len(keys) == 2:
                equation = compute(equation, symbols(keys[1].lstrip().rstrip()))
        except Exception as error:
            signal.alarm(0)
            msg = "An error has occurred!\n```python" + "".join(traceback.format_exception(type(error), error, error.__traceback__, 999)) + "```"
            await ctx.reply(msg[:2000], mention_author = False)
        else:
            signal.alarm(0)
            await tex(ctx, str(latex(equation)), "Result:", reply = True)


@bot.command()
async def tex(ctx):
    latex = ctx.message.content[5:]
    await tex(ctx, latex, reply = True)

@bot.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.CommandNotFound):
    return
  elif isinstance(error, commands.MissingRequiredArgument):
    await ctx.reply(f"**{ctx.author}**, please specify some text to be used with this command.", mention_author = False)
  elif isinstance(error, commands.CommandOnCooldown):
    await ctx.reply(f"**{ctx.author}**, this command is on cooldown. Try again in {error.retry_after} seconds.", mention_author = False)
  else:
    msg = "An error has occurred!\n```python" + "".join(traceback.format_exception(type(error), error, error.__traceback__, 999)) + "```"
    await ctx.reply(msg[:2000], mention_author = False)
    if len(msg) > 2000:
      try:
        print(msg)
      except:
        pass

# from cs213bot, from cs221bot, from :b:ot
def _urlencode(*args, **kwargs):
  kwargs.update(quote_via=urllib.parse.quote)
  return urllib.parse.urlencode(*args, **kwargs)

requests.models.urlencode = _urlencode

async def tex(ctx, formula, msg = None, reply = False):
  # from cs213bot, from cs221bot, from :b:ot
  formula = formula.strip("`")
  body = {
      "formula" : formula,
      "fsize"   : r"30px",
      "fcolor"  : r"FFFFFF",
      "mode"    : r"0",
      "out"     : r"1",
      "remhost" : r"quicklatex.com",
      "preamble": r"\usepackage{amsmath}\usepackage{amsfonts}\usepackage{amssymb}",
      "rnd"     : str(random.random() * 100)
  }

  try:
    img = requests.post("https://www.quicklatex.com/latex3.f", data=body, timeout=10)
  except (requests.ConnectionError, requests.HTTPError, requests.TooManyRedirects, requests.Timeout):
    if reply:
        return await ctx.reply("ERROR IN LATEX RENDER: Render timed out.", mention_author = False)
    return await ctx.send("ERROR IN LATEX RENDER: Render timed out.")

  if img.status_code != 200:
    if reply:
        return await ctx.reply("ERROR IN LATEX RENDER: Something went wrong. Maybe check your syntax?", mention_author = False)
    return await ctx.send("ERROR IN LATEX RENDER: Something went wrong. Maybe check your syntax?")

  if img.text.startswith("0"):
    raw = BytesIO(requests.get(img.text.split()[1]).content)
    img = Image.open(raw).convert("RGBA")
    base = Image.new("RGBA", img.size, (54, 57, 63, 255))
    base.paste(img, (0,0), img)
    filex = BytesIO()
    base.save(filex, "PNG")
    filex.seek(0)
    if reply:
        return await ctx.reply(msg, file=discord.File(filex, "latex.png"), mention_author = False)
    return await ctx.send(msg, file=discord.File(filex, "latex.png"))
  else:
    if reply:
        return await ctx.reply("ERROR IN LATEX RENDER:\n" + " ".join(img.text.split()[5:]), mention_author = False)
    return await ctx.send("ERROR IN LATEX RENDER:\n" + " ".join(img.text.split()[5:]))

bot.run(os.getenv("TOKEN"), bot=True, reconnect=True)
