import discord
from discord.ext import commands
from discord.ext.commands import command,Cog,Greedy
from discord.ext.commands import Context

#NOTE: MEMBER AND MEMBER.VOICE WILL BE COMBINED AS ONE






class Member(commands.Cog):
    """
    A Cog with commands relating to members, like adding/removing roles, ban/unban members, etc...
    """
    def __init__(self, bot):
        self.bot = bot


    @commands.hybrid_command(name='member-events')
    async def member_events(self,ctx:Context):
        """
        command group responsible for dealing with `member_events`
        """


    @commands.command(hidden=True,enabled=True,aliases=['user.info'])
    async def user_info(self,ctx,member:discord.Member=None):
        """
        Get information about a server member
        member(required): The mentioned member or name of the member to get info from
        {command_prefix}{command_name} @Member Name
        """
        if member is None:
            member = ctx.author
        emb = discord.Embed(title=f'{member.display_name} | {member.id}',color=member.color)
        emb.set_thumbnail(url=member.display_avatar.url)
        emb.add_field(name='User Since',value=f"{member.created_at.strftime('%B')} {member.created_at.day}, {member.created_at.year}")
        emb.add_field(name='Member Since',value=f"{member.joined_at.strftime('%B')} {member.joined_at.day}, {member.joined_at.year}")
        emb.add_field(name='Highest Role',value=member.top_role)
        if member.premium_since is not None:
            emb.add_field(name='Booster Since',value=f"{member.premium_since.strftime('%B')} {member.premium_since.day}, {member.premium_since.year}")
        emb.add_field(name="Roles",value=",".join([role.mention for role in member.roles]))
        emb.set_footer(text=f"Requested by: {ctx.author.display_name}",icon_url=ctx.author.display_avatar.url)
        return await ctx.send(embed=emb)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """
        Kick the mentioned member from the server.
        member(required): The member to kick from the server.
        reason(optional): The reason for kicking the member.
        {command_prefix}{command_name} @user_name reason
        """
        await member.send(f"kicked {member.name}\n reason: {reason}")
        await member.kick(reason=reason)
        if reason is None:
            return await ctx.send(f"{member.name} has been kicked from {ctx.guild.name}")

        return await ctx.send(f"{member.name} has been kicked from {ctx.guild.name} \n Reason: {reason}")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """
        ban a user from the server.
        member(required): The member to ban.
        reason (optional): The reason for banning the member.
        {command_prefix}{command_name} @user_name ban_reason
        """
        await member.send(f"banned {member.name}\nreason: {reason}")
        await member.ban(reason=reason)
        if reason is None:
            return await ctx.send(f"{member.name} has been kicked from {ctx.guild.name}")
        return await ctx.send(f"{member.name} has been kicked from {ctx.guild.name}\n Reason: {reason}")


    @commands.has_permissions(manage_channels=True)
    @command(name='move-member',enabled=False,hidden=True)
    async def move_member(self,members:Greedy[discord.Member],channel:discord.VoiceChannel):
        """ 
        Move a mentioned user(s) to a different voice channel
        members(required): The members to move to a different voice channel.
        {command_prefix}{command_name} @User1 @User2... Voice Channel Name
        """

    @commands.command(hidden=True)
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user:discord.User,*,reason=None):
        """
        unban a user from the server.
        user(required): The ID of the user to unban.
        {command_prefix}{command_name} username
        """
        if user is None:
            return await ctx.send(f"Unable to find user {user}")
        
        await ctx.guild.unban(user)
        if reason is None:
            return await ctx.send(f"unbanned {user.name}")

        return await ctx.send(f"unbanned {user.name}\n Reason: {reason}")

    @commands.has_permissions(ban_members=True)
    @commands.command(name='ban.list')
    async def ban_list(self,ctx):
        """
        View list of users that are banned from the server
        {command_prefix}{command_prefix}
        """
        bannedList = [user async for user in ctx.guild.bans()]
        emb = discord.Embed(title='Banned List')
        for user in bannedList:
            emb.add_field(name=user.user,value=user.reason,inline=False)
        return await ctx.send(embed=emb)


    @commands.command(name='give-role')
    @commands.has_permissions(manage_roles=True)
    async def give_role(self, ctx, member: discord.Member, role: discord.Role):        
        """
        Give a role to a member
        {command_prefix}{command_name} @User @Role
        """
        print(role)
        await member.add_roles(role)
        await ctx.send(f"Role **{role.name}** is given to **{member.name}**")



    @commands.command(name='remove-role')
    @commands.has_permissions(manage_roles=True)
    async def remove_role(self, ctx, member: discord.Member, *, role: discord.Role):
        """
        Remove a role from a member
        {command_prefix}{command_name} @User @Role
        """
        await member.remove_roles(role)
        return await ctx.send(f"Role **{role.name}** is removed from **{member.name}**")


async def setup(bot):
    await bot.add_cog(Member(bot))