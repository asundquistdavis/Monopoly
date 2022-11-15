import csv
import random as r

class Game():

    path = 'Resources'

    def __init__(self, *players, deck='mon_us_original_cards.csv', properties_deck='mon_us_original_properties.csv') -> None:
        self.players = list(players)
        self.deck = deck
        self.properties_deck = properties_deck
        self.cc_cards = []
        self.ch_cards = []
        self.properties = []
        self.make_cards()
        self.make_properties()
        self.setup()

    def setup(self):
        for player in self.players:
            player.money = 1500
            player.game = self

    def make_cards(self):
        with open(f'{Game.path}/{self.deck}') as file:
            file.readline()
            for row in csv.reader(file):
                # print(row)
                card = Card(*row)
                if row[1] == 'cc':
                    self.cc_cards.append(card)
                else:
                    self.ch_cards.append(card)
        r.shuffle(self.cc_cards)
        r.shuffle(self.ch_cards)

    def make_properties(self):
        with open(f'{Game.path}/{self.properties_deck}') as file:
            file.readline()
            for row in csv.reader(file):
                self.properties.append(Property(*row[:11], game=self))
        self.properties.sort(key=lambda p:p.position)

    def property_at(self, position):
        return list(filter(lambda property: property.position == position, self.properties))[0]

    def play_round(self):
        for player in self.players:
            player.play_turn()
            
    def roll(self):
        # output int from two d-6 die rolls
        die = [1, 2, 3, 4, 5, 6]
        die_1 = r.choice(die)
        die_2 = r.choice(die)
        print(f"{'Doubles! ' if die_1 == die_2 else ''}Rolled: {die_1} and {die_2}")
        return (die_1+die_2, die_1==die_2)

    def purchase(self, property):
        # player adds property to their list of properties and pays for propety
        pass

    def property_named(self, property_name):
        properties = list(filter(lambda property: property.name == property_name, self.properties))
        if len(properties) > 0:
            return properties[0]
        else:
            return None

class Player():

    def __init__(self) -> None:
        self.money = 0
        self.position = 0
        self.properties = []
        self.in_jail = False
        self.game = None
        self.houses = 0
        self.hotels = 0
        self.gojfs = 0
        self.turns_in_jail = 0
        self.num_of_doubles = 0

    def assets(self):
        property_value = sum(property.price for property in self.properties)/2
        return self.money + property_value

    def mrtg_asset(self):
        print(f"{self.name}'s balance is {self.money}. Select a property to mortgage:")
        for property in self.properties:
            print(f'{property.name} for {property.price/2}')
        property_name = input()
        if str(property_name) in [str(property.name) for property in self.properties]:
            property = self.game.property_named(property_name)
            property.mrtg = True
            self. exchange_money(property.price/2)
            return 'mrtg'
        else:
            print('Thats not a property you own. Try again')
            self.mrtg_asset()

    def move(self, distance, relative=True, collect_on_go=True):
        # move self 'distance' number of spaces 
        # if target==True, moves to space # 'distance' instead
        x = self.position
        if relative:
            y = x + distance - 40
            self.position = y % 40
        else:
            y = x - distance
            self.position = distance
        if collect_on_go and y > 0:
            self.exchange_money(200)

    def exchange_money(self, amount, player=None):
        # self looses/gains 'amount' of money if amount is (-)/(+)
        # 'player' gains/looses 'amount' of money if amount is (-)/(+)
        # if source is None money goes to bank 
        self.money += int(amount)
        if player != None:
            player.money -= int(amount)

    def draw(self, deck):
        # draw card from deck: either 'ch' or 'cc'
        # self performs action
        card = deck[0]
        deck.append(card)
        deck.pop(0)
        print(card.description)
        if card.function == 'move':
            if card.flag in ['d', 't']:
                value = min((x - int(self.position)) % 40 for x in list(card.value_1))
            else:
                value = int(card.value_1)
            self.move(value, relative=(True if card.flag=='r' else False), collect_on_go=(True if card.flag=='g' else False))
            property = self.game.property_at(self.position)
            property.action(self)
        elif card.function == 'money':
            if card.flag == 'p':
                for player in self.game.players:
                    value = card.value_1
                    self.exchange_money(value, player=player)
            elif card.flag == 'b':
                value = int(card.value_1)*self.houses + int(card.value_2)*self.hotels
            else:
                value = card.value_1
            self.exchange_money(value)
        elif card.function == 'gojf':
            self.gojfs += 1
        else:
            return None

    def play_turn(self):
        # roll dice
        roll = self.game.roll()
        if self.in_jail:
            if not roll[1]:
                if self.gojfs != 0:
                    self.gojfs -= 1
                elif self.turns_in_jail < 2:
                    self.turns_in_jail += 1
                    return 'jail'
                else:
                    self.exchange_money(-50)
                self.turns_in_jail = 0
                self.in_jail = False
        # move player
        self.move(roll[0])
        # get property player is at
        property = self.game.property_at(self.position)
        # get the base type of action performed at this property
        property.action(self)
        # if player.money is negative, have player mrtg properties until money is not negative.
        if self.money < 0 and self.assets() > 0:
            while self.money < 0:
                self.mrtg_asset()
        elif self.money < 0:
            # bankruptcy
            pass
        if roll[1]:
            self.num_of_doubles += 1
                

            # @todo player can purchase houses/hotels at this point

    def status(self):
        return f'{self.name} @ {self.position} has {self.money}M with {self.properties}\n'
        
    def __repr__(self):
        return f'{self.name} is a{"n" if self.type.lower()[0] in "aeiou" else ""} {self.type}'

class AI(Player):

    num_of_AI = 0
    default_name = f'AI#{num_of_AI}'

    def __init__(self, name=default_name, purchasing_logic='greedy') -> None:
        super().__init__()
        self.type = 'ai'
        self.purchasing_logic = purchasing_logic
        self.name = name
        AI.num_of_AI += 1

    def greedy(self, property):
        return 'y'

    call_logic = {'greedy': greedy}

    def will_purchase(self, property) -> str:
        return AI.call_logic[self.purchasing_logic](self, property)

class Human(Player):

    def __init__(self, name) -> None:
        super().__init__()
        self.type = 'human'
        self.name = name

    def will_purchase(self, property) -> str:
        return input(f'{property.name} is for sale and costs {property.price}M. You have {self.money}M. Would you like to purchase it? [y]es or [n]o: ')

class Property():
    
    def __init__(self, name, position, price, type, house_price, rent_0, rent_1, rent_2, rent_3, rent_4, rent_5, game=None) -> None:
        self.name = name
        self. position = int(position)
        self.price = int(price)
        self.type = type
        self.house_price = int(house_price)
        self.rent_0 = int(rent_0)
        self.rent_1 = int(rent_1)
        self.rent_2 = int(rent_2)
        self.rent_3 = int(rent_3)
        self.rent_4 = int(rent_4)
        self.rent_5 = int(rent_5)
        self.owner = None
        self.is_mrtg = False
        self.rent = self.rent_0
        self.game = game

    def __repr__(self) -> str:
        return self.name

    def action(self, player):
        print(f'{player.name} is at {self.name}')
        # checking all non-deed type of properties (i.e. not for sale)
        # is it 'jail'?
        if self.name == 'Go to Jail':
            player.move(10, relative=False, collect_on_go=False)
            player.in_jail = True
            return 'jail'
        # is it a 'free' action?
        elif self.name in ('Free Parking', 'Just Visiting', 'Go'):
            return 'free'
        # is it a 'chance' card?
        elif self.name in ('Chance 1', 'Chance 2', 'Chance 3'):
            player.draw(self.game.ch_cards)
            return 'card'
        # is it a 'community chest' card?
        elif self.name in ('Community Chest 1', 'Community Chest 2', 'Community Chest 3'):
            player.draw(self.game.cc_cards)
            return 'card'
        # is it a luxory tax?
        elif self.name == 'Luxory Tax':
            player.exchange_money(-self.price)
            return 'pay'
        elif self.name == 'Income Tax':
        # is it an icome tax?
            # value is players choice of self.value_1 or 10% of player.assets
            player.exchange_money(-self.price)
            return 'pay'
        # if it is not from above, it is a deed
        # is it purchasable by the player?
        elif (self.owner == None) and (self.price <= player.assets()):
            # does the player want to purchase it?
            if player.will_purchase(self) == 'y':
                # player losses money equal to self.price
                # add self to player.properties
                # change self.owner to player
                player.exchange_money(-self.price)
                player.properties.append(self)
                self.owner = player
                return 'purchase'
            else:
                # player does nothing
                return 'free'
        # does another player own the prooperty?
        elif (self.owner != None) and (self.owner != player):
            # is owner unable to collect?
            if self.owner.in_jail or self.is_mrtg:
                # player does nothing
                return 'free'
            else:
                # player must pay 
                player.exchange_money(self.rent, self.owner)
                return 'pay'
        # if none of the above, the player either owns the plroperty or is unable to purchase it
        else:
            # player does nothing
            return 'free'

class Card():

    id = 0

    def __init__(self, description='this is a card', deck=None, function='money', value_1=0, value_2=0, flag=None) -> None:
        self.id = Card.id
        self.description = description
        self.deck = str(deck)
        self.function = function
        self.value_1 = value_1
        self.value_2 = value_2
        self.flag = flag
        Card.id += 1
    
    def __repr__(self) -> str:
        return f"'id': {self.id}, 'disc': {self.description}, 'deck': {self.deck}, 'func': {self.function}, 'flag': {self.flag}"