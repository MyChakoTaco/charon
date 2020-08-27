import roles
import discord
from datetime import datetime

# 86400 seconds in 24 hours
# 43200 seconds in 12 hours
# 3600 seconds in an hour
ACTIVE_DURATION_SECONDS = 86400
DEFAULT_PARTY_SIZE = 4
DEFAULT_JOIN_EMOJI = '👍'
DEFAULT_LEAVE_EMOJI = '❌'


class party:
    def __init__(self, message, leader, name, size=None):
        self.__close = False
        self.message = message
        # self.__leader = leader
        self.__creationDateTime = datetime.now()
        self.__partyList = [leader.name]
        self.__waitlist = []

        preset = self.__getPreset(name)

        if (preset is not None):
            self.name = preset.name
            self.size = preset.size if size is None else size
            self.imageURL = preset.imageURL
            self.joinEmoji = preset.emoji
        else:
            self.name = name
            self.size = DEFAULT_PARTY_SIZE if size is None else size
            self.imageURL = None
            self.joinEmoji = DEFAULT_JOIN_EMOJI

        self.leaveEmoji = DEFAULT_LEAVE_EMOJI

    @staticmethod
    def __getPreset(name):
        for preset in roles.ROLES_LIST:
            if name.casefold() == preset.name.casefold():
                return preset
        return None

    def addMember(self, name):
        if name in self.__partyList or name in self.__waitlist:
            return

        if len(self.__partyList) < self.size:
            self.__partyList.append(name)
        else:
            self.__waitlist.append(name)

    def removeMember(self, name):
        if name in self.__partyList:
            self.__partyList.remove(name)

        if name in self.__waitlist:
            self.__waitlist.remove(name)

        if len(self.__partyList) < self.size and len(self.__waitlist) > 0:
            self.__partyList.append(self.__waitlist.pop(0))

        if len(self.__partyList) == 0:
            self.__close = True

    def hasMember(self, name):
        return name in self.__partyList or name in self.__waitlist

    def isMatchJoinEmoji(self, reaction):
        return (self.message.id == reaction.message.id
                and self.joinEmoji == reaction.emoji)

    def isMatchLeaveEmoji(self, reaction):
        return (self.message.id == reaction.message.id
                and self.leaveEmoji == reaction.emoji)

    def isInactive(self):
        return ((datetime.now() - self.__creationDateTime).total_seconds()
                > ACTIVE_DURATION_SECONDS)

    def isClosed(self):
        return self.__close

    def getEmbed(self):
        embed = discord.Embed()

        if self.__close:
            embed.title = f'{self.name} (Closed)'
            embed.description = ('This party is closed.')
            # embed.description = ('This party was closed by '
            #                      f'{self.__leader.name}.')
        elif self.isInactive():
            embed.title = f'{self.name} (Inactive)'
            embed.description = ('This party is inactive because it is old.'
                                 '\nPlease create a new party.')
        else:
            embed.title = f'{self.name}'
            embed.description = ('Add yourself to the party by using reaction '
                                 f'\"{self.joinEmoji}\"\n')
            embed.add_field(
                name=f'Party Members ({len(self.__partyList)}/{self.size})',
                value="\n".join(self.__partyList) if len(
                    self.__partyList) > 0 else '👻...',
                inline=True)
            if (len(self.__waitlist) > 0):
                embed.add_field(
                    name='Waitlist',
                    value="\n".join(self.__waitlist),
                    inline=True)
            if self.imageURL is not None:
                embed.set_thumbnail(url=self.imageURL)

        return embed
