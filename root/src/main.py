DAYS_OF_WEEK = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
VALID_RESPONSE = ['Y', 'N']

class Preference:
    def __init__(self):
        self.preferences: dict = {}
        preference_list: list[str] = []

        #Load preferences as attributes.
        with open('../data/config.tsv', 'r') as config:
            header = config.readline().strip('\n').split('\t')
            preference_data = config.readline().strip('\n').split('\t')
            for preference in header:
                self.preferences[preference] = None
                preference_list.append(preference)
            i = 0
            for datapoint in preference_data:
                self.preferences[preference_list[i]] = datapoint
                i += 1
        
        #Parse comma-separated string values
        for value in ['BREAKFAST_ITEMS', 'PASTRY_ITEMS', 'EXCLUDED_ITEMS']:
            if value in self.preferences:
                self.preferences[value] = self.preferences[value].split('|')

    #This method allows the user to change the item order or rebuild item lists.
    def edit_item_list(self, item_list: list[str]):
        print('***EDIT ITEM LISTS***')
        with open('../data/config.tsv', 'r') as config:
            print('***SELECT ITEM LIST:***')
            #Choose the item list
            item_lists = list(config.readline().strip('\n').split('\t'))[3:6]
            current_list = menu_selection(item_lists)
            #Until changes are made, work with a copy of a list of all items.
            list_data = item_list.copy()
            new_list = []
            complete = False
            i = 0
            #Use enumeration to select items from the list of all items.
            while not complete:
                print(f'***SELECT ITEM {i + 1}:***')
                current_item = menu_selection(list_data)
                new_list.append(current_item[1])
                list_data.remove(current_item[1])
                i += 1
                #get_valid_input() always returns False boolean value and user
                #response.
                response = list(get_valid_input('Finished editing? (Y/N)'))
                if response[1] == 'Y':
                    complete = True
        
        #I learned that multiple return values are returned as a tuple :)
        valid_input = list(get_valid_input('Do you want to save to config? (Y/N)'))
        #Save changes to the configuration file
        while not valid_input[0]:
            if valid_input[1] == 'Y':
                #Create a copy of the config file, modify it, then overwrite it.
                with open('../data/test.tsv', 'r') as f:
                    lines = [line.strip('\n').split('\t') for line in f.readlines()]
                    #Rewrite the new configuration as pipe-separated values
                    lines[1][current_list[0] + 3] = ''.join([f'{item}|' for item in new_list])
                with open('../data/test.tsv', 'w') as f:
                    #Using a list comprehension in a list comprehension, write
                    #to the config file in TSV format and line break between
                    #the header and values.
                    text = ''.join([''.join([i + '\t' for i in item]) + '\n' for item in lines])
                    f.write(text)
            #otherse, use the configuration for this file only.
            self.preferences[current_list[1]] = new_list
            valid_input[0] = True

class Par:
    def __init__(self):
        self.item_by_day: dict[str : str, int] = {}
        self.pars: dict[str : str, int] = {}
        self.items = []
        self.period = []

    #Load the initialized arrays with data from a report.
    def load_data(self, filename):
        with open(filename, 'r', encoding='utf-8', errors='replace') as file:
            #Skip header file.
            next(file)

            #Main population algorithm.
            for line in file:
                #Split the line into individual columns.
                column = line.split('\t')

                #Prepare data to be loaded into lists.
                item = column[3]
                current_units = int(column[4])
                date = column[0][-5:]

                #Populate self.item_units with items as keys and the value as
                #date-unit pairs and self.items with a list of items sold that
                #week.
                if item not in self.item_by_day:
                    self.item_by_day[item] = [[date, current_units]]
                    self.items.append(item)
                else:
                    self.item_by_day[item].append([date, current_units])

                #Populate self.period with each day of the reporting period.
                if date not in self.period:
                    self.period.append(date)

            #For days in which there are no item sales, append the missing
            #date and indicate there were 0 Current Units.
            for item in self.items:
                i = 0
                while i < len(self.period):
                    day_units = self.item_by_day[item]
                    if not any(self.period[i] == day[0] for day in day_units):
                        self.item_by_day[item].append([self.period[i], 0])
                    i += 1

            #Sort the values of each key item in ascending order by date
            for item in self.items:
                to_sort = self.item_by_day[item]
                to_sort = sorted(to_sort, key=lambda day_units: day_units[0])
                self.item_by_day[item] = to_sort
            self.period = sorted(self.period)
        
        #Save a copy of self.item_by_day to self.pars for later use in par
        #calculation.
        self.pars = self.item_by_day.copy()

    #Use sales data to calculate par with safety stock.
    def calculate_par(self, minimum_par: int,
                      safety_net: float,
                      breakfast_items: list) -> dict:
        #Iterate through the list of reported items.
        for item in self.items:
            #Create an alias of self.pars[item] for easier understanding
            date_units = self.pars[item]
            for index, column in enumerate(date_units):
                #Hard code check for low volume stores
                if column[1] in [0, 1, 2] and item not in breakfast_items:
                    self.pars[item][index][1] = minimum_par
                elif column[1] in [0, 1] and item in breakfast_items:
                    self.pars[item][index][1] = minimum_par - 1
                else:
                    self.pars[item][index][1] = round_up(column[1] * (1 + safety_net))

class Report:
    def __init__(self, par_data: dict[str : str, int]):
        self.pars = par_data
    #Assuming first day of the reporting period is Sunday
    def print_report(self,
                     days: list[str],
                     period: list[str],
                     items: list[str],
                     breakfast_items: list[str],
                     pastry_items: list[str],
                     excluded_items: list[str]):
        indent = max([len(item) for item in items])
        print(f'''FOR WEEK ENDING {period[-1].strip("'")}:''')
        header = ' ' * indent + '\t'
        i, day_date = 0, []
        while i < len(period):
            day_date.append(f'{days[i]}\t')
            i += 1
        header += ''.join(day_date)
        print(header)
        for item in breakfast_items:
            list_pars = [str(date_par[1]) for date_par in self.pars[item][1:]]
            list_pars.append(str(self.pars[item][0][1]))
            list_pars = '\t'.join(list_pars)
            spaces = ' ' * (indent - len(item))
            print(f'{spaces}{item}\t{list_pars}')
        print()
        for item in pastry_items:
            list_pars = [str(date_par[1]) for date_par in self.pars[item][1:]]
            list_pars.append(str(self.pars[item][0][1]))
            list_pars = '\t'.join(list_pars)
            spaces = ' ' * (indent - len(item))
            print(f'{spaces}{item}\t{list_pars}')

#Helper function which rounds up for any partial value and returns an int.
#Example: 4.12 -> 5
def round_up(value: float) -> int:
    if (value - float(int(value))) > 0.0:
        return int(value) + 1
    else:
        return int(value)
    
def menu_selection(item_list: list[str]) -> list[int, str]:
    for index, item in enumerate(item_list):
        print(f'{index}\t{item}')
    while item_list:
        try:
            selection = int(input('Enter the number of your selection: '))
            if 0 <= selection <= len(item_list) - 1:
                return selection, str(item_list[selection])
            else:
                print("Invalid input. Please try again")
        except ValueError:
            print("Invalid input. Please try again")

def get_valid_input(prompt: str) -> [bool, str]:
    user_input = input(prompt)
    while user_input:
        try:
            if user_input.upper() in VALID_RESPONSE:
                return False, user_input.upper()
            else:
                print("Invalid input. Please try again")
        except ValueError:
            print("Invalid input. Please try again")

ret2 = Preference()
ret2.preferences

ret = Par()
ret.load_data(ret2.preferences['FILENAME'])
ret.period
ret.items
ret.item_by_day
ret.calculate_par(int(ret2.preferences['MINIMUM_PAR']),
                  float(ret2.preferences['SAFETY_NET']),
                  ret2.preferences['BREAKFAST_ITEMS'])
ret.pars

ret3 = Report(ret.pars)

ret3.print_report(DAYS_OF_WEEK,
                  ret.period,
                  ret.items,
                  ret2.preferences['BREAKFAST_ITEMS'],
                  ret2.preferences['PASTRY_ITEMS'],
                  ret2.preferences['EXCLUDED_ITEMS'])

#ret2.edit_item_list(ret.items)
#print(ret2.preferences)