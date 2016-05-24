#!/usr/bin/env python

from cloaca.game import Game
from cloaca.player import Player
from cloaca.building import Building
from cloaca.error import GTRError

import cloaca.card_manager as cm

import cloaca.message as message

from cloaca.test.monitor import Monitor
import cloaca.test.test_setup as test_setup
from cloaca.test.test_setup import TestDeck

import unittest

class TestMultiLegionary(unittest.TestCase):
    """Test handling legionary responses with multiple legionary
    actions.
    """

    def setUp(self):
        self.deck = TestDeck()
        d = self.deck

        self.game = test_setup.two_player_lead('Legionary',
                clientele=[['Atrium'],[]],
                deck = d)

        self.p1, self.p2 = self.game.players


    def test_opponent_has_some_match(self):
        """Demand cards that opponent has only some of.
        """
        d = self.deck
        self.p1.hand.set_content([d.atrium0, d.shrine0])
        self.p2.hand.set_content([d.foundry0])

        self.assertEqual(self.game.legionary_count, 2)

        a = message.GameAction(message.LEGIONARY, d.atrium0, d.shrine0)
        self.game.handle(a)

        a = message.GameAction(message.GIVECARDS, d.foundry0)
        self.game.handle(a)

        self.assertNotIn(d.foundry0, self.p2.hand)
        self.assertIn(d.foundry0, self.p1.stockpile)
        self.assertEqual(len(self.p2.hand), 0)

        # It should be p2's turn now
        self.assertEqual(self.game.expected_action, message.THINKERORLEAD)


    def test_demand_more_than_allowed(self):
        """Demand more cards than p1 has legionary actions.
        """
        d = self.deck
        self.p1.hand.set_content([d.atrium0, d.shrine0, d.road0])
        self.p2.hand.set_content([d.foundry0])

        self.assertEqual(self.game.legionary_count, 2)

        mon = Monitor()
        mon.modified(self.game)

        a = message.GameAction(message.LEGIONARY, d.atrium0, d.shrine0, d.road0)

        with self.assertRaises(GTRError):
            self.game.handle(a)

        self.assertFalse(mon.modified(self.game))


class TestLegionary(unittest.TestCase):

    def setUp(self):
        """This is run prior to every test.
        """
        self.deck = TestDeck()
        self.game = test_setup.two_player_lead('Legionary')
        self.p1, self.p2 = self.game.players


    def test_expects_legionary(self):
        """The Game should expect a LEGIONARY action.
        """
        self.assertEqual(self.game.expected_action, message.LEGIONARY)


    def test_legionary(self):
        """Take one card from the pool with legionary action.
        """
        d = self.deck
        self.p1.hand.set_content([d.atrium0])
        self.game.pool.set_content([d.foundry0])

        a = message.GameAction(message.LEGIONARY, d.atrium0)
        self.game.handle(a)

        self.assertNotIn(d.foundry0, self.game.pool)
        self.assertIn(d.foundry0, self.p1.stockpile)

        self.assertIn(d.atrium0, self.p1.revealed) 

        self.assertEqual(self.game.expected_action, message.GIVECARDS)


    def test_give_cards(self):
        """Take one card from opponent.
        """
        d = self.deck
        self.p1.hand.set_content([d.atrium0])
        self.p2.hand.set_content([d.foundry0])

        a = message.GameAction(message.LEGIONARY, d.atrium0)
        self.game.handle(a)

        a = message.GameAction(message.GIVECARDS, d.foundry0)
        self.game.handle(a)

        self.assertIn(d.foundry0, self.p1.stockpile)
        self.assertNotIn(d.foundry0, self.p2.hand)

        # It should be p2's turn now
        self.assertEqual(self.game.expected_action, message.THINKERORLEAD)


    def test_illegal_give_cards(self):
        """A GIVECARDS action with too few cards will raise GTRError.
        """
        d = self.deck

        self.p1.hand.set_content([d.atrium0])
        self.p2.hand.set_content([d.foundry0])

        a = message.GameAction(message.LEGIONARY, d.atrium0)
        self.game.handle(a)

        a = message.GameAction(message.GIVECARDS)

        mon = Monitor()
        mon.modified(self.game)

        with self.assertRaises(GTRError):
            self.game.handle(a)

        self.assertFalse(mon.modified(self.game))


    def test_opponent_has_no_match(self):
        """Demand card that opponent doesn't have.
        """
        d = self.deck
        self.p1.hand.set_content([d.atrium0])
        self.p2.hand.set_content([d.latrine0])

        a = message.GameAction(message.LEGIONARY, d.atrium0)
        self.game.handle(a)

        a = message.GameAction(message.GIVECARDS)
        self.game.handle(a)

        self.assertNotIn(d.latrine0, self.p1.stockpile)
        self.assertIn(d.latrine0, self.p2.hand)

        # It should be p2's turn now
        self.assertEqual(self.game.expected_action, message.THINKERORLEAD)


    def test_demand_jack(self):
        """Demand Jack illegally. This should not change the game state.
        """
        d = self.deck
        self.p1.hand.set_content([d.atrium0, d.jack1])
        self.p2.hand.set_content([d.latrine0])

        mon = Monitor()
        mon.modified(self.game)

        a = message.GameAction(message.LEGIONARY, d.jack1)
        with self.assertRaises(GTRError):
            self.game.handle(a)

        self.assertFalse(mon.modified(self.game))


    def test_demand_non_existent_card(self):
        """Demand card that we don't have.
        """
        d = self.deck
        self.p1.hand.set_content([d.atrium0])

        mon = Monitor()
        mon.modified(self.game)

        a = message.GameAction(message.LEGIONARY, d.latrine0)
        with self.assertRaises(GTRError):
            self.game.handle(a)

        self.assertFalse(mon.modified(self.game))


class TestLegionaryPalisade(unittest.TestCase):
    """The Palisade allows you to not give cards with legionary.
    You still may.
    """

    def setUp(self):
        self.deck = TestDeck()
        d = self.deck

        self.game = test_setup.two_player_lead('Legionary',
                buildings=[[],['Palisade']],
                deck = self.deck)

        self.p1, self.p2 = self.game.players

        self.p1.hand.set_content([d.road0])
        self.game.pool.set_content([d.insula0])

        self.p2.hand.set_content([d.bar0])

        a = message.GameAction(message.LEGIONARY, d.road0)
        self.game.handle(a)


    def test_legionary_palisade(self):
        """Palisade makes p2 immune, but a GIVECARDS action is still
        necessary, since it's an option to lose cards even if immune
        to Legionary.
        """
        d = self.deck

        self.assertEqual(self.game.expected_action, message.GIVECARDS)

        a = message.GameAction(message.GIVECARDS)
        self.game.handle(a)

        self.assertIn(d.bar0, self.p2.hand)
        self.assertIn(d.insula0, self.p1.stockpile)


    def test_legionary_palisade_give_cards_anyway(self):
        d = self.deck

        self.assertEqual(self.game.expected_action, message.GIVECARDS)

        a = message.GameAction(message.GIVECARDS, d.bar0)
        self.game.handle(a)

        self.assertIn(d.bar0, self.p1.stockpile)
        self.assertIn(d.insula0, self.p1.stockpile)


class TestLegionaryWall(unittest.TestCase):
    """Tests the Wall for immunity to legionary, not for interaction with
    Bridge and not for the extra points from the stockpile.

    It is allowed to give cards even if you are immune with a Wall.
    """

    def setUp(self):
        self.deck = TestDeck()
        d = self.deck

        self.game = test_setup.two_player_lead('Legionary',
                buildings=[[],['Wall']],
                deck = self.deck)

        self.p1, self.p2 = self.game.players

        self.p1.hand.set_content([d.road0])
        self.game.pool.set_content([d.insula0])

        self.p2.hand.set_content([d.bar0])

        a = message.GameAction(message.LEGIONARY, d.road0)
        self.game.handle(a)


    def test_legionary_wall(self):
        """Wall makes p2 immune.
        """
        d = self.deck

        self.assertEqual(self.game.expected_action, message.GIVECARDS)

        a = message.GameAction(message.GIVECARDS)
        self.game.handle(a)

        self.assertIn(d.bar0, self.p2.hand)
        self.assertIn(d.insula0, self.p1.stockpile)


    def test_legionary_wall_give_cards_anyway(self):
        """Wall makes p2 immune, but p2 chooses to give cards in hand.
        """
        d = self.deck

        self.assertEqual(self.game.expected_action, message.GIVECARDS)

        a = message.GameAction(message.GIVECARDS, d.bar0)
        self.game.handle(a)

        self.assertIn(d.bar0, self.p1.stockpile)
        self.assertIn(d.insula0, self.p1.stockpile)


class TestLegionaryBridgePalisade(unittest.TestCase):
    """Test taking cards with the Bridge. The GIVECARDS action only
    specifies which cards to give from the player's hand. Cards
    from the stockpile are taken automatically.
    """

    def setUp(self):
        self.deck = TestDeck()
        d = self.deck

        self.game = test_setup.two_player_lead('Legionary',
                buildings=[['Bridge'],['Palisade']],
                deck = self.deck)

        self.p1, self.p2 = self.game.players


    def test_bridge_over_palisade(self):
        """Palisade does nothing in the face of a Bridge.
        """
        d = self.deck

        self.p1.hand.set_content([d.road0])

        self.p2.hand.set_content([d.bar0])
        self.p2.stockpile.set_content([d.latrine0])

        self.game.pool.set_content([d.insula0])

        a = message.GameAction(message.LEGIONARY, d.road0)
        self.game.handle(a)

        self.assertEqual(self.game.expected_action, message.GIVECARDS)

        a = message.GameAction(message.GIVECARDS, d.bar0)
        self.game.handle(a)

        self.assertIn(d.bar0, self.p1.stockpile)
        self.assertIn(d.insula0, self.p1.stockpile)
        self.assertIn(d.latrine0, self.p1.stockpile)


    def test_bridge_multiple_choices(self):
        """Bridge takes a card from stockpile. It doesn't matter which
        one if there's a choice.
        """
        d = self.deck

        self.p1.hand.set_content([d.road0])

        self.p2.stockpile.set_content([d.latrine0, d.road1])

        a = message.GameAction(message.LEGIONARY, d.road0)
        self.game.handle(a)

        self.assertEqual(self.game.expected_action, message.GIVECARDS)

        a = message.GameAction(message.GIVECARDS)
        self.game.handle(a)

        self.assertTrue(d.latrine0 in self.p1.stockpile or d.road1 in self.p1.stockpile)
        self.assertTrue(d.latrine0 in self.p2.stockpile or d.road1 in self.p2.stockpile)


class TestLegionaryBridgeWall(unittest.TestCase):
    """Tests the Wall for immunity to legionary even with a Bridge.
    Does not test for extra points with Wall.
    """

    def setUp(self):
        self.deck = TestDeck()
        d = self.deck

        self.game = test_setup.two_player_lead('Legionary',
                buildings=[['Bridge'],['Wall']],
                deck = self.deck)

        self.p1, self.p2 = self.game.players

        self.p1.hand.set_content([d.road0])
        self.game.pool.set_content([d.insula0])

        self.p2.hand.set_content([d.bar0])
        self.p2.stockpile.set_content([d.bar1])

        a = message.GameAction(message.LEGIONARY, d.road0)
        self.game.handle(a)


    def test_legionary_bridge_wall(self):
        """Wall makes p2 immune.
        """
        d = self.deck

        self.assertEqual(self.game.expected_action, message.GIVECARDS)

        a = message.GameAction(message.GIVECARDS)
        self.game.handle(a)

        self.assertIn(d.bar0, self.p2.hand)
        self.assertIn(d.insula0, self.p1.stockpile)


    def test_legionary_bridge_wall_give_cards_anyway(self):
        """Wall makes p2 immune, but p2 gives cards anyway,
        including from stockpile.
        """
        d = self.deck

        self.assertEqual(self.game.expected_action, message.GIVECARDS)

        a = message.GameAction(message.GIVECARDS, d.bar0, d.bar1)
        self.game.handle(a)

        self.assertIn(d.bar0, self.p1.stockpile)
        self.assertIn(d.insula0, self.p1.stockpile)


class TestLegionaryColiseum(unittest.TestCase):
    """Test taking cards with the Coliseum.
    """

    def setUp(self):
        self.deck = TestDeck()
        d = self.deck

        self.game = test_setup.two_player_lead('Legionary',
                buildings=[['Coliseum'],[]],
                deck = self.deck)

        self.p1, self.p2 = self.game.players


    def test_coliseum_client(self):
        """Palisade does nothing in the face of a Bridge.
        """
        d = self.deck

        self.p1.hand.set_content([d.road0])

        self.p2.hand.set_content([d.bar0])
        self.p2.clientele.set_content([d.latrine0])

        a = message.GameAction(message.LEGIONARY, d.road0)
        self.game.handle(a)

        self.assertEqual(self.game.expected_action, message.GIVECARDS)

        a = message.GameAction(message.GIVECARDS, d.bar0)
        self.game.handle(a)

        self.assertIn(d.bar0, self.p1.stockpile)
        self.assertIn(d.latrine0, self.p1.vault)


    def test_coliseum_multiple_choices(self):
        """Coliseum takes a card from clientele. It doesn't matter which
        one if there's a choice.
        """
        d = self.deck

        self.p1.hand.set_content([d.road0])

        self.p2.clientele.set_content([d.latrine0, d.road1])

        a = message.GameAction(message.LEGIONARY, d.road0)
        self.game.handle(a)

        self.assertEqual(self.game.expected_action, message.GIVECARDS)

        a = message.GameAction(message.GIVECARDS)
        self.game.handle(a)

        self.assertTrue(d.latrine0 in self.p1.vault or d.road1 in self.p1.vault)
        self.assertTrue(d.latrine0 in self.p2.clientele or d.road1 in self.p2.clientele)

    
if __name__ == '__main__':
    unittest.main()
