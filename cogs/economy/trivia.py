from __future__ import annotations

import html
import random

import aiohttp
import discord
from discord.ext import commands

from .base_cog import BaseEconomyCog


class TriviaException(Exception):
    pass


# Suboptimal implementation, ideally I'd cache multiple questions at a time
# but this is good enough for our purposes
class TriviaQuestion:
    """Represents a trivia question"""

    LETTERS = ['A', 'B', 'C', 'D']

    def __init__(self, category, question, correct_answer, incorrect_answers, difficulty):
        self.category = html.unescape(category)
        self.question = html.unescape(question)
        self.correct_answer = html.unescape(correct_answer)
        self.incorrect_answers = [html.unescape(x) for x in incorrect_answers]
        self.difficulty = html.unescape(difficulty)
        self.correct_answer_letter = random.choice(TriviaQuestion.LETTERS)

    @classmethod
    async def get_trivia(cls, get_url: str = "https://opentdb.com/api.php?amount=1&type=multiple") -> TriviaQuestion:
        try:
            async with aiohttp.ClientSession() as cs:
                async with cs.get(get_url) as resp:
                    question_dict = await resp.json()
                    questions = question_dict.get('results')
                    if questions:
                        result = questions[0]  # first question
                        return cls(
                            result['category'], result['question'], result['correct_answer'], result['incorrect_answers'], result['difficulty']
                        )
                    else:
                        raise TriviaException("Invalid response received from API.")
        except aiohttp.ClientConnectionError:
            raise TriviaException("Could not connect to OpenTDB server.")

    @property
    def embed(self) -> discord.Embed:
        embed = discord.Embed(title=f'Category: {self.category} ({self.difficulty})', description=self.question, color=discord.Color.blue())

        incorrect_answers = self.incorrect_answers.copy()
        random.shuffle(incorrect_answers)

        for letter in TriviaQuestion.LETTERS:
            if letter == self.correct_answer_letter:
                embed.add_field(name=letter, value=self.correct_answer, inline=False)
            else:
                embed.add_field(name=letter, value=incorrect_answers.pop(), inline=False)
        return embed


class TriviaView(discord.ui.View):
    message: discord.Message  # set when view sent.

    def __init__(self, owner: discord.User | discord.Member, question: TriviaQuestion):
        super().__init__(timeout=30.0)
        self.owner = owner
        self.question = question

    async def on_timeout(self) -> None:
        await self.message.edit(content="Did not answer in time", view=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user == self.owner:
            return True
        await interaction.response.send_message("You cannot answer this question.", ephemeral=True)
        return False

    async def handle_click(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        pick = button.label
        if pick == self.question.correct_answer_letter:
            cog = interaction.client.get_cog("Economy")  # type: ignore
            wallet = await cog.get_wallet(interaction.user)
            amount_won = random.randint(6, 20)
            await wallet.add(amount_won)

            win_text = f"That's correct. `{pick}` was the correct answer.\n\nYou won {amount_won}€"
            await interaction.response.edit_message(content=win_text, view=None)
        else:
            lose_text = f"Incorrect, `{pick}` not the correct answer.\n\nThe correct answer was `{self.question.correct_answer_letter}`."
            await interaction.response.edit_message(content=lose_text, view=None)
        self.stop()  # prevent timeout logic

    @discord.ui.button(label="A", style=discord.ButtonStyle.blurple)
    async def a_btn(self, interaction: discord.Interaction, btn: discord.ui.Button) -> None:
        await self.handle_click(interaction, btn)

    @discord.ui.button(label="B", style=discord.ButtonStyle.blurple)
    async def b_btn(self, interaction: discord.Interaction, btn: discord.ui.Button) -> None:
        await self.handle_click(interaction, btn)

    @discord.ui.button(label="C", style=discord.ButtonStyle.blurple)
    async def c_btn(self, interaction: discord.Interaction, btn: discord.ui.Button) -> None:
        await self.handle_click(interaction, btn)

    @discord.ui.button(label="D", style=discord.ButtonStyle.blurple)
    async def d_btn(self, interaction: discord.Interaction, btn: discord.ui.Button) -> None:
        await self.handle_click(interaction, btn)


class Trivia(BaseEconomyCog):
    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 30.0, commands.BucketType.user)  # 1 time per 30 seconds per user
    async def trivia(self, ctx: commands.Context):
        triviaquestion = await TriviaQuestion.get_trivia()
        triviaview = TriviaView(ctx.author, triviaquestion)

        triviaview.message = await ctx.send(embed=triviaquestion.embed, view=triviaview)
