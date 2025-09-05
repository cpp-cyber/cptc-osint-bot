import interactions
from interactions import slash_command, SlashContext, listen, Intents, SlashCommandChoice, slash_option, OptionType
import yaml


scope = "<DISCORD GUILD ID>"
bot = interactions.Client(token="<DISCORD BOT TOKEN>", intents=Intents.DEFAULT)


def write_to_yaml(data):
    with open('queries.yml', 'r') as file:
        queries = yaml.safe_load(file)

    search_engine_data = {
        "google": {
            "search_string": data["search_string"],
            "cx": data.get("cx", "web")
        },
        "bing": {
            "search_string": data["search_string"]
        }
    }

    search_engine = data["search_engine"]

    for engine in ("google", "bing"):
        if search_engine in ("all", engine):
            queries[engine].append(search_engine_data[engine])

    with open('queries.yml', 'w') as file:
        yaml.safe_dump(queries, file)


@listen()
async def on_ready():
    print("Ready")


@slash_command(name="list_queries", description="List of queries that are currently being monitored.")
async def list_queries(ctx: SlashContext):
    with open('queries.yml', 'r') as file:
        queries = yaml.safe_load(file)

    json_queries = yaml.dump(queries)
    await ctx.respond(f"```{json_queries}```", ephemeral=True)


@slash_command(name="search", description="Add a search query you want to be monitored.")
@slash_option(
    name="query",
    description="The search query you want monitored.",
    required=True,
    opt_type=OptionType.STRING,
)
@slash_option(
    name="search_engine",
    description="Search engine",
    required=True,
    opt_type=OptionType.STRING,
    choices=[
        SlashCommandChoice(name="All", value="all"),
        SlashCommandChoice(name="Google", value="google"),
        SlashCommandChoice(name="Bing", value="bing"),
    ]
)
@slash_option(
    name="cx",
    description="ONLY IF 'GOOGLE' OR 'ALL' IS USED: Custom search engine",
    required=False,
    opt_type=OptionType.STRING,
    choices=[
        SlashCommandChoice(name="Web", value="web"),
        SlashCommandChoice(name="Social Medias", value="social"),
        SlashCommandChoice(name="Facebook", value="facebook"),
        SlashCommandChoice(name="Linkedin", value="linkedin"),
        SlashCommandChoice(name="StackOverflow", value="stackoverflow"),
        SlashCommandChoice(name="GitHub", value="github")
    ]
)
async def search(ctx: SlashContext, query: str, search_engine: str, cx: str | None = None):
    if search_engine == "all" or search_engine == "google":
        data = {
            "search_string": query,
            "search_engine": search_engine,
            "cx": cx or "web"
        }
    else:
        data = {
            "search_string": query,
            "search_engine": search_engine,
        }

    write_to_yaml(data)
    await ctx.respond(f"Searching for '{query}' using {search_engine}.", ephemeral=True)


if __name__ == '__main__':
    bot.start()
