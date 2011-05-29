#
# PowerAdmin Plugin for BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2008 Mark Weirath (xlr8or@xlr8or.com)
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
#
# CHANGELOG :
#
# 6/4/2010 - 0.1.2 -SpacepiG
# added:
# paset, paget, pamap, macyclemap, pamaprestart, pamapreload
# payell, payellteam, payellenemy, payellplayer, paversion, pasetnextmap, paident
#
# 8/4/2010 - 0.1.3 -SpacepiG
# added:
# pakill, pachangeteam
# Removed:
# pamap, pacyclemap - exist in bfbc2 parser/admin
# Modified:
# payell, payellteam, payellenemy, payellplayer
#
# 9/4/2010 - 0.1.4 -SpacepiG
# Modified:
# payell
#
# 11/4/2010 - 0.2 - Bakes
# Rewrote many of the functions to be more efficient.
#
# 12/4/2010 - 0.2.1 - Bakes
# Added:
# payellsquad
#
# 12/4/2010 - 0.2.2 - Bakes
# Modified:
# paserverinfo
# paset
# paident
#
# 19/04/2010 - 0.3 - Courgette
# * add !pamatch command that allow teams to ready up and does a count down
# * teambalancer now move players to the other team instead of just warning them.
#   It is not scheduled yet but can be run with the !pateams command for instant
#   balancing. If this works well, we'll schedule it
# * fixes to !payellteam, !payellenemies, !payellplayer, !paset, !paget, !pasetnextmap
#   !paident, !pakill, !pachangeteam, !paspectate
# 19/04/2010 - 0.3.1 - Courgette
# * merge with Bakes
# 25/04/2010 - 0.4 - Courgette
# * match mode now requires all players to type !ready
# * make sure to reset the ready state for all players when !match on 
# * add tests for match mode
# * add !parush !paconquest !pasqdm !pasqrush commands to change mod
# 26/04/2010 - 0.5 - Courgette
# * move cmd_ready to the MatchManager class
# * a player cannot unready once the match countdown started
# 15/08/2010 - 0.5.1 - Nye Liu
# * client.teamId is an int
# 25/09/2010 - 0.5.2 - xlr8or
# * handle changes in parser: bfbc2 to frostbite
# 22/05/2011 - 0.6 - Courgette
# * add !swap command
# * add scrambler
# * now requires B3 v1.7
# 22/05/2011 - 0.7  - Courgette
# * update teambalancer
# 24/05/2011 - 0.7.1  - Courgette
# * changing game mode will end the current round so that the new mode is loaded right away
# * changing game mode to the currently running mode will be cancelled
# 24/05/2011 - 0.7.2 - Courgette
# * new attempt at fixing commands that change game mode
# 24/05/2011 - 0.10.0 - Courgette
# * revert commands that change game mode (a fix is now in the BFBC2 parser)
# * add commands !runnextround, !reserveslot and !unreserveslot 
# 29/05/2011 - 0.11.0 - Courgette
# * command !teams also works when teambalancer is disabled
#
__version__ = '0.11.0'
__author__  = 'Courgette, SpacepiG, Bakes'

import b3, time, re, random

import b3.plugin
from b3.parsers.frostbite.connection import FrostbiteCommandFailedError
from b3.parsers.frostbite.util import PlayerInfoBlock


from distutils import version
b3Version = version.LooseVersion(b3.__version__)
if b3Version < version.LooseVersion("1.7.0"):
    raise SystemExit("the poweradminbfbc2 plugin requires B3 v1.7+. Yours is %s" % b3Version)
        
        
class Scrambler:
    _plugin = None
    _getClients_method = None
    _last_round_scores = PlayerInfoBlock([0,0])
    
    def __init__(self):
        self._getClients_method = self._getClients_randomly

    def scrambleTeams(self):
        clients = self._getClients_method()
        if len(clients)==0:
            return
        elif len(clients)<3:
            self.debug("Too few players to scramble")
        else:
            self._scrambleTeams(clients)

    def setStrategy(self, strategy):
        """Set the scrambling strategy"""
        if strategy.lower() == 'random':
            self._getClients_method = self._getClients_randomly
        elif strategy.lower() == 'score':
            self._getClients_method = self._getClients_by_scores
        else: 
            raise ValueError

    def onRoundOverTeamScores(self, playerInfoBlock):
        self._last_round_scores = playerInfoBlock

    def _scrambleTeams(self, listOfPlayers):
        team = 0
        while len(listOfPlayers)>0:
            self._plugin._movePlayer(listOfPlayers.pop(), team + 1)
            team = (team + 1)%2

    def _getClients_randomly(self):
        clients = self._plugin.console.clients.getList()
        random.shuffle(clients)
        return clients

    def _getClients_by_scores(self):
        allClients = self._plugin.console.clients.getList()
        self.debug('all clients : %r' % [x.cid for x in allClients])
        sumofscores = reduce(lambda x, y: x+y, [int(data['score']) for data in self._last_round_scores], 0)
        self.debug('sum of scores is %s' % sumofscores)
        if sumofscores == 0:
            self.debug('no score to sort on, using ramdom strategy instead')
            random.shuffle(allClients)
            return allClients
        else:
            sortedScores = sorted(self._last_round_scores, key=lambda x:x['score'])
            self.debug('sorted score : %r' % sortedScores)
            sortedClients = []
            for cid in [x['name'] for x in sortedScores]:
                # find client object for each player score
                clients = [c for c in allClients if c.cid == cid]
                if clients and len(clients)>0:
                    allClients.remove(clients[0])
                    sortedClients.append(clients[0])
            self.debug('sorted clients A : %r' % map(lambda x:x.cid, sortedClients))
            random.shuffle(allClients)
            for client in allClients:
                # add remaining clients (they had no score ?)
                sortedClients.append(client)
            self.debug('sorted clients B : %r' % map(lambda x:x.cid, sortedClients))
            return sortedClients

    def debug(self, msg):
        self._plugin.debug('scramber:\t %s' % msg)



#--------------------------------------------------------------------------------------------------
class Poweradminbfbc2Plugin(b3.plugin.Plugin):

    _adminPlugin = None

    _enableTeamBalancer = False
    _ignoreBalancingTill = 0
    _tinterval = 0
    _teamdiff = 1
    _tcronTab = None
    _tmaxlevel = 100
    
    _matchmode = False
    _match_plugin_disable = []
    _matchManager = None
    
    _scrambling_planned = False
    _autoscramble_rounds = False
    _autoscramble_maps = False
    _scrambler = Scrambler()
    
    _parseUserCmdRE = re.compile(r'^(?P<cid>[^\s]{2,}|@[0-9]+)\s?(?P<parms>.*)$')
    
    
    def startup(self):
        """\
        Initialize plugin settings
        """

        # get the admin plugin so we can register commands
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
            self.error('Could not find admin plugin')
            return False
    
        # register our commands
        if 'commands' in self.config.sections():
            for cmd in self.config.options('commands'):
                level = self.config.get('commands', cmd)
                sp = cmd.split('-')
                alias = None
                if len(sp) == 2:
                    cmd, alias = sp
            
                func = self.getCmd(cmd)
                if func:
                    self._adminPlugin.registerCommand(self, cmd, level, func, alias)

        # do not balance on the 1st minute after bot start
        self._ignoreBalancingTill = self.console.time() + 60

        # Register our events
        self.registerEvent(b3.events.EVT_CLIENT_TEAM_CHANGE)
        self.registerEvent(b3.events.EVT_GAME_ROUND_START)
        self.registerEvent(b3.events.EVT_GAME_ROUND_PLAYER_SCORES)
        self.registerEvent(b3.events.EVT_CLIENT_DISCONNECT)
        self.registerEvent(b3.events.EVT_CLIENT_AUTH)


    def getCmd(self, cmd):
        cmd = 'cmd_%s' % cmd
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            return func
    
        return None


    def onLoadConfig(self):
        self._scrambler._plugin = self
        self.LoadTeamBalancer()
        self.LoadMatchMode()
        self.LoadScrambler()

    def LoadTeamBalancer(self):
        try:
            self._enableTeamBalancer = self.config.getboolean('teambalancer', 'enabled')
        except:
            self._enableTeamBalancer = False
            self.debug('Using default value (%s) for Teambalancer enabled', self._enableTeamBalancer)

        try:
            self._tmaxlevel = self.config.getint('teambalancer', 'maxlevel')
        except:
            self._tmaxlevel = 100
            self.debug('Using default value (%s) for Teambalancer maxlevel', self._tmaxlevel)

        try:
            self._tinterval = self.config.getint('teambalancer', 'checkInterval')
            # set a max interval for teamchecker
            if self._tinterval > 59:
                self._tinterval = 59
        except:
            self._tinterval = 0
            self.debug('Using default value (%s) for Teambalancer Interval', self._tinterval)
            
    
        try:
            self._teamdiff = self.config.getint('teambalancer', 'maxDifference')
            # set a minimum/maximum teamdifference
            if self._teamdiff < 1:
                self._teamdiff = 1
            if self._teamdiff > 9:
                self._teamdiff = 9
        except:
            self._teamdiff = 1
            self.debug('Using default value (%s) for teamdiff', self._teamdiff)
        
        
        self.debug('Teambalancer enabled: %s' %(self._tinterval))
        self.debug('Teambalancer maxlevel: %s' %(self._tmaxlevel))
        self.debug('Teambalancer check interval (in minute): %s' %(self._tinterval))
        self.debug('Teambalancer max team difference: %s' %(self._teamdiff))
        if self._tcronTab:
            # remove existing crontab
            self.console.cron - self._tcronTab
        if self._tinterval > 0:
            self._tcronTab = b3.cron.PluginCronTab(self, self.autobalance, 0, '*/%s' % (self._tinterval))
            self.console.cron + self._tcronTab
            
            
    def LoadMatchMode(self):
        # MATCH MODE SETUP
        self._match_plugin_disable = []
        try:
            self.debug('pamatch_plugins_disable/plugin : %s' %self.config.get('pamatch_plugins_disable/plugin'))
            for e in self.config.get('pamatch_plugins_disable/plugin'):
                self.debug('pamatch_plugins_disable/plugin : %s' %e.text)
                self._match_plugin_disable.append(e.text)
        except:
            self.debug('Can\'t setup pamatch disable plugins because there is no plugins set in config')

    def LoadScrambler(self):
        try:
            strategy = self.config.get('scrambler', 'strategy')
            self._scrambler.setStrategy(strategy)
            self.debug("scrambling strategy '%s' set" % strategy)
        except:
            self._scrambler.setStrategy('random')
            self.debug('Using default value (%s) for scrambling strategy : random')

        try:
            mode = self.config.get('scrambler', 'mode')
            if mode not in ('off', 'round', 'map'):
                raise ValueError
            if mode == 'off':
                self._autoscramble_rounds = False
                self._autoscramble_maps = False
            elif mode == 'round':
                self._autoscramble_rounds = True
                self._autoscramble_maps = False
            elif mode == 'map':
                self._autoscramble_rounds = False
                self._autoscramble_maps = True
            self.debug('auto scrambler mode is : %s' % mode)
        except:
            self._autoscramble_rounds = False
            self._autoscramble_maps = False
            self.warning('Using default value (off) for auto scrambling mode')
            


##################################################################################################

    def onEvent(self, event):
        """\
        Handle intercepted events
        """
        if event.type == b3.events.EVT_CLIENT_TEAM_CHANGE:
            self.onTeamChange(event.data, event.client)
        elif event.type == b3.events.EVT_GAME_ROUND_PLAYER_SCORES:
            self._scrambler.onRoundOverTeamScores(event.data)
        elif event.type == b3.events.EVT_GAME_ROUND_START:
            self.debug('match mode : '.rjust(30) + str(self._matchmode))
            self.debug('manual scramble planned : '.rjust(30) + str(self._scrambling_planned))
            self.debug('auto scramble rounds : '.rjust(30) + str(self._autoscramble_rounds))
            self.debug('auto scramble maps : '.rjust(30) + str(self._autoscramble_maps))
            self.debug('self.console.game.rounds : '.rjust(30) + repr(self.console.game.rounds))
            # do not balance on the 1st minute after bot start
            self._ignoreBalancingTill = self.console.time() + 60
            if self._scrambling_planned:
                self.debug('manual scramble is planned')
                self._scrambler.scrambleTeams()
                self._scrambling_planned = False
            elif self._matchmode:
                self.debug('match mode on, ignoring autosramble')
            else:
                if self._autoscramble_rounds: 
                    self.debug('auto scramble is planned for rounds')
                    self._scrambler.scrambleTeams()
                elif self._autoscramble_maps and self.console.game.rounds == 0:
                    self.debug('auto scramble is planned for maps')
                    self._scrambler.scrambleTeams()
        elif event.type == b3.events.EVT_CLIENT_DISCONNECT:
            # do not balance just after a player disconnected
            self._ignoreBalancingTill = self.console.time() + 10
        elif event.type == b3.events.EVT_CLIENT_AUTH:
            self.onClientAuth(event.data, event.client)

    def cmd_pateams(self ,data , client, cmd=None):
        """\
        Make the teams balanced
        """
        if client:
            team1players, team2players = self.getTeams()
            
            # if teams are uneven by one or even, then stop here
            gap = abs(len(team1players) - len(team2players))
            if gap <= 1:
                client.message('Teams are balanced, T1: %s, T2: %s (diff: %s)' %(len(team1players), len(team2players), gap))
            else:
                self.teambalance()


    def cmd_pateambalance(self, data, client=None, cmd=None):
        """\
        <on/off> - Set teambalancer on/off
        Setting teambalancer on will warn players that make teams unbalanced
        """
        if not data:
            if client:
                if self._enableTeamBalancer:
                    client.message("team balancing is on")
                else:
                    client.message("team balancing is off")
            else:
                self.debug('No data sent to cmd_teambalance')
        else:
            if data.lower() in ('on', 'off'):
                if data.lower() == 'off':
                    self._enableTeamBalancer = False
                    client.message('Teambancer is now disabled')
                elif data.lower() == 'on':
                    self._enableTeamBalancer = True
                    client.message('Teambancer is now enabled')
            else:
                if client:
                    client.message("Invalid data, expecting 'on' or 'off'")
                else:
                    self.debug('Invalid data sent to cmd_teambalance : %s' % data)
    
    
    def cmd_runscript(self, data, client, cmd=None):
        """\
        <configfile.cfg> - Execute a server configfile.
        """
        if not data:
            client.message('missing paramter, try !help runscript')
        else:
            if re.match('^[a-z0-9_.]+.cfg$', data, re.I):
                self.debug('Executing configfile = [%s]', data)
                try:
                    self.console.write(('admin.runScript', '%s' % data))
                except FrostbiteCommandFailedError, err:
                    self.error(err)
                    client.message('Error: %s' % err.response)
            else:
                self.error('%s is not a valid configfile', data)


    def cmd_pb_sv_command(self, data, client, cmd=None):
        """\
        <punkbuster command> - Execute a punkbuster command
        """
        if not data:
            client.message('missing paramter, try !help pb_sv_command')
        else:
            self.debug('Executing punkbuster command = [%s]', data)
            try:
                self.console.write(('punkBuster.pb_sv_command', '%s' % data))
            except FrostbiteCommandFailedError, err:
                self.error(err)
                client.message('Error: %s' % err.response)


    def cmd_paserverinfo(self, data, client, cmd=None):
        """\
        get server info
        """
        data = self.console.write(('serverInfo',))
        client.message('Server Name: %s' % data[0])
        client.message('Current Players: %s' % data[1])
        client.message('Max Players: %s' % data[2])
        client.message('GameType: %s' % data[3])
        client.message('Map: %s' % self.console.getEasyName(data[4]))


    def cmd_payell(self, data, client, cmd=None):
        """\
        <msg>- Yell message to all players
        """
        if client :
            if not data:
                client.message('missing parameter, try !help payell')
                return False
            self.console.saybig('%s: %s' % (client.exactName, data))
                    
                    
    def cmd_payellteam(self, data, client, cmd=None):
        """\
        <msg> Yell message to all players of your team
        """ 
        if not data:
            client.message('missing parameter, try !help payellteam')
            return False
        for c in self.console.clients.getList():
            if c.team == client.team:
                c.messagebig(data)

    def cmd_payellsquad(self, data, client, cmd=None):
        """\
        <msg> Yell message to all players of your squad
        """ 
        if not data:
            client.message('missing parameter, try !help payellsquad')
            return False
        for c in self.console.clients.getList():
            if c.squad == client.squad and c.team == client.team:
                c.messagebig(data)
    
    
    def cmd_payellenemy(self, data, client, cmd=None):
        """\
        <msg> - Yell message to all players of the other team
        """
        if not data:
            client.message('missing parameter, try !help payellenemy')
            return False
        for c in self.console.clients.getList():
            if c.team != client.team:
                c.messagebig(data)

    def cmd_payellplayer(self, data, client, cmd=None):
        """\
        <player> <msg> - Yell message to a player
        """
        m = self._adminPlugin.parseUserCmd(data)
        if not m:
            client.message('invalid parameters, try !help payellplayer')
            return False
        cid, message = m
        sclient = self._adminPlugin.findClientPrompt(cid, client)
        if not sclient:
            return False
        sclient.messagebig(message)
        
        
    def cmd_paversion(self, data, client, cmd=None):
        """\
        This command identifies PowerAdminBFBC2 version and creator.
        """
        #client.message(message)
        cmd.sayLoudOrPM(client, 'I am PowerAdminBFBC2 version %s by %s' % (__version__, __author__))
        return None
        
    def cmd_pamaplist(self, data, client, cmd=None):
        """\
        <maplist.txt> - Load a server maplist.
        (You must use the command exactly as it is! )
        """
        if not data:
            client.message('Invalid or missing data, try !help pamaplist')
            return False
        else:
            if re.match('^[a-z0-9_.]+.txt$', data, re.I):
                self.debug('Loading maplist = [%s]', data)
                self.console.write(('mapList.load %s' % data))
            else:
                self.error('%s is not a valid maplist', data)
        
     
    def cmd_pamaprestart(self, data, client, cmd=None):
        """\
        Restart the current map.
        (You can safely use the command without the 'pa' at the beginning)
        """
        self.console.say('Restarting map')
        time.sleep(1)
        self.console.write(('admin.restartMap',))
        return True
        
    
    def cmd_pamapreload(self, data, client, cmd=None):
        """\
        Reload the current map.
        (You can safely use the command without the 'pa' at the beginning)
        """
        self.console.say('Reloading map')
        time.sleep(1)
        data = self.console.write(('admin.currentLevel',))
        self.console.write(('mapList.clear',))
        self.console.write(('mapList.append', data))
        self.console.write(('admin.runNextLevel',))
        self.console.write(('mapList.load',))
        return True
        
        
    def cmd_paset(self, data, client, cmd=None):
        """\
        <var> <value> - Set a server var to a certain value.
        (You must use the command exactly as it is! )
        """
        if client:
            if not data:
                client.message('Invalid or missing data, try !help paset')
            else:
                # are we still here? Let's write it to console
                varName, value = data.split(' ',1)
                try:
                    self.console.write(('vars.%s' % varName, value))
                    client.message('%s set' % varName)
                except FrostbiteCommandFailedError, err:
                    client.message('ERROR setting %s : %s' % (varName, err))



    def cmd_paget(self, data, client, cmd=None):
        """\
        <var> - Returns the value of a servervar.
        (You must use the command exactly as it is! )
        """
        if not data:
            client.message('Invalid or missing data, try !help paget')
        else:
            # are we still here? Let's write it to console
            var = data.split(' ')
            cvar = self.console.getCvar(var[0])
            client.message('%s' % cvar.value)

        
        
    def cmd_pasetnextmap(self, data, client=None, cmd=None):
        """\
        <mapname> - Set the nextmap (partial map name works)
        """
        if not data:
            client.message('Invalid or missing data, try !help setnextmap')
        else:
            match = self.console.getMapsSoundingLike(data)
            if len(match) > 1:
                client.message('do you mean : %s ?' % ", ".join(match))
                return
            if len(match) == 1:
                levelname = match[0]
                
                currentLevelCycle = self.console.write(('mapList.list',))
                try:
                    newIndex = currentLevelCycle.index(levelname)
                    self.console.write(('mapList.nextLevelIndex', newIndex))
                except ValueError:
                    # the wanted map is not in the current cycle
                    # insert the map in the cycle
                    mapindex = self.console.write(('mapList.nextLevelIndex',))
                    self.console.write(('mapList.insert', mapindex, levelname))
                if client:
                    cmd.sayLoudOrPM(client, 'nextmap set to %s' % self.console.getEasyName(levelname))
            else:
                client.message('do you mean : %s.' % ", ".join(data))
      
      
    def cmd_paident(self, data, client, cmd=None):
        """\
        [<name>] - show the ip and guid of a player
        (You can safely use the command without the 'pa' at the beginning)
        """
        input = self.parseUserCmd(data)
        if not input:
            # assume the player wants his own ident
            try:
                cmd.sayLoudOrPM(client, '%s %s %s' % (client.cid, client.ip, client.guid))
            except FrostbiteCommandFailedError, err:
                client.message('Error, server replied %s' % err)
        else:
            try:
                # input[0] is the player id
                sclient = self._adminPlugin.findClientPrompt(input[0], client)
                if sclient:
                    cmd.sayLoudOrPM(client, '%s %s %s' % (sclient.cid, sclient.ip, sclient.guid))
            except FrostbiteCommandFailedError, err:
                client.message('Error, server replied %s' % err)
        
    def cmd_reserveslot(self, data, client, cmd=None):
        """\
        <player> add player to the list of players who can use the reserved slots
        """
        # this will split the player name and the message
        input = self._adminPlugin.parseUserCmd(data)
        if input:
            sclient = self._adminPlugin.findClientPrompt(input[0], client)
            if not sclient:
                # a player matching the name was not found, a list of closest matches will be displayed
                # we can exit here and the user will retry with a more specific player
                return False
            else:
                try:
                    self.console.write(('reservedSlots.load',))
                    self.console.write(('reservedSlots.addPlayer', sclient.cid))
                    self.console.write(('reservedSlots.save',))
                    client.message('%s added to reserved slots list' % sclient.cid)
                    sclient.message('You now have access to reserved slots thanks to %s' % client.cid)
                except FrostbiteCommandFailedError, err:
                    if err.message == ['PlayerAlreadyInList']:
                        client.message('%s already has access to reserved slots' % sclient.cid)
                    else:
                        client.message('Error: %s' % err.message)

    def cmd_unreserveslot(self, data, client, cmd=None):
        """\
        <player> remove player from the list of players who can use the reserved slots
        """
        # this will split the player name and the message
        input = self._adminPlugin.parseUserCmd(data)
        if input:
            sclient = self._adminPlugin.findClientPrompt(input[0], client)
            if not sclient:
                # a player matchin the name was not found, a list of closest matches will be displayed
                # we can exit here and the user will retry with a more specific player
                return False
            else:
                try:
                    self.console.write(('reservedSlots.load',))
                    self.console.write(('reservedSlots.removePlayer', sclient.cid))
                    self.console.write(('reservedSlots.save',))
                    client.message('%s removed from reserved slots list' % sclient.cid)
                    sclient.message('You don\'t have access to reserved slots anymore')
                except FrostbiteCommandFailedError, err:
                    if err.message == ['PlayerNotInList']:
                        client.message('%s has no access to reserved slots' % sclient.cid)
                    else:
                        client.message('Error: %s' % err.message)

    def cmd_runnextround(self, data, client, cmd=None):
        """\
        Switch to next round, without ending current
        """
        self.console.say('forcing next round')
        time.sleep(1)
        try:
            self.console.write(('admin.runNextRound',))
        except FrostbiteCommandFailedError, err:
            client.message('Error: %s' % err.message)
        
    def cmd_pakill(self, data, client, cmd=None):
        """\
        <name> <reason> - kill a player
        """
        m = self.parseUserCmd(data)
        if not m:
            client.message('Invalid data, try !help pakill')
        else:
            cid, keyword = m
            reason = self._adminPlugin.getReason(keyword)
    
            if not reason and client.maxLevel < self._adminPlugin.config.getint('settings', 'noreason_level'):
                client.message('ERROR: You must supply a reason')
            else:
                sclient = self._adminPlugin.findClientPrompt(cid, client)
                if sclient:
                    self.console.saybig('%s was terminated by server admin' % sclient.name)
                    try:
                        self.console.write(('admin.killPlayer', sclient.cid))
                        if reason:
                            self.console.say('%s was terminated by server admin for : %s' % (sclient.name, reason))
                    except FrostbiteCommandFailedError, err:
                        client.message('Error, server replied %s' % err)
     

    def cmd_pachangeteam(self, data, client, cmd=None):
        """\
        [<name>] - change a player to the other team
        """
        input = self.parseUserCmd(data)
        if not input:
            client.message('Invalid data, try !help pachangeteam')
        else:
            # input[0] is the player id
            sclient = self._adminPlugin.findClientPrompt(input[0], client)
            if sclient:
                if sclient.teamId == 1:
                    newteam = '2'
                else:
                    newteam = '1' 
                try:
                    self.console.write(('admin.movePlayer', sclient.cid, newteam, 0, 'true'))
                    cmd.sayLoudOrPM(client, '%s forced from team %s to team %s' % (sclient.cid, sclient.teamId, newteam))
                except FrostbiteCommandFailedError, err:
                    client.message('Error, server replied %s' % err)
        
        
    def cmd_paspectate(self, data, client, cmd=None):
        """\
        [<name>] - move a player to spectate
        """
        input = self.parseUserCmd(data)
        if not input:
            client.message('Invalid data, try !help paspectate')
        else:
            # input[0] is the player id
            sclient = self._adminPlugin.findClientPrompt(input[0], client)
            if sclient:
                try:
                    self.console.write(('admin.movePlayer', sclient.cid, 0, 0, 'true'))
                    cmd.sayLoudOrPM(client, '%s forced to spectate' % sclient.name)
                except FrostbiteCommandFailedError, err:
                    client.message('Error, server replied %s' % err)
        
    def cmd_pamatch(self, data, client, cmd=None): 
        """\
        Set server match mode on/off
        (You can safely use the command without the 'pa' at the beginning)
        """
        if not data or str(data).lower() not in ('on','off'):
            client.message('Invalid or missing data, expecting "on" or "off"')
            return False
        else:
            if data.lower() == 'on':
                
                self._matchmode = True
                self._enableTeamBalancer = False
                
                for e in self._match_plugin_disable:
                    self.debug('Disabling plugin %s' %e)
                    plugin = self.console.getPlugin(e)
                    if plugin:
                        plugin.disable()
                        client.message('plugin %s disabled' % e)
                
                self.console.say('match mode: ON')
                if self._matchManager:
                    self._matchManager.stop()
                self._matchManager = MatchManager(self)
                self._matchManager.initMatch()

            elif data.lower() == 'off':
                self._matchmode = False
                if self._matchManager:
                    self._matchManager.stop()
                self._matchManager = None
                
                # enable plugins
                for e in self._match_plugin_disable:
                    self.debug('enabling plugin %s' %e)
                    plugin = self.console.getPlugin(e)
                    if plugin:
                        plugin.enable()
                        client.message('plugin %s enabled' % e)

                self.console.say('match mode: OFF')
                
    def _changeMode(self, data, client, cmd=None, mode=None):
        if mode is None:
            self.error('mode cannot be None')
        elif mode not in ('CONQUEST', 'RUSH', 'SQDM', 'SQRUSH'):
            self.error('invalid game mode %s' % mode)
        else:
            try:
                self.console.write(('admin.setPlaylist', mode))
                client.message('Server playlist changed to %s' % mode)
                client.message('Use the !map command to switch to the new game mode')
            except FrostbiteCommandFailedError, err:
                client.message('Failed to change game mode. Server replied with: %s' % err)
            
    def cmd_paconquest(self, data, client, cmd=None): 
        """\
        change server mode to CONQUEST
        """
        self._changeMode(data, client, cmd, mode='CONQUEST')
        
    def cmd_parush(self, data, client, cmd=None): 
        """\
        change server mode to RUSH
        """
        self._changeMode(data, client, cmd, mode='RUSH')
        
    def cmd_pasqdm(self, data, client, cmd=None): 
        """\
        change server mode to SQDM
        """
        self._changeMode(data, client, cmd, mode='SQDM')
        
    def cmd_pasqrush(self, data, client, cmd=None): 
        """\
        change server mode to SQRUSH
        """
        self._changeMode(data, client, cmd, mode='SQRUSH')
        
    def cmd_scramble(self, data, client, cmd=None):
        """\
        Toggle on/off the teams scrambling for next round
        """
        if self._scrambling_planned:
            self._scrambling_planned = False
            client.message('Teams scrambling canceled for next round')
        else:
            self._scrambling_planned = True
            client.message('Teams will be scrambled at next round start')

    def cmd_scramblemode(self, data, client, cmd=None):
        """\
        <random|score> change the scrambling strategy
        """
        if not data:
            client.message("invalid data. Expecting 'random' or 'score'")
        else:
            if data[0].lower() == 'r':
                self._scrambler.setStrategy('random')
                client.message('Scrambling strategy is now: random')
            elif data[0].lower() == 's':
                self._scrambler.setStrategy('score')
                client.message('Scrambling strategy is now: score')
            else:
                client.message("invalid data. Expecting 'random' or 'score'")

    def cmd_autoscramble(self, data, client, cmd=None):
        """\
        <off|round|map> manage the auto scrambler
        """
        if not data:
            client.message("invalid data. Expecting one of [off, round, map]")
        else:
            if data.lower() == 'off':
                self._autoscramble_rounds = False
                self._autoscramble_maps = False
                client.message('Auto scrambler now disabled')
            elif data[0].lower() == 'r':
                self._autoscramble_rounds = True
                self._autoscramble_maps = False
                client.message('Auto scrambler will run at every round start')
            elif data[0].lower() == 'm':
                self._autoscramble_rounds = False
                self._autoscramble_maps = True
                client.message('Auto scrambler will run at every map change')
            else:
                client.message("invalid data. Expecting one of [off, round, map]")
                    
    def cmd_swap(self, data, client, cmd=None):
        """\
        <player A> <player B> - swap teams for player A and B if they are in different teams
        """
        input = self._adminPlugin.parseUserCmd(data)
        if not input:
            client.message('Invalid data, try !help swap')
            return
        # input[0] is player A
        pA = input[0]

        if len(input)==1 or input[1] is None:
            client.message('Invalid data, try !help swap')
            return
                
        input = self._adminPlugin.parseUserCmd(input[1])
        if not input:
            client.message('Invalid data, try !help swap')
            return
        pB = input[0]
        
        sclientA = self._adminPlugin.findClientPrompt(pA, client)
        if not sclientA:
            return
        sclientB = self._adminPlugin.findClientPrompt(pB, client)
        if not sclientB:
            return
        if sclientA.teamId not in (1, 2) and sclientB.teamId not in (1, 2):
            client.message('could not determine players teams')
            return
        if sclientA.teamId == sclientB.teamId:
            client.message('both players are in the same team. Cannot swap')
            return
        teamA = sclientA.teamId
        teamB = sclientB.teamId
        teamA, teamB = teamB, teamA
        self._movePlayer(sclientA, teamA)
        self._movePlayer(sclientB, teamB)
        cmd.sayLoudOrPM(client, 'swapped player %s with %s' % (sclientA.cid, sclientB.cid))

                
        
##################################################################################################  

    def parseUserCmd(self, cmd, req=False):
        """Parse command arguments to extract a player id as a first paramenter
        from the other params
        """
        m = re.match(self._parseUserCmdRE, cmd)

        if m:
            cid = m.group('cid')
            parms = m.group('parms')

            if req and not len(parms): return None

            if cid[:1] == "'" and cid[-1:] == "'":
                cid = cid[1:-1]

            return (cid, parms)
        else:
            return None
        
        
    def removeClantag(self, dirtyname):
        #sclient = self._adminPlugin.findClientPrompt(input[0], client)
        dirtyname = self.console.stripColors(dirtyname) 
        m = re.search('(?<=' ')\w+', dirtyname)
        return (m.group(0))
    

    def onClientAuth(self, data, client):
        #store the time of teamjoin for autobalancing purposes 
        client.setvar(self, 'teamtime', self.console.time())
        
    def onTeamChange(self, data, client):
        #store the time of teamjoin for autobalancing purposes 
        client.setvar(self, 'teamtime', self.console.time())
        self.verbose('Client variable teamtime set to: %s' % client.var(self, 'teamtime').value)
        
        if self._enableTeamBalancer:
            
            if self.console.time() < self._ignoreBalancingTill:
                return
            
            if client.team in (b3.TEAM_SPEC, b3.TEAM_UNKNOWN):
                return
            
            # get teams
            team1players, team2players = self.getTeams()
            
            # if teams are uneven by one or even, then stop here
            if abs(len(team1players) - len(team2players)) <= 1:
                return
            
            biggestteam = team1players
            if len(team2players) > len(team1players):
                biggestteam = team2players
            
            # has the current player gone contributed to making teams uneven ?
            if client.cid in biggestteam:
                self.debug('%s has contributed to unbalance the teams')
                client.message('do not make teams unbalanced')
                if client.teamId == 1:
                    newteam = '2'
                else:
                    newteam = '1' 
                try:
                    self.console.write(('admin.movePlayer', client.cid, newteam, 0, 'true'))
                except FrostbiteCommandFailedError, err:
                    self.warning('Error, server replied %s' % err)
                
    def autobalance(self):
        ## called from cron
        if self._enableTeamBalancer is False:
            return
        if self.console.time() < self._ignoreBalancingTill:
            self.debug('ignoring team balancing as the round started less than 1 minute ago')
            return
        self.teambalance()
                
    def teambalance(self):
        # get teams
        team1players, team2players = self.getTeams()
        
        # if teams are uneven by one or even, then stop here
        gap = abs(len(team1players) - len(team2players))
        if gap <= self._teamdiff:
            self.verbose('Teambalancer: Teams are balanced, T1: %s, T2: %s (diff: %s, tolerance: %s)' %(len(team1players), len(team2players), gap, self._teamdiff))
            return
        
        howManyMustSwitch = int(gap / 2)
        bigTeam = 1
        smallTeam = 2
        if len(team2players) > len(team1players):
            bigTeam = 2
            smallTeam = 1
            
        self.verbose('Teambalance: Teams are NOT balanced, T1: %s, T2: %s (diff: %s)' %(len(team1players), len(team2players), gap))
        self.console.saybig('Autobalancing Teams!')

        ## we need to change team for howManyMustSwitch players from bigteam
        playerTeamTimes = {}
        clients = self.console.clients.getList()
        for c in clients:
            if c.teamId == bigTeam:
                playerTeamTimes[c] = c.var(self, 'teamtime', self.console.time()).value
        #self.debug('playerTeamTimes: %s' % playerTeamTimes)
        sortedPlayersTeamTimes = sorted(playerTeamTimes.iteritems(), key=lambda (k,v):(v,k))
        #self.debug('sortedPlayersTeamTimes: %s' % sortedPlayersTeamTimes)

        playersToMove = [c for (c,teamtime) in sortedPlayersTeamTimes if c.maxLevel<self._tmaxlevel][:howManyMustSwitch]
        self.console.say('forcing %s to the other team' % (', '.join([c.name for c in playersToMove])))
        for c in playersToMove:
            self._movePlayer(c, smallTeam)
                
    def _movePlayer(self, client, newTeamId):
        try:
            client.setvar(self, 'movedByBot', True)
            self.console.write(('admin.movePlayer', client.cid, newTeamId, 0, 'true'))
        except FrostbiteCommandFailedError, err:
            self.warning('Error, server replied %s' % err)
                    
    def getTeams(self):
        """Return two lists containing the names of players from both teams"""
        team1players = []
        team2players = []
        for name, clientdata in self.console.getPlayerList().iteritems():
            if str(clientdata['teamId']) == '1':
                team1players.append(name)
            elif str(clientdata['teamId']) == '2':
                team1players.append(name)
        return team1players, team2players
       
################################################################################## 
import threading
class MatchManager:
    plugin = None
    _adminPlugin = None
    console = None
    playersReady = {}
    countDown = 10
    running = True
    timer = None
    countdownStarted = None
    
    def __init__(self, plugin):
        self.plugin = plugin
        self.console = plugin.console
        self._adminPlugin = self.console.getPlugin('admin')
        if not self._adminPlugin:
            # something is wrong, can't start without admin plugin
            raise Exception('Could not find admin plugin')
    
    def stop(self):
        try: self.timer.cancel()
        except: pass
        self.running = False
        self.unregisterCommandReady()
        
    def initMatch(self):
        for c in self.console.clients.getList():
            c.setvar(self.plugin, 'ready', False)
        self.countdownStarted = False
        self.registerCommandReady()
        self.console.saybig('MATCH starting soon !!')
        self.console.say('ALL PLAYERS : type !ready when you are ready')
        self.console.saybig('ALL PLAYERS : type !ready when you are ready')
        self.timer = threading.Timer(10.0, self._checkIfEveryoneIsReady)
        self.timer.start()
    
    def registerCommandReady(self):
        self._adminPlugin.registerCommand(self.plugin, 'ready', 0, self.cmd_ready)
    
    def unregisterCommandReady(self):
        # unregister the !ready command
        try:
            cmd = self._adminPlugin._commands['ready']
            if cmd.plugin == self.plugin:
                self.plugin.debug('unregister !ready command')
                del self._adminPlugin._commands['ready']
        except KeyError:
            pass
    
    def yellToClient(self, message, duration, client):
        """We need this to bypass the message queue managed by the BFBC2 parser"""
        self.console.write(('admin.yell', message, duration, 'player', client.cid))

    def _checkIfEveryoneIsReady(self):
        self.console.debug('checking if all players are ready')
        isAllPlayersReady = True
        waitingForPlayers = []
        for c in self.console.clients.getList():
            isReady = c.var(self.plugin, 'ready', False).value
            self.plugin.debug('is %s ready ? %s' % (c.cid, isReady))
            if isReady is False:
                waitingForPlayers.append(c)
                self.yellToClient('we are waiting for you. type !ready', 10000, c)
                isAllPlayersReady = False
    
        if len(waitingForPlayers) > 0 and len(waitingForPlayers) <= 6:
            self.console.say('waiting for %s' % ', '.join([c.cid for c in waitingForPlayers]))
        
        try: self.timer.cancel()
        except: pass
        
        if isAllPlayersReady is True:
            self.console.say('All players are ready, starting count down')
            self.countDown = 10
            self.countdownStarted = True
            self.timer = threading.Timer(0.9, self._countDown)
        else:
            self.timer = threading.Timer(10.0, self._checkIfEveryoneIsReady)
            
        if self.running:
            self.timer.start()

    def _countDown(self):
        self.plugin.debug('countdown: %s' % self.countDown)
        if self.countDown > 0:
            self.console.write(('admin.yell', 'MATCH STARTING IN %s' % self.countDown, 900, 'all'))
            self.countDown -= 1
            if self.running:
                self.timer = threading.Timer(1.0, self._countDown)
                self.timer.start()
        else:    
            # make sure to have a brief big text
            self.console.write(('admin.yell', 'FIGHT !!!', 6000, 'all'))
            self.console.say('Match started. GL & HF')
            self.console.write(('admin.restartMap',))
            self.stop()

    def cmd_ready(self, data, client, cmd=None): 
        """\
        Notify other teams you are ready to start the match
        """
        self.plugin.debug('MatchManager::ready(%s)' % client.cid)
        if self.countdownStarted:
            client.message('Count down already started. You cannot change your ready state')
        else:
            wasReady = client.var(self.plugin, 'ready', False).value
            if wasReady:
                client.setvar(self.plugin, 'ready', False)
                self.yellToClient('You are not ready anymore', 3000, client)
                client.message('You are not ready anymore')
            else:
                client.setvar(self.plugin, 'ready', True)
                self.yellToClient('You are now ready', 3000, client)
                client.message('You are now ready')
            self._checkIfEveryoneIsReady()





if __name__ == '__main__':
    import time
    
    from b3.fake import fakeConsole, FakeConsole
    fakeConsole.gameName = 'bfbc2'
    
    fakeConsole.Events.createEvent('EVT_GAME_ROUND_PLAYER_SCORES', 'round player scores')
    fakeConsole.Events.createEvent('EVT_GAME_ROUND_TEAM_SCORES', 'round team scores')
    
    from b3.fake import joe, simon, moderator, superadmin
            
    from b3.config import XmlConfigParser
    conf = XmlConfigParser()
    conf.setXml("""
    <configuration plugin="poweradminbfbc2">
        <settings name="commands">
            <set name="runscript">100</set>
            <set name="pb_sv_command-pbcmd">100</set>
            <set name="paset">100</set>
            <set name="paget">100</set>
    
            <set name="parush-rush">60</set>
            <set name="paconquest-conq">60</set>
            <set name="pasqdm-sqdm">60</set>
            <set name="pasqrush-sqru">60</set>
            
            <set name="pamaplist-maplist">60</set>
            <set name="pamaprestart-maprestart">60</set>
            <set name="pamapreload-mapreload">60</set>
            <set name="pasetnextmap-setnextmap">60</set>
    
            <set name="pachangeteam-ct">60</set>
            <set name="paspectate-spectate">60</set>
            <set name="pakill-kill">60</set>
    
            <set name="paserverinfo">40</set>
            <set name="paversion">20</set>
    
            <set name="pateambalance">40</set>
            <set name="pateams-teams">20</set>
            <set name="swap">20</set>
            <set name="scramble">20</set>
            <set name="scramblemode">20</set>
            <set name="autoscramble">20</set>
    
            <set name="payell-yell">20</set>
            <set name="payellteam-yt">20</set>
            <set name="payellenemy-ye">20</set>
            <set name="payellplayer-yp">20</set>
            <set name="payellsquad-ys">20</set>
    
            <set name="paident-id">20</set>
    
            <!-- set match mode on/off. Will wait for teams leaders to type !ready
                and then start a count down -->
            <set name="pamatch-match">20</set>
        </settings>
    
        <settings name="teambalancer">
            <set name="enabled">no</set>
            <set name="checkInterval">1</set>
            <set name="maxDifference">1</set>
            <set name="maxlevel">20</set>
        </settings>
    
        <settings name="scrambler">
            <set name="mode">off</set>
            <set name="strategy">random</set>
        </settings>
        
        <pamatch_plugins_disable>
            <!-- The Plugins that need to be disabled during matchmode -->
            <plugin>spree</plugin>
            <plugin>adv</plugin>
            <plugin>tk</plugin>
            <plugin>pingwatch</plugin>
        </pamatch_plugins_disable>
    </configuration>
    """)

    
    ## create an instance of the plugin to test
    p = Poweradminbfbc2Plugin(fakeConsole, conf)
    p.onStartup()

    joe.connects('Joe')
    joe.teamId = 1
    print 'joe.guid: %s' % joe.guid
    superadmin.connects('superadmin')
    superadmin.teamId = 1
    print 'superadmin.guid: %s' % superadmin.guid
    
    def getPlayerList(self=None, maxRetries=0):
        players = {}
        for c in fakeConsole.clients.getList():
            players[c.cid] = {
                'cid' : c.cid,
                'name' : c.name,
                'teamId': c.teamId
                }
        print "getPlayerList : %s" % repr(players)
        return players
    FakeConsole.getPlayerList = getPlayerList
    
    def getPlayerScores(self=None, maxRetries=0):
        scores = {}
        for c in fakeConsole.clients.getList():
            scores[c.cid] = random.randint(-20, 200)
        print "getPlayerScores : %s" % repr(scores)
        return scores
    FakeConsole.getPlayerScores = getPlayerScores
    
    def getClient(self, cid, _guid=None):
        return fakeConsole.clients.getByCID(cid)
    FakeConsole.getClient = getClient
    
    def movePlayer(client, newTeamId):
        client.teamId = newTeamId
        print " %s -----> team %s" % (client.cid, newTeamId)
    p._movePlayer = movePlayer
    
    def testMatch1():
        print """-----------------------
        usual scenario"""
        moderator.says('!match on')
        time.sleep(1)
        
        joe.says('!ready')
        time.sleep(1)
    
        simon.says('!ready')
        time.sleep(1)
    
        moderator.says('!ready')
        time.sleep(15)
        p._matchManager.stop()
        
    def testMatch2():
        print """-----------------------
        joe types !ready a second time"""
        moderator.says('!match on')
        time.sleep(1)
        
        joe.says('!ready')
        time.sleep(1)
    
        simon.says('!ready')
        time.sleep(1)

        joe.says('!ready')
        time.sleep(1)
    
        moderator.says('!ready')
        time.sleep(15)
        
        p._matchManager.stop()
        
    def testMatch3():
        print """-----------------------
        moderator types !match off"""
        moderator.says('!match on')
        time.sleep(1)
        
        joe.says('!ready')
        time.sleep(1)
    
        simon.says('!ready')
        time.sleep(1)
    
        moderator.says('!match off')
        time.sleep(15)
        
        print "p._matchManager : %s" % p._matchManager

    def testMatch4():
        print """-----------------------
        moderator types !match on a second time"""
        moderator.says('!match on')
        time.sleep(1)
        
        joe.says('!ready')
        time.sleep(1)
    
        simon.says('!ready')
        time.sleep(1)
    
        moderator.says('!match on')
        time.sleep(15)
        
        joe.says('!ready')
        time.sleep(1)
    
        simon.says('!ready')
        time.sleep(12)
        
        moderator.says('!ready')
        
        time.sleep(12)
        print "p._matchManager : %s" % p._matchManager
        
        
    def testMatch5():
        print """-----------------------
        a player got kicked"""
        p.console.PunkBuster = None
        
        moderator.says('!match on')
        time.sleep(1)
        
        joe.says('!ready')
        time.sleep(1)
    
        moderator.says('!ready')
        time.sleep(15)
        
        simon.kick('AFL')
        time.sleep(30)
        p._matchManager.stop()
        
    def testMatch6():
        print """-----------------------
        a player tries to type !ready after the count down started"""
        p.console.PunkBuster = None
        
        moderator.says('!match on')
        time.sleep(1)
        
        joe.says('!ready')
        time.sleep(1)
    
        moderator.says('!ready')
        time.sleep(1)
        
        simon.says('!ready')
        time.sleep(5)
        
        simon.says('!ready')
        time.sleep(10)
        p._matchManager.stop()

    def testServerModeChange():
        superadmin.connects('Superman')
        superadmin.says('!parush')
        superadmin.says('!rush')
        superadmin.says('!pasqrush')
        superadmin.says('!pasqru')
        superadmin.says('!paconquest')
        superadmin.says('!conq')
        superadmin.says('!pasqrush')
        superadmin.says('!sqru')
        
        
    def test_swap():
        superadmin.says('!swap')
        superadmin.says('!swap alfred')
        superadmin.says('!swap alfred joe')
        superadmin.says('!swap joe alfred')
        joe.teamId = 1
        superadmin.teamId = 1
        superadmin.says('!swap joe god')
        time.sleep(1)
        joe.teamId = 2
        superadmin.says('!swap joe god')
        time.sleep(1)
        if joe.teamId == 1 and superadmin.teamId == 2:
            print "swap success"
        else:
            print "players where not swapped !"

    def test_scramble():
        superadmin.says('!scramble')
        print p._scrambling_planned
        superadmin.says('!scramble')
        print p._scrambling_planned
        superadmin.says('!scramble')
        print p._scrambling_planned
        fakeConsole.clients.newClient(cid='p1', guid='p1')
        fakeConsole.clients.newClient(cid='p2', guid='p2')
        fakeConsole.clients.newClient(cid='p3', guid='p3')
        fakeConsole.clients.newClient(cid='p4', guid='p4')
        fakeConsole.clients.newClient(cid='p5', guid='p5')
        fakeConsole.clients.newClient(cid='p6', guid='p6')
        p._scrambler.scrambleTeams()
        print "-------------"
        p._scrambler.scrambleTeams()
        print "-------------"
        superadmin.says('!scramblemode')
        superadmin.says('!scramblemode random')
        superadmin.says('!scramblemode score')
        
        scores = fakeConsole.getPlayerScores()
        scorelist = ['2','name','score',len(scores)]
        for k, v in scores.items():
            scorelist.append(k)
            scorelist.append(v)
        p._scrambler._last_round_scores = PlayerInfoBlock(scorelist)
        fakeConsole.clients.newClient(cid='p7', guid='p7')
        p._scrambler.scrambleTeams()
        print "============="
        time.sleep(5)
        fakeConsole.queueEvent(fakeConsole.getEvent('EVT_GAME_ROUND_START', 2, None))
        time.sleep(10)
        fakeConsole.queueEvent(fakeConsole.getEvent('EVT_GAME_ROUND_START', 2, None))
    
    def test_autoscramble_round():
        print """
        
/*\\
|*|        
|*| Testing !autoscramble round        
|*|        
\\*/        
        """
        p._scrambling_planned = False
        fakeConsole.game.g_maxrounds = 2
        superadmin.says('!scramblemode random')
        superadmin.says('!autoscramble off')
        fakeConsole.clients.newClient(cid='p1', guid='p1')
        fakeConsole.clients.newClient(cid='p2', guid='p2')
        fakeConsole.clients.newClient(cid='p3', guid='p3')
        print "============="
        fakeConsole.game.rounds = 0
        fakeConsole.queueEvent(fakeConsole.getEvent('EVT_GAME_ROUND_START', fakeConsole.game, None))
        time.sleep(1)
        fakeConsole.game.rounds = 1
        fakeConsole.queueEvent(fakeConsole.getEvent('EVT_GAME_ROUND_START', fakeConsole.game, None))
        time.sleep(1)
        fakeConsole.game.rounds = 0
        fakeConsole.queueEvent(fakeConsole.getEvent('EVT_GAME_ROUND_START', fakeConsole.game, None))
        time.sleep(1)
        superadmin.says('!autoscramble round')
        time.sleep(1)
        print '=============== round 0 ============'
        fakeConsole.game.rounds = 0
        fakeConsole.queueEvent(fakeConsole.getEvent('EVT_GAME_ROUND_START', fakeConsole.game, None))
        time.sleep(1)
        print '--------------- round 1 ------------'
        fakeConsole.game.rounds = 1
        fakeConsole.queueEvent(fakeConsole.getEvent('EVT_GAME_ROUND_START', fakeConsole.game, None))
        time.sleep(1)
        print '--------------- round 2 ------------'
        fakeConsole.game.rounds = 2
        fakeConsole.queueEvent(fakeConsole.getEvent('EVT_GAME_ROUND_START', fakeConsole.game, None))
        time.sleep(1)
        print '=============== round 0 ============'
        fakeConsole.game.rounds = 0
        fakeConsole.queueEvent(fakeConsole.getEvent('EVT_GAME_ROUND_START', fakeConsole.game, None))
        time.sleep(1)
        print '--------------- round 1 ------------'
        fakeConsole.game.rounds = 1
        fakeConsole.queueEvent(fakeConsole.getEvent('EVT_GAME_ROUND_START', fakeConsole.game, None))
        
           
    
    def test_autoscramble_map():
        print """
        
/*\\
|*|        
|*| Testing !autoscramble map        
|*|        
\\*/        
        """
        p._scrambling_planned = False
        fakeConsole.game.g_maxrounds = 2
        superadmin.says('!scramblemode random')
        superadmin.says('!autoscramble off')
        fakeConsole.clients.newClient(cid='p1', guid='p1')
        fakeConsole.clients.newClient(cid='p2', guid='p2')
        fakeConsole.clients.newClient(cid='p3', guid='p3')
        print "============="
        fakeConsole.game.rounds = 0
        fakeConsole.queueEvent(fakeConsole.getEvent('EVT_GAME_ROUND_START', fakeConsole.game, None))
        time.sleep(1)
        fakeConsole.game.rounds = 1
        fakeConsole.queueEvent(fakeConsole.getEvent('EVT_GAME_ROUND_START', fakeConsole.game, None))
        time.sleep(1)
        fakeConsole.game.rounds = 0
        fakeConsole.queueEvent(fakeConsole.getEvent('EVT_GAME_ROUND_START', fakeConsole.game, None))
        time.sleep(1)
        superadmin.says('!autoscramble map')
        time.sleep(1)
        print '=============== round 0 ============'
        fakeConsole.game.rounds = 0
        fakeConsole.queueEvent(fakeConsole.getEvent('EVT_GAME_ROUND_START', fakeConsole.game, None))
        time.sleep(1)
        print '--------------- round 1 ------------'
        fakeConsole.game.rounds = 1
        fakeConsole.queueEvent(fakeConsole.getEvent('EVT_GAME_ROUND_START', fakeConsole.game, None))
        time.sleep(1)
        print '--------------- round 2 ------------'
        fakeConsole.game.rounds = 2
        fakeConsole.queueEvent(fakeConsole.getEvent('EVT_GAME_ROUND_START', fakeConsole.game, None))
        time.sleep(1)
        print '=============== round 0 ============'
        fakeConsole.game.rounds = 0
        fakeConsole.queueEvent(fakeConsole.getEvent('EVT_GAME_ROUND_START', fakeConsole.game, None))
        time.sleep(1)
        print '--------------- round 1 ------------'
        fakeConsole.game.rounds = 1
        fakeConsole.queueEvent(fakeConsole.getEvent('EVT_GAME_ROUND_START', fakeConsole.game, None))
        
    def test_teambalancer():
        p._ignoreBalancingTill = time.time() - 1
        p._enableTeamBalancer = True
        # remove crontab s
        if p._tcronTab:
            p.console.cron - p._tcronTab
        
        from b3.fake import simon, moderator, FakeClient
        
        time.sleep(1)
        p.teambalance()
        time.sleep(2)
        p.teambalance()
        time.sleep(2)
        print "- - - - - - - - - - - "
        superadmin.teamId = 1
        joe.teamId = 1
        joe.groupBits = 16
        simon.connects('simon')
        simon.teamId = 1
        simon.groupBits = 16
        moderator.connects('moderator')
        moderator.teamId = 1
        moderator.groupBits = 16
        p1 = FakeClient(fakeConsole, name="p1", exactName="P1", guid="p1", groupBits=16, teamId=1)
        p1.connects('p1')
        p2 = FakeClient(fakeConsole, name="p2", exactName="P2", guid="p2", groupBits=1, teamId=1)
        p2.connects('p2')
        p3 = FakeClient(fakeConsole, name="p3", exactName="P3", guid="p3", groupBits=16, teamId=1)
        p3.connects('p3')
        p4 = FakeClient(fakeConsole, name="p4", exactName="P4", guid="p4", groupBits=1, teamId=1)
        p4.connects('p4')
        p5 = FakeClient(fakeConsole, name="p5", exactName="P5", guid="p5", groupBits=16, teamId=1)
        p5.connects('p5')
        p6 = FakeClient(fakeConsole, name="p6", exactName="P6", guid="p6", groupBits=16, teamId=1)
        p6.connects('p6')
        time.sleep(2)
        p.teambalance()
        

    #test_swap()
    #test_scramble()
    #test_autoscramble_round()
    #test_autoscramble_map()
    test_teambalancer()
    