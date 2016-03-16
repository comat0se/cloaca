#!/usr/bin/env python

from cloaca.gtr import Game
from cloaca.gamestate import GameState
from cloaca.player import Player
from cloaca.building import Building
from cloaca.zone import Zone
import cloaca.card_manager as cm

import cloaca.message as message
from cloaca.message import BadGameActionError

from cloaca.test.monitor import Monitor
import cloaca.test.test_setup as test_setup

import unittest

class TestThinkerOrLead(unittest.TestCase):
    """ Test handling thinker or lead.
    """

    def setUp(self):
        """ This is run prior to every test.
        """
        self.game = test_setup.simple_two_player()
        self.p1, self.p2 = self.game.game_state.players

    def test_expects_thinker_or_lead(self):
        """ The Game should expect a THINKERORLEAD action.
        """
        self.assertEqual(self.game.expected_action(), message.THINKERORLEAD)

    
    def test_handle_do_thinker(self):
        """ Responding with True should do expect THINKERTYPE response.
        """
        a = message.GameAction(message.THINKERORLEAD, True)
        self.game.handle(a)

        self.assertEqual(self.game.expected_action(), message.THINKERTYPE)


    def test_handle_do_lead(self):
        """ Responding with False should expect LEADROLE response.
        """
        a = message.GameAction(message.THINKERORLEAD, False)
        self.game.handle(a)

        self.assertEqual(self.game.expected_action(), message.LEADROLE)

    def test_thinker_for_cards_many_times(self):
        """ Thinker several times in a row for both players.

        Hands start empty.
        """
        a = message.GameAction(message.THINKERORLEAD, True)
        b = message.GameAction(message.THINKERTYPE, False)

        for i in range(10):
            # Player 1
            self.game.handle(a)
            self.game.handle(b)

            # Player 2
            self.game.handle(a)
            self.game.handle(b)

        self.assertEqual(len(self.game.game_state.players[0].hand), 14)
        self.assertEqual(len(self.game.game_state.players[1].hand), 14)

    def test_thinker_for_jacks_many_times(self):
        """ Thinker several times in a row for both players.

        Three thinkers for Jacks for each player will empty the pile, 
        since hands start empty.
        """
        a = message.GameAction(message.THINKERORLEAD, True)
        b = message.GameAction(message.THINKERTYPE, True)

        for i in range(3):
            # Player 1
            self.game.handle(a)
            self.game.handle(b)

            # Player 2
            self.game.handle(a)
            self.game.handle(b)

        self.assertEqual(len(self.game.game_state.players[0].hand), 3)
        self.assertEqual(len(self.game.game_state.players[1].hand), 3)

    def test_thinker_for_too_many_jacks(self):
        """ Thinker for a Jack with an empty Jack pile

        This bad action should not change anything about the game state.
        """
        a = message.GameAction(message.THINKERORLEAD, True)
        b = message.GameAction(message.THINKERTYPE, True)

        self.game.game_state.jack_pile.set_content([])

        self.game.handle(a)

        # Monitor the gamestate for any changes
        mon = Monitor()
        mon.modified(self.game.game_state)

        # Player 1
        self.game.handle(b)

        self.assertFalse(mon.modified(self.game.game_state))


class TestLeadRole(unittest.TestCase):
    """ Test leading.
    """

    def setUp(self):
        """ This is run prior to every test.
        """
        self.game = test_setup.simple_two_player()
        self.p1, self.p2 = self.game.game_state.players
        
        # Indicate that we want to lead
        a = message.GameAction(message.THINKERORLEAD, False)
        self.game.handle(a)


    def test_handle_lead_role_with_orders(self):
        """ Leading a role sets GameState.role_led, camp actions.
        """
        self.p1.hand.set_content([cm.get_card('Latrine')])

        a = message.GameAction(message.LEADROLE, 'Laborer', 1, 'Latrine')
        self.game.handle(a)

        self.assertEqual(self.game.game_state.role_led, 'Laborer')
        self.assertEqual(self.p1.n_camp_actions, 1)
        self.assertIn('Latrine', self.p1.camp)
        self.assertNotIn('Latrine', self.p1.hand)
        self.assertEqual(self.game.expected_action(), message.FOLLOWROLE)


    def test_handle_lead_latrine_with_jack(self):
        """ Leading a role sets GameState.role_led, camp actions.
        """
        self.p1.hand.set_content([cm.get_card('Jack')])

        a = message.GameAction(message.LEADROLE, 'Laborer', 1, 'Jack')
        self.game.handle(a)

        self.assertEqual(self.game.game_state.role_led, 'Laborer')
        self.assertEqual(self.p1.n_camp_actions, 1)
        self.assertIn('Jack', self.p1.camp)
        self.assertNotIn('Jack', self.p1.hand)
        self.assertEqual(self.game.expected_action(), message.FOLLOWROLE)


class TestFollow(unittest.TestCase):
    """ Test handling following mechanics
    """

    def setUp(self):
        """ This is run prior to every test.
        """
        self.game = test_setup.simple_two_player()
        self.p1, self.p2 = self.game.game_state.players
        
        # Indicate that p1 will lead
        a = message.GameAction(message.THINKERORLEAD, False)
        self.game.handle(a)

        self.p1.hand.set_content([cm.get_card('Jack')])

        # p1 leads Laborer
        a = message.GameAction(message.LEADROLE, 'Laborer', 1, 'Jack')
        self.game.handle(a)


    def test_expects_follow_role(self):
        """ The Game should expect a FOLLOWROLE action.
        """
        self.assertEqual(self.game.expected_action(), message.FOLLOWROLE)

    
    def test_do_thinker(self):
        """ Responding with True should do expect THINKERTYPE response.
        """
        a = message.GameAction(message.FOLLOWROLE, True, 0, None)
        self.game.handle(a)

        self.assertEqual(self.game.expected_action(), message.THINKERTYPE)
        self.assertEqual(self.p2.n_camp_actions, 0)


    def test_follow_role_with_jack(self):
        """ Follow Laborer with a Jack.
        """
        self.p2.hand.set_content([cm.get_card('Jack')])

        a = message.GameAction(message.FOLLOWROLE, False, 1, 'Jack')
        self.game.handle(a)

        self.assertEqual(self.game.expected_action(), message.LABORER)
        self.assertIn('Jack', self.p2.camp)
        self.assertNotIn('Jack', self.p2.hand)
        self.assertEqual(self.p2.n_camp_actions, 1)


    def test_follow_role_with_orders(self):
        """ Follow Laborer with a Latrine.
        """
        self.p2.hand.set_content([cm.get_card('Latrine')])

        a = message.GameAction(message.FOLLOWROLE, False, 1, 'Latrine')
        self.game.handle(a)

        self.assertEqual(self.game.expected_action(), message.LABORER)
        self.assertIn('Latrine', self.p2.camp)
        self.assertNotIn('Latrine', self.p2.hand)
        self.assertEqual(self.p2.n_camp_actions, 1)

    def test_follow_role_with_nonexistent_card(self):
        """Follow Laborer specifying a non-existent card.

        This bad action should not change anything about the game state.
        """
        self.p2.hand.set_content([])
        
        a = message.GameAction(message.FOLLOWROLE, False, 1, 'Latrine')
        
        # Monitor the gamestate for any changes
        mon = Monitor()
        mon.modified(self.game.game_state)
        #print self.game.game_state.__dict__

        #self.game.handle(a)
        #print self.game.game_state.__dict__

        #from copy import deepcopy
        #gs2 = deepcopy(self.game.game_state)
        #print gs2 == self.game.game_state
        #self.assertEqual(self.game.game_state, gs2)

        self.assertFalse(mon.modified(self.game.game_state))

    def test_follow_role_with_card_of_different_role(self):
        """ Follow Laborer specifying a card of the wrong role.

        This bad action should not change anything about the game state.
        """
        self.p2.hand.set_content([cm.get_card('Atrium')])
        
        a = message.GameAction(message.FOLLOWROLE, False, 1, 'Atrium')
        
        # Monitor the gamestate for any changes
        mon = Monitor()
        mon.modified(self.game.game_state)

        self.game.handle(a)

        self.assertFalse(mon.modified(self.game.game_state))

    def test_follow_role_with_petition_of_different_role(self):
        """ Follow Laborer by petition of non-Laborer role cards.
        """
        self.p2.hand.set_content(cm.get_cards(['Atrium', 'School', 'School']))
        
        a = message.GameAction(message.FOLLOWROLE, False, 1, 'Atrium', 'School', 'School')
        
        self.game.handle(a)

        self.assertEqual(self.game.expected_action(), message.LABORER)
        self.assertIn('Atrium', self.p2.camp)
        self.assertEqual(self.p2.camp.count('School'), 2)
        self.assertEqual(len(self.p2.hand), 0)

    def test_follow_role_with_petition_of_same_role(self):
        """ Follow Laborer by petition of Laborer role cards.
        """
        self.p2.hand.set_content(cm.get_cards(['Latrine', 'Insula', 'Insula']))
        
        a = message.GameAction(message.FOLLOWROLE, False, 1, 'Latrine', 'Insula', 'Insula')

        self.game.handle(a)

        self.assertEqual(self.game.expected_action(), message.LABORER)
        self.assertIn('Latrine', self.p2.camp)
        self.assertEqual(self.p2.camp.count('Insula'), 2)
        self.assertEqual(len(self.p2.hand), 0)


    def test_follow_role_with_illegal_petition(self):
        """ Follow Laborer by petition of the wrong number of Laborer cards.

        This bad action should not change anything about the game state.
        """
        self.p2.hand.set_content(cm.get_cards(['Latrine', 'Road', 'Insula']))
        
        a = message.GameAction(message.FOLLOWROLE, False, 1, 'Latrine', 'Insula')

        self.game.handle(a)

        # Monitor the gamestate for any changes
        mon = Monitor()
        mon.modified(self.game.game_state)

        self.game.handle(a)

        self.assertFalse(mon.modified(self.game.game_state))


if __name__ == '__main__':
    unittest.main()
