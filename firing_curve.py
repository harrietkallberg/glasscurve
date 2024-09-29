import numpy as np
import json
import matplotlib.pyplot as plt
import os
import matplotlib.colors as mcolors

class _Phase:
    def __init__(self, velocity = 1, endTemp = 0, holdingTime = 0, index = 0, startTemp = None):
        '''Initializing a new Phase in the firing curve'''
        self._velocity = int(velocity)
        self._endTemp = int(endTemp)
        self._holdingTime = int(holdingTime)
        self._index = index
        self._nextPhase = None
        self._prevPhase = None
        self._setStartTemp(startTemp)
        self._color = None  # New attribute to store the color
        
    def _calculateTime(self):
        '''Calculates time based on start and end temperature, speed and holding time'''
        if self._velocity == 0:
            return self._holdingTime
        else:
            calculated_time_minutes = np.ceil(abs((self._endTemp - self._startTemp) / (self._velocity/60)) + self._holdingTime).astype(int)
            
            return calculated_time_minutes

    def _setStartTemp(self, newStarttemp):
        '''Sets the starting temperature and recalculates the time for the current phase.'''
        self._startTemp = newStarttemp
        self._time = self._calculateTime()
    
    def _findNext(self):
        return self._nextPhase
    
    def _findPrev(self):
        return self._prevPhase

    def _changeEndTemp(self, newEndTemp):
        '''Changes the final temperature and recalculates the time for the 
        current phase, sets start temp for next to this end temp'''
        self._endTemp = newEndTemp
        self._time = self._calculateTime()

        if self._nextPhase:
            self._nextPhase._setStartTemp(self._endTemp)

    def _changeVelocity(self, newVelocity):
        '''Changes hastiness and recalculates time for current phase'''
        self._velocity = newVelocity
        self._time = self._calculateTime()
    
    def _changeHoldingTime(self, newHoldingTime):
        '''Changes Hold Time and recalculates time for the current phase'''
        self._holdingTime = newHoldingTime
        self._time = self._calculateTime()
            
    
class firingCurve:
    def __init__(self, roomTemp):
        '''Initializes an empty glass firing curve'''
        self._totalPhases = 0
        self._totalTime = 0
        self._firstPhase = None
        self._lastPhase = None
        self._roomTemp = roomTemp
        self._currentPhase = None  # For iteration
        
    
    def _uppdateIndexAndTime(self, startPhase):
        '''Updates the index and total time of the curve'''
        if startPhase is None:
            return
        current = startPhase
        index = 0
        time = 0
        while current is not None:
            current._index = index
            time += current._time
            if current._nextPhase:
                current._nextPhase._startTemp = current._endTemp
            current = current._nextPhase
            index += 1
        self._totalTime = time
    
    def _clear(self):
        '''Empty the curve'''
        self._totalPhases = 0
        self._totalTime = 0
        self._firstPhase = None
        self._lastPhase = None
            
    def newPhase(self, velocity = 1, endTemp = 0, holdingTime = 0, index = None): # Adds new phase at designated place
        '''Adds new phase at the intended location, 
        if no index is specified it is added last'''
        if index is None:
            index = self._totalPhases
        if index < 0 or index > self._totalPhases:
            raise IndexError("Index outside of interval")
        if index == 0 and self._firstPhase is not None:
            startTemp = self._roomTemp
        elif self._firstPhase and index > 0:
            startTemp = self.findPhase(index-1)._endTemp
        else:
            startTemp = self._roomTemp  # First phase in empty list
      
        newPhase = _Phase(velocity, endTemp, holdingTime, index, startTemp)
        
        if index == 0:
            newPhase._nextPhase = self._firstPhase
            if self._firstPhase:
                self._firstPhase._prevPhase = newPhase
            self._firstPhase = newPhase
            if self._totalPhases == 0:
                self._lastPhase = newPhase     
        elif index == self._totalPhases:  # Insert to end
            if self._lastPhase:
                self._lastPhase._nextPhase = newPhase
                newPhase._prevPhase = self._lastPhase
            else:
                self._firstPhase = newPhase
            self._lastPhase = newPhase 
        else:  # Insert to middle
            prev = self._firstPhase
            for _ in range(index - 1):
                prev = prev._nextPhase  # Move previous to correct position
            newPhase._nextPhase = prev._nextPhase  # The new phase's next phase is the previous's current next phase
            newPhase._prevPhase = prev  # The previous phase of the new phase is the previous one
            prev._nextPhase._prevPhase = newPhase  # The next phase after the previous one must now point back to the new phase
            prev._nextPhase = newPhase  # The previous next phase is now the new phase
        
        self._totalPhases += 1
        self._uppdateIndexAndTime(self._firstPhase)
    
    def removePhase(self, index):
        '''Deletes phase with given index provided it exists'''
        if index < 0 or index >= self._totalPhases:
            raise IndexError("Index outside of interval.")
        elif self._totalPhases == 1:
            self._clear()
        else:
            if index == 0:
                self._firstPhase = self._firstPhase._nextPhase
                self._firstPhase._prevPhase = None
                if self._totalPhases == 2:
                    self._lastPhase = self._firstPhase
            else:
                current = self._firstPhase
                for _ in range(index):   #Found the phase to be removed. index = 3:  # _= 0: index0 -> index1
                    current = current._nextPhase                                 # _= 1: index1 -> index2
                                                                                     # _= 2: intex2 -> index3
                if not current._nextPhase:
                    self._lastPhase = current._prevPhase
                    self._lastPhase._nextPhase = None
                else:
                    current._prevPhase._nextPhase = current._nextPhase
                    current._nextPhase._prevPhase = current._prevPhase
            self._totalPhases -= 1  # Reduce the number of phases in the list
        self._uppdateIndexAndTime(self._firstPhase)
    
    def findPhase(self, index): # O(n) since we need to go through the list
        '''Finds phase with given index'''
        if index < 0 or index >= self._totalPhases:
            return None
        current = self._firstPhase
        for _ in range(index):
            current = current._nextPhase
        return current
    
    def changePhaseEndTemp(self, index, newEndTemp):
        '''Changes the final temperature of a phase and updates the index and time'''
        fas = self.findPhase(index)
        fas._changeEndTemp(newEndTemp)
        self._uppdateIndexAndTime(self._firstPhase)
        
    def changePhaseVelocity(self, index, newVelocity):
        '''Changes the velocity of a phase and updates the index and time'''
        fas = self.findPhase(index)
        fas._changeVelocity(newVelocity)
        self._uppdateIndexAndTime(self._firstPhase)
        
    def changePhaseHoldingTime(self, index, newHoldingTime):
        '''Changes a phase's holding time and updates the index and time'''
        fas = self.findPhase(index)
        fas._changeHoldingTime(newHoldingTime)
        self._uppdateIndexAndTime(self._firstPhase)
    
    def getTotalTime(self):
        hours, minutes = divmod(self._totalTime, 60)
        return f"{hours} timmar och {minutes} minuter"
    
    def _healthy(self): # O(n) since we need to go through the list
        '''Checking the health of the list'''
        if self._totalPhases == 0:
            assert self._firstPhase is None
            assert self._lastPhase is None
            assert self._totalTime == 0
            assert self._totalPhases == 0
        else:
            assert self._lastPhase._findNext() is None
            assert self._firstPhase._findPrev() is None
        forward_count = 0
        current_time = 0
        node = self._firstPhase
        
        while node:
            current_time += node._time
            node = node._findNext()
            forward_count += 1
        
        assert forward_count == self._totalPhases
        assert np.ceil(current_time) == np.ceil(self._totalTime)
        
        backward_count = 0
        current_time = 0
        node = self._lastPhase
        
        while node:
            current_time += node._time
            node = node._findPrev()
            backward_count += 1
        
        assert backward_count == self._totalPhases
        assert np.ceil(current_time) == np.ceil(self._totalTime)
        
    def __iter__(self):
        #Allows iteration over the phases
        self._currentPhase = self._firstPhase
        return self

    def __next__(self):
        if self._currentPhase is None:
            raise StopIteration
        else:
            phase = self._currentPhase
            self._currentPhase = self._currentPhase._nextPhase
            return phase

class GlassTypeHandler:
    def __init__(self, json_filepath):
        self.json_filepath = json_filepath
        self.glass_data = self._load_json_data()

    def _load_json_data(self):
        # Get the absolute path to the directory containing this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Build the full path to the JSON file
        json_file_path = os.path.join(script_dir, self.json_filepath)

        # Try to open and load the JSON file
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Filen '{self.json_filepath}' kunde inte hittas i katalogen '{script_dir}'.")
            exit(1)

    def get_glass_info(self):
        print("Vilken typ av glas ska du bränna?")
        glass_options = {i + 1: glass for i, glass in enumerate(self.glass_data["Glassorter"])}
        for num, glass in glass_options.items():
            print(f"{num}. {glass['namn']}")
        
        choice = int(input("Skriv din valda siffra och klicka enter: "))
        if choice not in glass_options:
            raise ValueError("Invalid choice")
        
        return glass_options[choice]
    
    def get_user_preferences(self, glass_info):
        # Determine allowed oven types based on glass category
        allowed_oven_types = []
        if glass_info['kategori'] == "floatglas":
            allowed_oven_types = ['t']
        elif glass_info['kategori'] == "COE-90/COE-96-glas":
            allowed_oven_types = ['t', 's']
        else:
            # Default to both oven types if other categories are added in the future
            allowed_oven_types = ['t', 's']
        
        # Map for display purposes
        oven_type_display = {'t': 'toppvärmd', 's': 'sidovärmd'}
        
        # Oven Type Selection
        if len(allowed_oven_types) == 1:
            oven_type = allowed_oven_types[0]
            print(f"\nFör glaset '{glass_info['namn']}' (kategori: {glass_info['kategori']}) är endast "
                f"'{oven_type_display[oven_type]}' ugn tillgänglig.")
        else:
            while True:
                print("Vilken typ av ugn har du?")
                for i, ot in enumerate(allowed_oven_types, 1):
                    print(f"{i}. {oven_type_display[ot]}")
                oven_choice = input("Skriv din valda siffra och klicka enter: ").strip()
                try:
                    oven_index = int(oven_choice) - 1
                    if 0 <= oven_index < len(allowed_oven_types):
                        oven_type = allowed_oven_types[oven_index]
                        break
                    else:
                        print("Ogiltigt val. Vänligen ange ett giltigt nummer.")
                except ValueError:
                    print("Ogiltigt val. Vänligen ange ett giltigt nummer.")


        # Radius Selection
        valid_radii = [5, 10, 20, 30, 40, 50, 60]
        while True:
            print("Vilken är din största radie? \nBara 5, 10, 20, 30, 40, 50, 60 är tillåtna")
            radius_input = input("Skriv ett tal och klicka enter: ").strip()
            if radius_input.isdigit() and int(radius_input) in valid_radii:
                radius = int(radius_input)
                break
            else:
                print(f"Ogiltig dimension. Tillåtna värden är: {', '.join(map(str, valid_radii))}")

        # Layers Selection
        valid_layers = [1, 2, 3, 4, 5]
        while True:
            print("Hur många lager har du som mest? \nBara heltal 1 till 5 är tillåtna")
            layers_input = input("Skriv en siffra och klicka enter: ").strip()
            if layers_input.isdigit() and int(layers_input) in valid_layers:
                layers = int(layers_input)
                break
            else:
                print(f"Ogiltigt antal lager. Tillåtna värden är: {', '.join(map(str, valid_layers))}")

        # Minutes Selection
        valid_minutes = list(range(1, 16))
        while True:
            print("Hur många minuter vill du stanna på topptemperatur? \nBara heltal 1 till 15 är tillåtna")
            minutes_input = input("Skriv en siffra och klicka enter: ").strip()
            if minutes_input.isdigit() and int(minutes_input) in valid_minutes:
                minutes = int(minutes_input)
                break
            else:
                print(f"Ogiltigt antal minuter. Tillåtna värden är: {', '.join(map(str, valid_minutes))}")

        # Room Temperature Selection
        valid_temps = list(range(10, 31))
        while True:
            print("Vilken rumstemperatur har du i din verkstad? \nBara heltal 10 till 30 är tillåtna")
            room_temp_input = input("Skriv en siffra och klicka enter: ").strip()
            if room_temp_input.isdigit() and int(room_temp_input) in valid_temps:
                room_temp = int(room_temp_input)
                break
            else:
                print(f"Ogiltig rumstemperatur. Tillåtna värden är: {', '.join(map(str, valid_temps))}")

        # Firing Type Selection
        while True:
            print("Vilken bränning vill du ha?")
            print("1. fullfusing")
            print("2. slumping")
            print("3. tackfusing")
            firing_choice = input("Skriv din valda siffra och klicka enter: ").strip()
            if firing_choice == '1':
                firing_type = "f"
                break
            elif firing_choice == '2':
                firing_type = "s"
                break
            elif firing_choice == '3':
                firing_type = "t"
                break
            else:
                print("Ogiltigt val. Vänligen ange 1, 2 eller 3.")

        return oven_type, radius, layers, minutes, room_temp, firing_type

    def get_time_from_table(self, table, radius, layers):
        for row in table:
            if str(radius) in row:
                return row[str(radius)][str(layers)]
        raise ValueError("Radius or layers not found in the table")
    
    def data_finder(self):
        glass_info = self.get_glass_info()
        oven_type, radius, layers, minutes, room_temp, firing_type = self.get_user_preferences(glass_info)
        print('Du har valt följande glas:')
        for key, value in glass_info.items():
            print(f"{key}: {value}")  # Debug print
        print('ugnstyp = ', oven_type, '\nstörsta radie =', radius,
              '\nantal lager =',layers, 
              '\nantal minuter =',minutes, 
              '\nrumstemperatur =',room_temp, 
              '\nbränningstyp =',firing_type)
        
        if firing_type == "f":
            topptemp = round((glass_info.get("f_topptemp")[0] + glass_info.get("f_topptemp")[1]) / 2)
            print(f"topptemp = {topptemp} grader Celsius\n")
        elif firing_type == "s":
            topptemp = round((glass_info.get("s_topptemp")[0] + glass_info.get("s_topptemp")[1]) / 2)
            print(f"topptemp = {topptemp} grader Celsius\n")
        elif firing_type == "t":
            topptemp = glass_info.get("t_topptemp")
            print(f"topptemp = {topptemp} grader Celsius\n")
        
        # Extracting the uppvarmning_table
        uppvarmning_table = next(
            item["tabell"] for item in self.glass_data["Tider for uppvarmning"]
            if item["kategori"] == glass_info["kategori"] and item["ugn"] == oven_type
        )

        # Extracting the halltider_table
        halltider_table = next(
            item["tabell"] for item in self.glass_data["Halltider"]
            if item["kategori"] == glass_info["kategori"]
        )

        # Extracting the avspanning_table
        avspanning_table = next(
            item["tabell"] for item in self.glass_data["Avspanningstider"]
            if item["kategori"] == glass_info["kategori"]
        )
        
        uppvarmning_time = self.get_time_from_table(uppvarmning_table, radius, layers)
        halltider_time = self.get_time_from_table(halltider_table, radius, layers)
        avspanning_time = self.get_time_from_table(avspanning_table, radius, layers)
        
        return glass_info, uppvarmning_time, halltider_time, avspanning_time, topptemp, minutes, room_temp
        
    def firing_curve_creator(self):
        glass_info, uppvarmning_time, halltider_time, avspanning_time, topptemp, minutes, room_temp = self.data_finder()
        o_astemp = glass_info.get("o_astemp")
        n_astemp = glass_info.get("n_astemp")
        inledande_smaltpunkt = self.glass_data["Inledande_smaltpunkt"]
        
        first_heating_velocity = 999 if np.trunc(60*(inledande_smaltpunkt - room_temp)/uppvarmning_time) >= 999 else np.trunc(60*(inledande_smaltpunkt - room_temp)/uppvarmning_time)
        second_heating_velocity = 999
        first_cooling_velocity = np.trunc(60*(o_astemp - topptemp)/halltider_time)
        second_cooling_velocity = np.trunc(60*(n_astemp - o_astemp)/avspanning_time)
        last_cooling_velocity = -20
        
        curve = firingCurve(room_temp)
        curve.newPhase(first_heating_velocity, inledande_smaltpunkt)
        curve._healthy()
        curve.newPhase(second_heating_velocity, topptemp, minutes)
        curve._healthy()
        curve.newPhase(first_cooling_velocity, o_astemp)
        curve._healthy()
        curve.newPhase(second_cooling_velocity, n_astemp)
        curve._healthy()
        curve.newPhase(last_cooling_velocity, room_temp)
        curve._healthy()
        return curve
    
    def plotting_of_curve(self, curve):
        total_time = 0
        current_temp = curve._roomTemp

        plt.figure(figsize=(10, 6))

        # Create a colormap
        cmap = plt.get_cmap('tab20')  # A colormap with many distinct colors

        times = [0]
        temperatures = [current_temp]

        for idx, phase in enumerate(curve):
            # Assign a color if it's not already set
            if phase._color is None:
                phase._color = cmap(idx % 20)  # Get a color from the colormap

            # Calculate time increment for the phase
            phase_time = phase._time
            middle_time = None
            if phase._holdingTime != 0:
                phase_holdingTime = phase._holdingTime
                middle_time = total_time + phase_time - phase_holdingTime
            start_time = total_time
            end_time = total_time + phase_time
            total_time = end_time

            # Time points for this phase
            if middle_time:
                time_points = [start_time, middle_time, end_time]
            else:
                time_points = [start_time, end_time]

            # Temperature points for this phase
            if phase._velocity == 0:
                # Holding phase
                temp_points = [current_temp, current_temp]
            else:
                if middle_time:
                    temp_points = [current_temp, phase._endTemp, phase._endTemp]
                else:
                    temp_points = [current_temp, phase._endTemp]

            # Plot this phase
            plt.plot(time_points, temp_points, marker='o', color=phase._color, label=f'Fas {idx+1}')

            # Update current temperature
            current_temp = phase._endTemp

            # Append to lists for potential use later
            times.append(end_time)
            temperatures.append(current_temp)

        plt.title('Brännkurva')
        plt.xlabel('Tid (minuter)')
        plt.ylabel('Temperatur (°C)')
        plt.grid(True)
        plt.legend(title='Faser', bbox_to_anchor=(1.05, 1), loc='upper left')  # Place legend outside the plot
        plt.tight_layout()
        plt.show()

def main():
    '''Test code of methods above'''
    json_filepath = 'tables.json'  # Path to your JSON file
    handler = GlassTypeHandler(json_filepath)
    fc = handler.firing_curve_creator()
    
    # Plot the firing curve
    handler.plotting_of_curve(fc)
    
    for i in range(fc._totalPhases):
        phase = fc.findPhase(i)

        # Ensure the phase has a valid color and convert to hex
        if phase._color is not None:
            color_hex = mcolors.to_hex(phase._color)
        else:
            color_hex = 'No color assigned'

        print(f"Fas {i+1}: Start Temp = {phase._startTemp}°C, Slut Temp = {phase._endTemp}°C, "
              f"Hastighet = {phase._velocity} °C/h, Hålltid = {phase._holdingTime} min, "
              f"Fasens tid = {phase._time} min, Färg = {color_hex}")
    
    print(f'\nTotal tid för programmet: {fc.getTotalTime()}')

    
    

if __name__ == "__main__":
    main()
