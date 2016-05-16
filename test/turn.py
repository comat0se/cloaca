#!/usr/bin/env python

from cloaca.game import Game
from cloaca.player import Player
from cloaca.building import Building
from cloaca.zone import Zone
import cloaca.card_manager as cm

import cloaca.message as message
from cloaca.message import GameActionError

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
        self.p1, self.p2 = self.game.players

    def test_expects_thinker_or_lead(self):
        """ The Game should expect a THINKERORLEAD action.
        """
        self.assertEqual(self.game.expected_action, message.THINKERORLEAD)

    
    def test_handle_do_thinker(self):
        """ Responding with True should do expect THINKERTYPE response.
        """
        a = message.GameAction(message.THINKERORLEAD, True)
        self.game.handle(a)

        self.assertEqual(self.game.expected_action, message.THINKERTYPE)


    def test_handle_do_lead(self):
        """ Responding with False should expect LEADROLE response.
        """
        a = message.GameAction(message.THINKERORLEAD, False)
        self.game.handle(a)

        self.assertEqual(self.game.expected_action, message.LEADROLE)

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

        self.assertEqual(len(self.game.players[0].hand), 14)
        self.assertEqual(len(self.game.players[1].hand), 14)

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

        self.assertEqual(len(self.game.players[0].hand), 3)
        self.assertEqual(len(self.game.players[1].hand), 3)

    def test_thinker_for_too_many_jacks(self):
        """ Thinker for a Jack with an empty Jack pile

        This bad action should not change anything about the game state.
        """
        a = message.GameAction(message.THINKERORLEAD, True)
        b = message.GameAction(message.THINKERTYPE, True)

        self.game.jacks.set_content([])

        self.game.handle(a)

        # Monitor the gamestate for any changes
        mon = Monitor()
        mon.modified(self.game)

        # Player 1
        self.game.handle(b)

        self.assertFalse(mon.modified(self.game))


class TestLeadRole(unittest.TestCase):
    """ Test leading.
    """

    def setUp(self):
        """ This is run prior to every test.
        """
        self.game = test_setup.simple_two_player()
        self.p1, self.p2 = self.game.players
        
        # Indicate that we want to lead
        a = message.GameAction(message.THINKERORLEAD, False)
        self.game.handle(a)


    def test_handle_lead_role_with_orders(self):
        """ Leading a role sets GameState.role_led, camp actions.
        """
        latrine = cm.get_card('Latrine')
        self.p1.hand.set_content([latrine])

        a = message.GameAction(message.LEADROLE, 'Laborer', 1, latrine)
        self.game.handle(a)

        self.assertEqual(self.game.role_led, 'Laborer')
        self.assertEqual(self.p1.n_camp_actions, 1)
        self.assertIn(latrine, self.p1.camp)
        self.assertNotIn(latrine, self.p1.hand)
        self.assertEqual(self.game.expected_action, message.FOLLOWROLE)


    def test_handle_lead_latrine_with_jack(self):
        """ Leading a role sets GameState.role_led, camp actions.
        """
        jack = cm.get_card('Jack')

        self.p1.hand.set_content([jack])

        a = message.GameAction(message.LEADROLE, 'Laborer', 1, jack)
        self.game.handle(a)

        self.assertEqual(self.game.role_led, 'Laborer')
        self.assertEqual(self.p1.n_camp_actions, 1)
        self.assertIn(jack, self.p1.camp)
        self.assertNotIn(jack, self.p1.hand)
        self.assertEqual(self.game.expected_action, message.FOLLOWROLE)


    def test_petition(self):
        """Tests petition with 3 orders cards.
        """
        cards = cm.get_cards(['Road']*3)
        self.p1.hand.set_content(cards)

        a = message.GameAction(message.LEADROLE, 'Craftsman', 1, *cards)
        self.game.handle(a)

        self.assertEqual(self.game.role_led, 'Craftsman')
        self.assertEqual(self.p1.n_camp_actions, 1)
        self.assertTrue(self.p1.camp.contains(cards))
        self.assertNotIn('Road', self.p1.hand)
        self.assertEqual(self.game.expected_action, message.FOLLOWROLE)


    def test_petition_for_same_role(self):
        """Tests petition with 3 orders cards that match the role
        selected for the Petition. eg. 3 Road cards to Petition for Laborer.
        """
        cards = cm.get_cards(['Road']*3)
        self.p1.hand.set_content(cards)

        a = message.GameAction(message.LEADROLE, 'Laborer', 1, *cards)
        self.game.handle(a)

        self.assertEqual(self.game.role_led, 'Laborer')
        self.assertEqual(self.p1.n_camp_actions, 1)
        self.assertTrue(self.p1.camp.contains(cards))
        self.assertNotIn('Road', self.p1.hand)
        self.assertEqual(self.game.expected_action, message.FOLLOWROLE)


    def test_petition_with_circus_and_two_cards(self):
        """Tests petition with 2 orders cards using a Circus.
        """
        circus, dock = cm.get_cards(['Circus', 'Dock'])
        self.p1.buildings = [Building(circus, 'Wood', materials=[dock], complete=True)]

        cards = cm.get_cards(['Road']*2)
        self.p1.hand.set_content(cards)

        a = message.GameAction(message.LEADROLE, 'Craftsman', 1, *cards)
        self.game.handle(a)

        self.assertEqual(self.game.role_led, 'Craftsman')
        self.assertEqual(self.p1.n_camp_actions, 1)
        self.assertTrue(self.p1.camp.contains(cards))
        self.assertNotIn('Road', self.p1.hand)
        self.assertEqual(self.game.expected_action, message.FOLLOWROLE)


    def test_petition_with_circus_and_three_cards(self):
        """Tests petition with 3 orders cards despiting having a Circus.
        """
        circus, dock = cm.get_cards(['Circus', 'Dock'])
        self.p1.buildings = [Building(circus, 'Wood', materials=[dock], complete=True)]

        cards = cm.get_cards(['Road']*3)
        self.p1.hand.set_content(cards)

        a = message.GameAction(message.LEADROLE, 'Craftsman', 1, *cards)
        self.game.handle(a)

        self.assertEqual(self.game.role_led, 'Craftsman')
        self.assertEqual(self.p1.n_camp_actions, 1)
        self.assertTrue(self.p1.camp.contains(cards))
        self.assertNotIn('Road', self.p1.hand)
        self.assertEqual(self.game.expected_action, message.FOLLOWROLE)


    def test_petition_with_too_few_cards(self):
        """Tests petition with 2 orders cards without a circus. This illegal
        action should leave the game state unchanged.
        """
        cards = cm.get_cards(['Road']*2)
        self.p1.hand.set_content(cards)

        mon = Monitor()
        mon.modified(self.game)

        a = message.GameAction(message.LEADROLE, 'Craftsman', 1, *cards)
        self.game.handle(a)

        self.assertFalse(mon.modified(self.game))


    def test_petition_with_nonmatching_cards(self):
        """Tests petition with 3 orders cards of different roles. This illegal
        action should leave the game state unchanged.
        """
        cards = cm.get_cards(['Road', 'Insula', 'Atrium'])
        self.p1.hand.set_content(cards)

        mon = Monitor()
        mon.modified(self.game)

        a = message.GameAction(message.LEADROLE, 'Craftsman', 1, *cards)
        self.game.handle(a)

        self.assertFalse(mon.modified(self.game))


    def test_petition_with_too_many_cards(self):
        """Tests petition with 4 orders cards. This illegal
        action should leave the game state unchanged.
        """
        cards = cm.get_cards(['Road', 'Insula', 'Road', 'Road'])
        self.p1.hand.set_content(cards)

        mon = Monitor()
        mon.modified(self.game)

        a = message.GameAction(message.LEADROLE, 'Craftsman', 1, *cards)
        self.game.handle(a)

        self.assertFalse(mon.modified(self.game))


    def test_petition_with_nonexistent_cards(self):
        """Tests petition with cards not in players hand. This illegal
        action should leave the game state unchanged.
        """
        cards = cm.get_cards(['Road', 'Road', 'Road'])
        #self.p1.hand.set_content(cards)

        mon = Monitor()
        mon.modified(self.game)

        a = message.GameAction(message.LEADROLE, 'Craftsman', 1, *cards)
        self.game.handle(a)

        self.assertFalse(mon.modified(self.game))

class TestPalace(unittest.TestCase):
    """Test leading multiple actions with Palace.
    """

    def setUp(self):
        """ This is run prior to every test.
        """
        self.game = test_setup.simple_two_player()
        self.p1, self.p2 = self.game.players

        palace, statue = cm.get_cards(['Palace', 'Statue'])
        self.p1.buildings = [Building(palace, 'Marble', materials=[statue], complete=True)]
        
        # Indicate that we want to lead
        a = message.GameAction(message.THINKERORLEAD, False)
        self.game.handle(a)

    def test_petition_with_palace_3_actions(self):
        """Tests petition with multiple lead actions using Palace.

        Using 6 Docks and 3 Roads allows 3, 5, or 7 actions.
        """
        cards = cm.get_cards(['Road']*3 + ['Dock']*6)
        self.p1.hand.set_content(cards)

        n_actions = 3
        a = message.GameAction(message.LEADROLE, 'Craftsman', n_actions, *cards)
        self.game.handle(a)

        self.assertEqual(self.game.role_led, 'Craftsman')
        self.assertEqual(self.p1.n_camp_actions, n_actions)
        self.assertTrue(self.p1.camp.contains(cards))
        self.assertFalse(self.p1.hand.contains(['Road','Dock']))
        self.assertEqual(self.game.expected_action, message.FOLLOWROLE)

    def test_petition_with_palace_5_actions(self):
        """Tests petition with multiple lead actions using Palace.

        Using 6 Docks and 3 Roads allows 3, 5, or 7 actions.
        """
        cards = cm.get_cards(['Road']*3 + ['Dock']*6)
        self.p1.hand.set_content(cards)

        n_actions = 5
        a = message.GameAction(message.LEADROLE, 'Craftsman', n_actions, *cards)
        self.game.handle(a)

        self.assertEqual(self.game.role_led, 'Craftsman')
        self.assertEqual(self.p1.n_camp_actions, n_actions)
        self.assertTrue(self.p1.camp.contains(cards))
        self.assertFalse(self.p1.hand.contains(['Road','Dock']))
        self.assertEqual(self.game.expected_action, message.FOLLOWROLE)

    def test_petition_with_palace_7_actions(self):
        """Tests petition with multiple lead actions using Palace.

        Using 6 Docks and 3 Roads allows 3, 5, or 7 actions.
        """
        cards = cm.get_cards(['Road']*3 + ['Dock']*6)
        self.p1.hand.set_content(cards)

        n_actions = 7
        a = message.GameAction(message.LEADROLE, 'Craftsman', n_actions, *cards)
        self.game.handle(a)

        self.assertEqual(self.game.role_led, 'Craftsman')
        self.assertEqual(self.p1.n_camp_actions, n_actions)
        self.assertTrue(self.p1.camp.contains(cards))
        self.assertFalse(self.p1.hand.contains(['Road','Dock']))
        self.assertEqual(self.game.expected_action, message.FOLLOWROLE)

    def test_petition_with_illegal_n_actions(self):
        """Tests petition with multiple lead actions using Palace.

        Using 6 Docks and 3 Roads allows 3, 5, or 7 actions.
        """
        cards = cm.get_cards(['Road']*3 + ['Dock']*6)
        self.p1.hand.set_content(cards)

        n_actions = 6

        mon = Monitor()
        mon.modified(self.game)

        a = message.GameAction(message.LEADROLE, 'Craftsman', n_actions, *cards)
        self.game.handle(a)

        self.assertFalse(mon.modified(self.game))


    def test_petition_with_illegal_petition_size(self):
        """Tests petition with multiple lead actions using Palace.

        Using 6 Docks and 3 Roads allows 3, 5, or 7 actions.
        """
        cards = cm.get_cards(['Road']*3 + ['Dock']*4)
        self.p1.hand.set_content(cards)

        mon = Monitor()
        mon.modified(self.game)

        a = message.GameAction(message.LEADROLE, 'Craftsman', 1, *cards)
        self.game.handle(a)

        self.assertFalse(mon.modified(self.game))

        a = message.GameAction(message.LEADROLE, 'Craftsman', 2, *cards)
        self.game.handle(a)

        self.assertFalse(mon.modified(self.game))

        a = message.GameAction(message.LEADROLE, 'Craftsman', 4, *cards)
        self.game.handle(a)

        self.assertFalse(mon.modified(self.game))


class TestFollow(unittest.TestCase):
    """ Test handling following mechanics
    """

    def setUp(self):
        """ This is run prior to every test.
        """
        self.game = test_setup.simple_two_player()
        self.p1, self.p2 = self.game.players
        
        # Indicate that p1 will lead
        a = message.GameAction(message.THINKERORLEAD, False)
        self.game.handle(a)

        jack = cm.get_card('Jack')
        self.p1.hand.set_content([jack])

        # p1 leads Laborer
        a = message.GameAction(message.LEADROLE, 'Laborer', 1, jack)
        self.game.handle(a)


    def test_expects_follow_role(self):
        """ The Game should expect a FOLLOWROLE action.
        """
        self.assertEqual(self.game.expected_action, message.FOLLOWROLE)

    
    def test_do_thinker(self):
        """ Responding with True should do expect THINKERTYPE response.
        """
        a = message.GameAction(message.FOLLOWROLE, True, 0, None)
        self.game.handle(a)

        self.assertEqual(self.game.expected_action, message.THINKERTYPE)
        self.assertEqual(self.p2.n_camp_actions, 0)


    def test_follow_role_with_jack(self):
        """ Follow Laborer with a Jack.
        """
        jack = cm.get_card('Jack')
        self.p2.hand.set_content([jack])

        a = message.GameAction(message.FOLLOWROLE, False, 1, jack)
        self.game.handle(a)

        self.assertEqual(self.game.expected_action, message.LABORER)
        self.assertIn(jack, self.p2.camp)
        self.assertNotIn(jack, self.p2.hand)
        self.assertEqual(self.p2.n_camp_actions, 1)


    def test_follow_role_with_orders(self):
        """ Follow Laborer with a Latrine.
        """
        latrine = cm.get_card('Latrine')
        self.p2.hand.set_content([latrine])

        a = message.GameAction(message.FOLLOWROLE, False, 1, latrine)
        self.game.handle(a)

        self.assertEqual(self.game.expected_action, message.LABORER)
        self.assertIn(latrine, self.p2.camp)
        self.assertNotIn(latrine, self.p2.hand)
        self.assertEqual(self.p2.n_camp_actions, 1)

    def test_follow_role_with_nonexistent_card(self):
        """Follow Laborer specifying a non-existent card.

        This bad action should not change anything about the game state.
        """
        latrine = cm.get_card('Latrine')
        self.p2.hand.set_content([])
        
        a = message.GameAction(message.FOLLOWROLE, False, 1, latrine)
        
        # Monitor the gamestate for any changes
        mon = Monitor()
        mon.modified(self.game)

        self.assertFalse(mon.modified(self.game))

    def test_follow_role_with_card_of_different_role(self):
        """ Follow Laborer specifying a card of the wrong role.

        This bad action should not change anything about the game state.
        """
        atrium = cm.get_card('Atrium')
        self.p2.hand.set_content([atrium])
        
        a = message.GameAction(message.FOLLOWROLE, False, 1, atrium)
        
        # Monitor the gamestate for any changes
        mon = Monitor()
        mon.modified(self.game)

        self.game.handle(a)

        self.assertFalse(mon.modified(self.game))

    def test_follow_role_with_petition_of_different_role(self):
        """ Follow Laborer by petition of non-Laborer role cards.
        """
        cards = atrium, school1, school2 = cm.get_cards(['Atrium', 'School', 'School'])
        self.p2.hand.set_content(cards)
        
        a = message.GameAction(message.FOLLOWROLE, False, 1, *cards)
        
        self.game.handle(a)

        self.assertEqual(self.game.expected_action, message.LABORER)
        self.assertIn(atrium, self.p2.camp)
        self.assertIn(school1, self.p2.camp)
        self.assertIn(school2, self.p2.camp)
        self.assertEqual(self.p2.camp.count('School'), 2)
        self.assertEqual(len(self.p2.hand), 0)

    def test_follow_role_with_petition_of_same_role(self):
        """ Follow Laborer by petition of Laborer role cards.
        """
        cards = latrine, insula1, insula2 = cm.get_cards(['Latrine', 'Insula', 'Insula'])
        self.p2.hand.set_content(cards)
        
        a = message.GameAction(message.FOLLOWROLE, False, 1, *cards)

        self.game.handle(a)

        self.assertEqual(self.game.expected_action, message.LABORER)
        self.assertIn(latrine, self.p2.camp)
        self.assertIn(insula1, self.p2.camp)
        self.assertIn(insula2, self.p2.camp)
        self.assertEqual(self.p2.camp.count('Insula'), 2)
        self.assertEqual(len(self.p2.hand), 0)


    def test_follow_role_with_illegal_petition(self):
        """ Follow Laborer by petition of the wrong number of Laborer cards.

        This bad action should not change anything about the game state.
        """
        cards = latrine, road, insula = cm.get_cards(['Latrine', 'Road', 'Insula'])
        self.p2.hand.set_content(cards)
        
        a = message.GameAction(message.FOLLOWROLE, False, 1, latrine, insula)

        self.game.handle(a)

        # Monitor the gamestate for any changes
        mon = Monitor()
        mon.modified(self.game)

        self.game.handle(a)

        self.assertFalse(mon.modified(self.game))


if __name__ == '__main__':
    unittest.main()
